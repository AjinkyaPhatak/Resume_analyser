"""Relevance labels between a bio's occupation and a JD's occupation.

Binary:  1 if same occupation, else 0.
Graded:  2 if same occupation;
         1 if both occupations fall in the same SOC 2018 group (major group = first two
           digits by default, e.g. 23 Legal: attorney ~ paralegal; 29 Healthcare
           practitioners: physician ~ nurse ~ dentist ...; ``level: minor`` uses the first
           four characters, e.g. 27-2 Entertainers vs 27-3 Media workers);
         0 otherwise.
SOC codes come from configs/occupations.yaml (verified against O*NET-SOC 2019).
"""

from __future__ import annotations


def soc_group(code: str, level: str = "major") -> str:
    if level == "major":
        return code[:2]
    if level == "minor":
        return code[:4]
    raise ValueError(f"level must be 'major' or 'minor', got {level!r}")


class Relevance:
    def __init__(self, occ_cfg: dict, level: str = "major"):
        self.level = level
        self.group = {name: soc_group(spec["soc"], level) for name, spec in occ_cfg.items()}

    def binary(self, bio_occ: str, jd_occ: str) -> int:
        return int(bio_occ == jd_occ)

    def graded(self, bio_occ: str, jd_occ: str) -> int:
        if bio_occ == jd_occ:
            return 2
        return int(self.group[bio_occ] == self.group[jd_occ])

    def related(self, occ: str) -> list[str]:
        """Other occupations that get grade 1 with ``occ``."""
        return sorted(o for o, g in self.group.items() if o != occ and g == self.group[occ])
