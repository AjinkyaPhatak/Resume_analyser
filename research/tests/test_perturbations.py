"""Counterfactual generators on hand-written fixture sentences (test-only)."""

import pandas as pd
import pytest
import spacy
import yaml

from research.common.config import RESEARCH_ROOT
from research.perturbations.base import Replacement, apply_replacements, match_case, merge
from research.perturbations.lexical_swaps import AffiliationSwap, AgenticCommunalRewrite
from research.perturbations.names import NameResources, NameSwap, build_name_resources
from research.perturbations.pronouns import PronounSwap
from research.perturbations.registry import Condition, build_conditions


@pytest.fixture(scope="module")
def nlp():
    return spacy.load("en_core_web_sm")


def run(nlp, perturber, text, gender="F", key="k"):
    doc = nlp(text)
    return apply_replacements(doc, perturber.replacements(doc, gender, key))


# --- base -----------------------------------------------------------------------------

def test_match_case():
    assert match_case("He", "she") == "She"
    assert match_case("HIS", "her") == "HER"
    assert match_case("his", "Her") == "her"


def test_apply_replacements_keeps_whitespace_and_logs(nlp):
    doc = nlp("He  led\nthe lab.")
    res = apply_replacements(doc, [Replacement(0, 1, "She", "pronoun")])
    assert res.text == "She  led\nthe lab."
    c = res.changes[0]
    assert (c.original, c.replacement, c.start_char, c.end_char, c.orig_start, c.orig_end) == ("He", "She", 0, 3, 0, 2)


def test_merge_drops_overlaps():
    a = [Replacement(0, 2, "x", "a")]
    b = [Replacement(1, 3, "y", "b"), Replacement(4, 5, "z", "b")]
    assert [r.kind for r in merge([a, b])] == ["a", "b"]


# --- pronouns -------------------------------------------------------------------------

@pytest.mark.parametrize("src, expected", [
    ("He led the lab. His team praised him.", "She led the lab. Her team praised her."),
    ("She thanked her mentor and taught her students.", "He thanked his mentor and taught his students."),
    ("The board hired her in 2010.", "The board hired him in 2010."),
    ("She describes herself as curious.", "He describes himself as curious."),
    ("The final decision was his.", "The final decision was hers."),
    ("Ms. Reagan practices medicine.", "Mr. Reagan practices medicine."),
    ("Mr Smith teaches.", "Ms Smith teaches."),
    ("HE IS A NURSE.", "SHE IS A NURSE."),
])
def test_pronoun_swap(nlp, src, expected):
    assert run(nlp, PronounSwap(), src).text == expected


def test_pronoun_no_pronouns_unchanged(nlp):
    res = run(nlp, PronounSwap(), "The clinic serves rural patients and they miss few appointments.")
    assert not res.changed
    assert res.text == "The clinic serves rural patients and they miss few appointments."


def test_pronoun_swap_round_trip(nlp):
    src = "He and his team thanked him for the grant."
    once = run(nlp, PronounSwap(), src).text
    assert once == "She and her team thanked her for the grant."
    assert run(nlp, PronounSwap(), once).text == src   # "already swapped" text swaps back


def test_pronoun_bidirectional(nlp):
    assert run(nlp, PronounSwap(), "She met her husband when he was a student.").text == \
        "He met his husband when she was a student."


def test_pronoun_titles_optional(nlp):
    assert run(nlp, PronounSwap(swap_titles=False), "Ms. Reagan said she would.").text == "Ms. Reagan said he would."


# --- names ----------------------------------------------------------------------------

@pytest.fixture()
def names():
    lex = {"monica": ("F", 1.0), "james": ("M", 1.0), "harrison": ("M", 0.99), "leah": ("F", 1.0),
           "jordan": ("M", 0.7)}
    pools = {"us": {"F": ["Mary"], "M": ["John"]}, "in": {"F": ["Priya"], "M": ["Arjun"]}}
    return NameResources(lex, pools)


def test_name_swap_consistent_and_possessive(nlp, names):
    res = run(nlp, NameSwap(names, "us", "opposite"),
              "Monica is certified in nutrition. Monica's clients trust her.", gender="F")
    assert res.text == "John is certified in nutrition. John's clients trust her."
    assert {c.original for c in res.changes} == {"Monica"}


def test_name_swap_skips_titles_surnames_and_other_people(nlp, names):
    assert not run(nlp, NameSwap(names), "Dr. Harrison treats patients in Ohio.", gender="M").changed
    res = run(nlp, NameSwap(names), "Monica Lee is married to James Lee.", gender="F")
    assert "James" in res.text and "Monica" not in res.text   # spouse's (male) name kept


def test_name_swap_skips_non_subject_people(nlp, names):
    # other people with the subject's gender, inside "of X" / "under X" phrases, are left alone
    res = run(nlp, NameSwap(names), "As a writer he contributed to roasts of James Franco.", gender="M")
    assert not res.changed
    assert run(nlp, NameSwap(names), "James has a background in soccer.", gender="M").text.startswith("Mary")
    assert run(nlp, NameSwap(names, subject_only=False), "As a writer he contributed to roasts of James Franco.",
               gender="M").changed


def test_name_swap_ambiguous_names_skipped(nlp, names):
    assert not run(nlp, NameSwap(names, min_share=0.95), "Jordan Smith builds bridges.", gender="M").changed


def test_name_swap_same_gender_indian_pool(nlp, names):
    assert run(nlp, NameSwap(names, "in", "same"), "Monica Ray teaches yoga.", gender="F").text.startswith("Priya")


def test_name_swap_no_names(nlp, names):
    assert not run(nlp, NameSwap(names), "She teaches chemistry at a large school.", gender="F").changed


