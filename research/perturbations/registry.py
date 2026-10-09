"""Build perturbation conditions from configs/perturbations.yaml.

A *part* is one perturber (pronoun, name_us_opposite, affiliation, ...); a *condition*
is a named list of parts applied together to the same parsed bio (e.g. gender_full =
pronoun + name_us_opposite). Overlapping replacements: the earlier part wins.
"""

from __future__ import annotations

from dataclasses import dataclass

import yaml

from research.common.config import RESEARCH_ROOT

from .base import PerturbResult, apply_replacements, merge
from .lexical_swaps import AffiliationSwap, AgenticCommunalRewrite
from .names import NameSwap, build_name_resources
from .pronouns import PronounSwap


def _yaml(rel: str) -> dict:
    with open(RESEARCH_ROOT / rel, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_parts(cfg: dict, nlp, name_resources=None) -> dict:
    parts: dict = {"pronoun": PronounSwap(swap_titles=cfg.get("pronouns", {}).get("swap_titles", True))}
    res = name_resources if name_resources is not None else build_name_resources(cfg["names"])
    min_share = float(cfg["names"].get("min_share", 0.95))
    subject_only = bool(cfg["names"].get("subject_only", True))
    for pool in ("us", "in"):
        for tg in ("opposite", "same"):
            parts[f"name_{pool}_{tg}"] = NameSwap(res, pool, tg, min_share, subject_only=subject_only)
    parts["affiliation"] = AffiliationSwap(_yaml(cfg["affiliations_file"])["pairs"], nlp.tokenizer)
    parts["agentic_communal"] = AgenticCommunalRewrite(_yaml(cfg["agentic_communal_file"])["entries"])
    parts["_name_resources"] = res
    return parts


@dataclass
class Condition:
    name: str
    parts: list

    def apply(self, doc, gender: str, key: str) -> PerturbResult:
        return apply_replacements(doc, merge([p.replacements(doc, gender, key) for p in self.parts]))


def build_conditions(cfg: dict, parts: dict) -> list[Condition]:
    out = []
    for c in cfg["conditions"]:
        missing = [p for p in c["parts"] if p not in parts]
        if missing:
            raise ValueError(f"condition {c['name']!r} uses unknown parts {missing}")
        out.append(Condition(c["name"], [parts[p] for p in c["parts"]]))
    return out
