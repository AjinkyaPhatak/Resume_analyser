"""Phase 2 data components on tiny hand-made frames (test-only values)."""

import numpy as np
import pandas as pd
import pytest
import yaml

from research.common.config import RESEARCH_ROOT
from research.data.biasbios import PROFESSIONS, clean, stratified_resplit, to_frame
from research.data.jobs import load_postings, normalize_title
from research.data.occupation_map import (
    add_review_priority, apply_description_requirements, build_map, compile_patterns, final_mapping,
    match_title, merge_reviews, validate_reviews,
)
from research.data.pools import PoolError, build_pools, select_jds
from research.data.relevance import Relevance


@pytest.fixture(scope="module")
def occ_yaml():
    with open(RESEARCH_ROOT / "configs" / "occupations.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def occ_cfg(occ_yaml):
    return occ_yaml["occupations"]


@pytest.fixture(scope="module")
def patterns(occ_yaml):
    return compile_patterns(occ_yaml["occupations"], occ_yaml["title_exclude_all"])


# --- BiasBios ---------------------------------------------------------------------

def _raw(texts, profs, genders):
    return pd.DataFrame({"hard_text": texts, "profession": profs, "gender": genders})


def test_to_frame_maps_labels():
    df = to_frame(_raw(["He is a nurse here ok"], [13], [0]), "test")
    assert df.loc[0, "occupation"] == "nurse" and df.loc[0, "gender"] == "M"
    assert df.loc[0, "bio_id"] == "test-0" and df.loc[0, "n_words"] == 6


def test_to_frame_rejects_bad_labels():
    with pytest.raises(ValueError):
        to_frame(_raw(["x y z w v"], [28], [0]), "dev")
    with pytest.raises(ValueError):
        to_frame(_raw(["x y z w v"], [1], [2]), "dev")


def test_clean_dedup_and_leakage():
    long = "she works as a nurse in a large hospital"
    frames = {
        "train": to_frame(_raw([long, long, "too short"], [13, 13, 13], [1, 1, 1]), "train"),
        "dev": to_frame(_raw([long, "he teaches maths at a school"], [13, 26], [1, 0]), "dev"),
        "test": to_frame(_raw(["he teaches maths at a school", "she paints large murals for cities"], [26, 14], [0, 1]), "test"),
    }
    out, stats = clean(frames, min_words=5)
    assert stats["train"] == {"raw": 3, "too_short": 1, "duplicate_in_split": 1, "overlaps_earlier_split": 0, "kept": 1}
    assert stats["dev"]["overlaps_earlier_split"] == 1 and len(out["dev"]) == 1
    assert stats["test"]["overlaps_earlier_split"] == 1 and len(out["test"]) == 1


def test_stratified_resplit_deterministic_and_stratified():
    rng = np.random.default_rng(0)
    n = 2000
    raw = _raw([f"bio number {i} with words" for i in range(n)], rng.integers(0, 4, n), rng.integers(0, 2, n))
    frames = {"train": to_frame(raw.iloc[:1200], "train"), "dev": to_frame(raw.iloc[1200:1500], "dev"),
              "test": to_frame(raw.iloc[1500:], "test")}
    a = stratified_resplit(frames, seed=1)
    b = stratified_resplit(frames, seed=1)
    assert all(a[s]["bio_id"].tolist() == b[s]["bio_id"].tolist() for s in a)
    assert sum(len(v) for v in a.values()) == n
    for s in a:
        share = (a[s]["gender"] == "F").mean()
        assert abs(share - (raw["gender"] == 1).mean()) < 0.03


# --- jobs --------------------------------------------------------------------------

def test_normalize_title():
    assert normalize_title("  Sr. Software Engineer / Backend (Remote) ") == "sr. software engineer backend remote"
    assert normalize_title("Nurse – ICU") == "nurse - icu"


def test_load_postings(tmp_path):
    p = tmp_path / "postings.csv"
    words = " ".join(["word"] * 60)
    pd.DataFrame({
        "job_id": ["1", "2", "3", "4"],
        "title": ["Registered Nurse", "Paralegal", None, "Teacher"],
        "description": [words, words, words, "too short"],
        "views": [1, 2, 3, 4],
    }).to_csv(p, index=False)
    df, stats = load_postings(p, min_words=50)
    assert list(df["jd_id"]) == ["li-1"]          # 2 duplicates 1's text, 3 no title, 4 short
    assert stats == {"raw": 4, "missing_title_or_description": 1, "too_short": 1,
                     "duplicate_description": 1, "kept": 1}


def test_load_postings_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="arshkon"):
        load_postings(tmp_path / "nope.csv")


