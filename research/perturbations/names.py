"""name_swap: replace the bio subject's first name(s) with a name of another gender pool.

Name sources (both citable, both public domain / CC0):
  * US: Social Security Administration national baby-name counts (via the HF mirror
    nkrishnaswami/us-ssa-baby-names-national, spot-checked against the official files).
  * India: Wikidata given names of humans with Indian citizenship (P27 = Q668), classed
    as male (Q12308941) or female (Q11879590) given names, counted by number of people
    (query: research/data/wikidata_india_names.rq; snapshot in data/raw/names/).

Which tokens are swapped (BiasBios bios have their first sentence removed, so the full
name is often gone, and many remaining PERSON mentions are surnames):
  * the token must be the first word of a spaCy PERSON entity,
  * it must be in the detection lexicon with a gender share >= ``min_share`` (strongly
    gendered first names only),
  * its gender must equal the bio's gender label (the subject's name, not e.g. a spouse's),
  * it must NOT follow a title (Dr, Mr, Ms, Mrs, Miss, Prof) and must NOT occur in the bio
    as the last word of a multi-word PERSON entity (both mark surnames),
  * with ``subject_only`` (default), the name must look like the bio's SUBJECT: some
    mention of it is a single-word PERSON ("Ben has ...", "Katie's clients") or the head of
    a multi-word PERSON is a clause subject ("Deirdre Marchetti affiliates with ...").
    This skips other people named in the bio ("roasts of Bob Saget", "trained under
    painter Joseph Paquet", "the poetry of Raymond Carver").
Each distinct original name maps to one replacement within a bio (consistent), chosen
deterministically from the target pool by hashing (bio key, name).

``target_gender``: ``opposite`` (gender counterfactual) or ``same`` (e.g. a US -> Indian
name change holding gender fixed).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import pandas as pd

from research.common.config import repo_path

from .base import Replacement, match_case

TITLES = {"dr", "mr", "ms", "mrs", "miss", "prof", "professor", "dr.", "mr.", "ms.", "mrs.", "prof."}


@dataclass
class NameResources:
    lexicon: dict[str, tuple[str, float]]       # lower-cased name -> (gender, share of that gender)
    pools: dict[str, dict[str, list[str]]]      # pool name -> gender -> names


def _ssa_table(path, years) -> pd.DataFrame:
    d = pd.read_parquet(repo_path(path))
    d = d[(d["year"] >= years[0]) & (d["year"] <= years[1])]
    t = d.groupby(["name", "sex"])["count"].sum().unstack(fill_value=0)
    for g in ("F", "M"):
        if g not in t:
            t[g] = 0
    t["total"] = t["F"] + t["M"]
    t["share_F"] = t["F"] / t["total"]
    return t


def build_name_resources(ncfg: dict) -> NameResources:
    s = ncfg["ssa"]
    lex_t = _ssa_table(s["path"], s["lexicon_years"])
    lex_t = lex_t[lex_t["total"] >= s["lexicon_min_births"]]
    lexicon: dict[str, tuple[str, float]] = {}
    for name, row in lex_t.iterrows():
        g = "F" if row["share_F"] >= 0.5 else "M"
        lexicon[name.lower()] = (g, float(max(row["share_F"], 1 - row["share_F"])))

    pool_t = _ssa_table(s["path"], s["pool_years"])
    us = {}
    for g in ("F", "M"):
        share = pool_t["share_F"] if g == "F" else 1 - pool_t["share_F"]
        cand = pool_t[(share >= s["pool_min_share"]) & (pool_t["total"] >= s["lexicon_min_births"])]
        cand = cand.sort_values("total", ascending=False)
        us[g] = sorted(cand.index[: s["pool_size"]].tolist())

    w = ncfg["wikidata_india"]
    wd = pd.read_csv(repo_path(w["path"]))
    wd = wd[~wd["label"].duplicated(keep=False)]           # drop names classed as both genders
    wd = wd[wd["label"].str.fullmatch(r"[A-Z][a-z]+")]     # single plain word
    common_us = set(pool_t.index[pool_t["total"] >= w["exclude_if_ssa_births_over"]])
    wd = wd[~wd["label"].isin(common_us)]
    wd = wd[~wd["label"].isin(set(w.get("exclude_names") or []))]   # human-reviewed label errors
    india = {}
    for g in ("F", "M"):
        cand = wd[wd["gender"] == g].sort_values(["n", "label"], ascending=[False, True])
        india[g] = sorted(cand["label"].head(w["pool_size"]).tolist())
        for name in cand["label"]:
            lexicon.setdefault(name.lower(), (g, 1.0))
    return NameResources(lexicon, {"us": us, "in": india})


def _pick(pool: list[str], key: str, name: str) -> str:
    h = int(hashlib.sha256(f"{key}|{name}".encode("utf-8")).hexdigest()[:12], 16)
    return pool[h % len(pool)]


class NameSwap:
    def __init__(self, resources: NameResources, pool: str = "us", target_gender: str = "opposite",
                 min_share: float = 0.95, name: str | None = None, subject_only: bool = True):
        if target_gender not in ("opposite", "same"):
            raise ValueError("target_gender must be 'opposite' or 'same'")
        self.res, self.pool, self.target_gender, self.min_share = resources, pool, target_gender, min_share
        self.subject_only = subject_only
        self.name = name or f"name_swap_{pool}_{target_gender}"

    def _target(self, gender: str) -> str:
        return gender if self.target_gender == "same" else {"F": "M", "M": "F"}[gender]

    @staticmethod
    def _subject_like(ent) -> bool:
        if len(ent) == 1:
            return True
        return ent.root.dep_ in ("nsubj", "nsubjpass") or (ent.root.dep_ == "poss" and ent.root.head.dep_ in ("nsubj", "nsubjpass"))

    def candidate_tokens(self, doc, gender: str) -> list:
        surnames = {e[-1].text.lower() for e in doc.ents if e.label_ == "PERSON" and len(e) > 1}
        subjectish = {e[0].text.lower() for e in doc.ents if e.label_ == "PERSON" and self._subject_like(e)}
        out = []
        for e in doc.ents:
            if e.label_ != "PERSON":
                continue
            tok = e[0]
            low = tok.text.lower()
            if not tok.is_alpha or not tok.is_title:
                continue
            prev = doc[tok.i - 1].text.lower() if tok.i > 0 else ""
            if prev in TITLES or prev.rstrip(".") in TITLES:
                continue
            if len(e) == 1 and low in surnames:
                continue
            if self.subject_only and low not in subjectish:
                continue
            g_share = self.res.lexicon.get(low)
            if g_share is None or g_share[1] < self.min_share or g_share[0] != gender:
                continue
            out.append(tok)
        return out

    def replacements(self, doc, gender: str, key: str) -> list[Replacement]:
        pool = self.res.pools[self.pool][self._target(gender)]
        firsts = self.candidate_tokens(doc, gender)
        names = {t.text.lower() for t in firsts}
        mapping = {n: _pick(pool, key, n) for n in sorted(names)}
        # also replace later bare mentions of the same first name (e.g. possessives "Monica's")
        out = []
        for tok in doc:
            low = tok.text.lower()
            if low in mapping and tok.is_alpha and tok.is_title:
                prev = doc[tok.i - 1].text.lower() if tok.i > 0 else ""
                if prev in TITLES or prev.rstrip(".") in TITLES:
                    continue
                out.append(Replacement(tok.i, tok.i + 1, match_case(tok.text, mapping[low]), "name",
                                       f"{self.pool}:{gender}->{self._target(gender)}"))
        return out