def test_name_swap_bad_target(names):
    with pytest.raises(ValueError):
        NameSwap(names, target_gender="other")


def test_build_name_resources(tmp_path):
    rows = []
    for year in (1960, 1980):
        rows += [("Mary", "F", year, 1, 9000), ("John", "M", year, 1, 9000), ("Jordan", "M", year, 2, 600),
                 ("Jordan", "F", year, 2, 500), ("Tara", "F", year, 3, 4000), ("Zed", "M", year, 4, 10)]
    ssa = tmp_path / "ssa.parquet"
    pd.DataFrame(rows, columns=["name", "sex", "year", "rank", "count"]).to_parquet(ssa)
    wd = tmp_path / "wd.csv"
    pd.DataFrame({"name": ["q1", "q2", "q3", "q4", "q5"], "label": ["Priya", "Arjun", "Tara", "Kiran", "Kiran"],
                  "gender": ["F", "M", "F", "M", "F"], "n": [10, 9, 8, 7, 6]}).to_csv(wd, index=False)
    cfg = {"ssa": {"path": str(ssa), "lexicon_years": [1950, 2000], "lexicon_min_births": 100,
                   "pool_years": [1950, 2000], "pool_min_share": 0.98, "pool_size": 5},
           "wikidata_india": {"path": str(wd), "pool_size": 5, "exclude_if_ssa_births_over": 5000}}
    res = build_name_resources(cfg)
    assert res.pools["us"] == {"F": ["Mary", "Tara"], "M": ["John"]}   # Jordan not >= 98% one gender
    assert res.pools["in"] == {"F": ["Priya"], "M": ["Arjun"]}         # Tara common in US; Kiran both genders
    assert res.lexicon["jordan"][0] == "M" and res.lexicon["jordan"][1] < 0.6
    assert "zed" not in res.lexicon                                      # below min births
    assert res.lexicon["priya"] == ("F", 1.0)


# --- affiliations ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def aff(nlp):
    with open(RESEARCH_ROOT / "configs" / "affiliations.yaml", encoding="utf-8") as f:
        return AffiliationSwap(yaml.safe_load(f)["pairs"], nlp.tokenizer)


@pytest.mark.parametrize("src, expected", [
    ("She was president of her sorority.", "She was president of her fraternity."),
    ("Fraternity events kept him busy.", "Sorority events kept him busy."),
    ("A member of the Society of Women Engineers.", "A member of the National Society of Professional Engineers."),
    ("She chairs Women in Film Atlanta.", "She chairs Professionals in Film Atlanta."),
    ("She led Girl Scouts troop 12.", "She led Boy Scouts troop 12."),
])
def test_affiliation_swap(nlp, aff, src, expected):
    assert run(nlp, aff, src).text == expected


@pytest.mark.parametrize("src", [
    "Her research on women in leadership is widely cited.",   # lower-case: not an org name
    "She specialises in women's health.",                     # specialty, not affiliation
])
def test_affiliation_leaves_non_affiliations(nlp, aff, src):
    assert not run(nlp, aff, src).changed


# --- agentic / communal -------------------------------------------------------------

@pytest.fixture(scope="module")
def ac():
    with open(RESEARCH_ROOT / "configs" / "agentic_communal.yaml", encoding="utf-8") as f:
        return AgenticCommunalRewrite(yaml.safe_load(f)["entries"])


@pytest.mark.parametrize("src, expected", [
    ("She led the team and supports junior staff.", "She supported the team and leads junior staff."),
    ("He is a driven engineer.", "He is a committed engineer."),
    ("He drove growth in Asia.", "He helped growth in Asia."),
])
def test_agentic_communal_swaps(nlp, ac, src, expected):
    res = run(nlp, ac, src)
    assert res.text == expected
    assert all(c.kind in ("agentic->communal", "communal->agentic") for c in res.changes)


@pytest.mark.parametrize("src", [
    "She is a leading expert on malaria.",          # adjectival 'leading'
    "He was lead author on the paper.",             # nominal 'lead'
    "The project is supported by the NIH.",         # passive
    "She helped patients recover.",                 # no communal->agentic rule for 'helped'
    "Her documentary series led to her interest in parrots.",   # 'led to' = caused
    "Development is driving out the poor.",                     # phrasal verb
    "She dreams of leading the way in fashion law.",            # idiom
    "Her passion for travel led her to take a sabbatical.",     # object + complement
    "In addition to English, Dr. Morris's practice supports this language: Spanish.",   # template
    "She helps clients lead a life full of happiness.",          # idiom
    "He is one of the world's leading researchers on sleep.",    # attributive participle
    "She worked at a tech-driven healthcare company.",           # hyphenated compound
    "She published booklets to support local charities.",        # support->lead rule removed
])
def test_agentic_communal_leaves_alone(nlp, ac, src):
    assert not run(nlp, ac, src).changed


def test_agentic_communal_rejects_duplicates():
    with pytest.raises(ValueError):
        AgenticCommunalRewrite([{"from": "led", "to": "a", "direction": "x"}, {"from": "Led", "to": "b", "direction": "x"}])


# --- conditions ---------------------------------------------------------------------

def test_composite_condition(nlp, names):
    cond = Condition("gender_full", [PronounSwap(), NameSwap(names)])
    doc = nlp("Monica Lee leads her lab. She mentors students.")
    res = cond.apply(doc, "F", "bio-1")
    assert res.text == "John Lee leads his lab. He mentors students."
    assert {c.kind for c in res.changes} == {"pronoun", "name"}


def test_build_conditions_unknown_part():
    with pytest.raises(ValueError):
        build_conditions({"conditions": [{"name": "x", "parts": ["nope"]}]}, {"pronoun": PronounSwap()})