# --- occupation mapping ------------------------------------------------------------

@pytest.mark.parametrize("title, strong, weak", [
    ("registered nurse - icu", ["nurse"], []),
    ("physician assistant", [], []),
    ("software architect", [], []),
    ("project architect", ["architect"], []),
    ("senior software engineer", ["software_engineer"], []),
    ("nurse practitioner", ["nurse"], ["nurse"]),        # own weak pattern -> ambiguous
    ("dds residential counselor", [], ["dentist"]),       # DDS != dentist here
    ("general dentist", ["dentist"], []),
    ("oral surgeon", ["surgeon"], ["surgeon"]),
    ("volunteer virtual classroom speaker career path to becoming a surgeon", [], []),
    ("genesys routing composer developer", [], []),
    ("data model engineer", [], []),
    ("painter", [], ["painter"]),
    ("auto body painter", [], []),
    ("yoga instructor", ["yoga_teacher"], []),
    ("yoga teacher", ["yoga_teacher"], []),
    ("high school math teacher", ["teacher"], []),
    ("legal assistant", ["paralegal"], []),
    ("associate attorney", ["attorney"], []),
    ("dental assistant", [], []),
    ("hospitalist physician", ["physician"], []),
    ("orthopedic surgeon", ["surgeon"], []),
    ("athletic trainer", [], []),
    ("adjunct faculty - psychology", ["professor"], []),
])
def test_match_title(patterns, title, strong, weak):
    assert match_title(title, patterns) == (strong, weak)


def test_build_map_status(patterns):
    jds = pd.DataFrame({"title": ["Registered Nurse", "Registered Nurse", "Painter", "Cashier"],
                        "title_norm": ["registered nurse", "registered nurse", "painter", "cashier"]})
    m = build_map(jds, patterns).set_index("title_norm")
    assert m.loc["registered nurse", "status"] == "auto" and m.loc["registered nurse", "n_postings"] == 2
    assert build_map(pd.DataFrame({"title": ["NP"], "title_norm": ["nurse practitioner"]}), patterns
                     ).loc[0, "status"] == "ambiguous"
    assert m.loc["painter", "status"] == "ambiguous"
    assert "cashier" not in m.index


def test_reviews_merge_and_apply(tmp_path, patterns):
    jds = pd.DataFrame({"title": ["Painter", "Registered Nurse", "Nurse Educator"],
                        "title_norm": ["painter", "registered nurse", "nurse educator"]})
    m = build_map(jds, patterns)
    m.loc[m["title_norm"] == "painter", "reviewed_occupation"] = "none"
    m.loc[m["title_norm"] == "nurse educator", "reviewed_occupation"] = "nurse"
    path = tmp_path / "map.csv"
    m.to_csv(path, index=False)
    regenerated = merge_reviews(build_map(jds, patterns), path)
    mapping = final_mapping(regenerated)
    assert mapping == {"registered nurse": "nurse", "nurse educator": "nurse"}


def test_validate_reviews_rejects_typos():
    df = pd.DataFrame({"reviewed_occupation": ["nurse", "nurze"]})
    with pytest.raises(ValueError, match="nurze"):
        validate_reviews(df)


def test_all_occupations_have_soc(occ_cfg):
    assert set(occ_cfg) == set(PROFESSIONS)
    assert all(len(spec["soc"]) == 7 for spec in occ_cfg.values())


# --- relevance ---------------------------------------------------------------------

def test_relevance(occ_cfg):
    rel = Relevance(occ_cfg)
    assert rel.graded("nurse", "nurse") == 2
    assert rel.graded("paralegal", "attorney") == 1
    assert rel.graded("nurse", "physician") == 1
    assert rel.graded("yoga_teacher", "personal_trainer") == 1
    assert rel.graded("accountant", "nurse") == 0
    assert rel.binary("paralegal", "attorney") == 0
    assert "paralegal" in rel.related("attorney")
    minor = Relevance(occ_cfg, level="minor")
    assert minor.graded("teacher", "professor") == 0 and rel.graded("teacher", "professor") == 1


# --- pools -------------------------------------------------------------------------

