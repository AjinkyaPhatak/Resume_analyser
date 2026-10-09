"""Map job-posting titles to BiasBios occupations, with a human-review CSV.

Mapping happens per unique normalised title (not per posting), so the review file is
short. Patterns live in configs/occupations.yaml.

Review CSV (research/data/occupation_map.csv), one row per title that matched anything:
    title_norm, n_postings, example_title, auto_occupation, candidates, status,
    reviewed_occupation, note
``status`` is ``auto`` (exactly one occupation matched an include pattern, nothing else
matched) or ``ambiguous`` (several occupations matched; or only a ``weak`` pattern
matched; or the include match also hit one of that occupation's ``flag`` patterns, e.g.
"nurse practitioner" for nurse).
``review_priority`` is ``high`` when a candidate occupation has fewer auto-mapped
postings than the pools need, i.e. reviewing that row can add JDs where they're scarce.
``reviewed_occupation`` is for the human reviewer: put an occupation name to accept or
override, or ``none`` to reject. A filled ``reviewed_occupation`` always wins. Unreviewed
ambiguous titles are excluded from the experiments. Regenerating the CSV keeps
existing reviews.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .biasbios import PROFESSIONS

COLUMNS = ["review_priority", "title_norm", "n_postings", "example_title", "auto_occupation", "candidates",
           "status", "reviewed_occupation", "note"]


@dataclass
class OccupationPatterns:
    name: str
    include: list[re.Pattern]
    weak: list[re.Pattern]
    exclude: list[re.Pattern]
    require_description: re.Pattern | None = None
    flag: list[re.Pattern] = None


def compile_patterns(occ_cfg: dict, exclude_all: list[str] | None = None) -> list[OccupationPatterns]:
    """``exclude_all`` patterns veto every occupation (e.g. 'volunteer ... speaker' titles)."""
    unknown = set(occ_cfg) - set(PROFESSIONS)
    if unknown:
        raise ValueError(f"occupations.yaml has unknown occupations: {sorted(unknown)}")
    out = []
    for name in PROFESSIONS:
        spec = occ_cfg.get(name, {})
        comp = lambda pats: [re.compile(p, re.IGNORECASE) for p in (pats or [])]  # noqa: E731
        req = spec.get("require_description")
        out.append(OccupationPatterns(name, comp(spec.get("include")), comp(spec.get("weak")),
                                      comp(list(spec.get("exclude") or []) + list(exclude_all or [])),
                                      re.compile(req, re.IGNORECASE) if req else None,
                                      comp(spec.get("flag"))))
    return out


def match_title(title_norm: str, patterns: list[OccupationPatterns]) -> tuple[list[str], list[str]]:
    """Return (occupations with an include match, occupations needing review), after excludes.

    An occupation lands in the second list if only its ``weak`` patterns matched, or if an
    include match also hit one of its ``flag`` patterns (then it's in both lists).
    """
    strong, weak = [], []
    for occ in patterns:
        if any(p.search(title_norm) for p in occ.exclude):
            continue
        if any(p.search(title_norm) for p in occ.include):
            strong.append(occ.name)
            if any(p.search(title_norm) for p in occ.flag or []):
                weak.append(occ.name)
        elif any(p.search(title_norm) for p in occ.weak):
            weak.append(occ.name)
    return strong, weak


def build_map(jds: pd.DataFrame, patterns: list[OccupationPatterns]) -> pd.DataFrame:
    counts = Counter(jds["title_norm"])
    examples = jds.drop_duplicates("title_norm").set_index("title_norm")["title"]
    rows = []
    for title, n in counts.items():
        strong, weak = match_title(title, patterns)
        if not strong and not weak:
            continue
        if len(strong) == 1 and not weak:
            status, auto, note = "auto", strong[0], ""
        elif len(strong) == 1:
            status, auto, note = "ambiguous", strong[0], "flagged / weak match: " + "|".join(weak)
        elif len(strong) > 1:
            status, auto, note = "ambiguous", "", "matches several occupations"
        else:
            status, auto, note = "ambiguous", "", "weak pattern only"
        rows.append({"review_priority": "", "title_norm": title, "n_postings": n, "example_title": examples[title],
                     "auto_occupation": auto, "candidates": "|".join(dict.fromkeys(strong + weak)),
                     "status": status, "reviewed_occupation": "", "note": note})
    return pd.DataFrame(rows, columns=COLUMNS)


def add_review_priority(df: pd.DataFrame, needed_per_occupation: int) -> pd.DataFrame:
    """Mark ambiguous rows whose candidates include an occupation short of auto-mapped
    postings; sort so those come first, then by posting count."""
    auto_counts = df[df["status"] == "auto"].groupby("auto_occupation")["n_postings"].sum().to_dict()
    scarce = {o for o in PROFESSIONS if auto_counts.get(o, 0) < needed_per_occupation}
    df = df.copy()
    is_amb = df["status"] == "ambiguous"
    hit = df["candidates"].str.split("|").map(lambda cs: any(c in scarce for c in cs))
    df["review_priority"] = ""
    df.loc[is_amb & hit, "review_priority"] = "high"
    df.loc[is_amb & ~hit, "review_priority"] = "low"
    order = df["review_priority"].map({"high": 0, "low": 1, "": 2})
    return (df.assign(_o=order).sort_values(["_o", "candidates", "n_postings", "title_norm"],
                                            ascending=[True, True, False, True])
              .drop(columns="_o").reset_index(drop=True))


def apply_description_requirements(jds: pd.DataFrame, patterns: list[OccupationPatterns]) -> tuple[pd.DataFrame, dict]:
    """Unmap postings of occupations with ``require_description`` whose text lacks a match.

    Used where titles are polysemous (e.g. 'architect' is mostly IT in LinkedIn data).
    Returns (frame with occupation set to NA for dropped rows, {occupation: n_dropped}).
    """
    jds = jds.copy()
    dropped = {}
    for occ in patterns:
        if occ.require_description is None:
            continue
        sel = jds["occupation"] == occ.name
        bad = sel & ~jds["text"].str.contains(occ.require_description)
        dropped[occ.name] = int(bad.sum())
        jds.loc[bad, "occupation"] = None
    return jds, dropped


def merge_reviews(new: pd.DataFrame, old_path: Path) -> pd.DataFrame:
    """Carry ``reviewed_occupation`` over from an existing CSV, keyed by title_norm."""
    if not old_path.is_file():
        return new
    old = pd.read_csv(old_path, dtype=str, keep_default_na=False)
    reviews = {t: r for t, r in zip(old["title_norm"], old["reviewed_occupation"]) if r.strip()}
    new = new.copy()
    new["reviewed_occupation"] = new["title_norm"].map(reviews).fillna(new["reviewed_occupation"])
    return new


def validate_reviews(df: pd.DataFrame) -> None:
    allowed = set(PROFESSIONS) | {"none", ""}
    bad = sorted(set(df["reviewed_occupation"].str.strip()) - allowed)
    if bad:
        raise ValueError(f"occupation_map.csv: invalid reviewed_occupation values {bad}; "
                         f"use one of the 28 BiasBios occupations or 'none'")


def final_mapping(df: pd.DataFrame) -> dict[str, str]:
    """title_norm -> occupation, applying reviews; ambiguous+unreviewed are dropped."""
    validate_reviews(df)
    out = {}
    for row in df.itertuples(index=False):
        rev = str(row.reviewed_occupation).strip()
        if rev:
            if rev != "none":
                out[row.title_norm] = rev
        elif row.status == "auto":
            out[row.title_norm] = row.auto_occupation
    return out