def _toy_bios(n_per=12):
    rows = []
    for occ in ["nurse", "attorney", "teacher", "paralegal"]:
        for g in ["F", "M"]:
            for i in range(n_per):
                rows.append({"bio_id": f"{occ}-{g}-{i}", "occupation": occ, "gender": g})
    return pd.DataFrame(rows)


def test_build_pools_balanced_and_deterministic(occ_cfg):
    bios = _toy_bios()
    jds = pd.DataFrame({"jd_id": ["j1", "j2"], "occupation": ["nurse", "attorney"]})
    rel = Relevance(occ_cfg)
    a = build_pools(bios, jds, rel, n_candidates=20, n_relevant=4, rng=np.random.default_rng(3))
    b = build_pools(bios, jds, rel, n_candidates=20, n_relevant=4, rng=np.random.default_rng(3))
    pd.testing.assert_frame_equal(a, b)
    for jd, g in a.groupby("jd_id"):
        assert len(g) == 20 and g["bio_id"].is_unique
        assert g["rel_binary"].sum() == 4
        assert (g["bio_gender"] == "F").sum() == 10
        assert (g[g["rel_binary"] == 1]["bio_gender"] == "F").sum() == 2
    att = a[a["jd_id"] == "j2"]
    assert set(att.loc[att["bio_occupation"] == "paralegal", "rel_graded"]) <= {1}


def test_build_pools_proportional(occ_cfg):
    p = build_pools(_toy_bios(), pd.DataFrame({"jd_id": ["j"], "occupation": ["teacher"]}), Relevance(occ_cfg),
                    20, 4, np.random.default_rng(0), irrelevant_sampling="proportional")
    assert len(p) == 20 and p["bio_id"].is_unique


def test_build_pools_insufficient(occ_cfg):
    with pytest.raises(PoolError):
        build_pools(_toy_bios(n_per=1), pd.DataFrame({"jd_id": ["j"], "occupation": ["nurse"]}),
                    Relevance(occ_cfg), 20, 4, np.random.default_rng(0))


def test_build_pools_rejects_odd(occ_cfg):
    with pytest.raises(ValueError):
        build_pools(_toy_bios(), pd.DataFrame({"jd_id": ["j"], "occupation": ["nurse"]}),
                    Relevance(occ_cfg), 21, 4, np.random.default_rng(0))


def test_select_jds_coverage():
    jds = pd.DataFrame({"jd_id": [f"n{i}" for i in range(10)] + ["a1", "a2"],
                        "occupation": ["nurse"] * 10 + ["attorney"] * 2})
    dev, test, cov = select_jds(jds, per_occupation=6, min_per_occupation=3, dev_fraction=0.5,
                                rng=np.random.default_rng(0))
    assert cov["nurse"] == {"available": 10, "used": 6, "dev": 3, "test": 3}
    assert cov["attorney"]["used"] == 0
    assert set(dev["jd_id"]).isdisjoint(test["jd_id"])


def test_description_requirement(patterns):
    jds = pd.DataFrame({"occupation": ["architect", "architect", "nurse"],
                        "text": ["Produce construction documents in Revit.", "Design Kafka streaming platforms.",
                                 "Care for patients."]})
    out, dropped = apply_description_requirements(jds, patterns)
    assert out["occupation"].iloc[0] == "architect" and pd.isna(out["occupation"].iloc[1])
    assert out["occupation"].iloc[2] == "nurse"
    assert dropped == {"architect": 1}


def test_review_priority(patterns):
    jds = pd.DataFrame({"title": ["x"] * 4, "title_norm": ["registered nurse"] * 3 + ["hospice chaplain"]})
    jds = pd.concat([jds, pd.DataFrame({"title": ["Painter"], "title_norm": ["painter"]})], ignore_index=True)
    m = add_review_priority(build_map(jds, patterns), needed_per_occupation=2).set_index("title_norm")
    assert m.loc["hospice chaplain", "review_priority"] == "high"   # pastor has no auto postings
    assert m.loc["registered nurse", "review_priority"] == ""       # auto rows need no review
    jds2 = pd.DataFrame({"title": ["x"] * 4, "title_norm": ["registered nurse"] * 3 + ["nurse practitioner"]})
    m2 = add_review_priority(build_map(jds2, patterns), needed_per_occupation=2).set_index("title_norm")
    assert m2.loc["nurse practitioner", "review_priority"] == "low"  # nurse already has enough
