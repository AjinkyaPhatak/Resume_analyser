"""SkillSpan loader (Zhang et al., 2022; HF ``jjzha/skillspan``).

Each line is one sentence: ``tokens`` plus two independent BIO layers, ``tags_skill``
and ``tags_knowledge`` (tags are bare "B"/"I"/"O"). The layers may overlap, e.g. a
knowledge span nested in a skill span. Spans are returned per layer with token offsets
(end exclusive).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from research.common.config import repo_path


@dataclass(frozen=True)
class GoldSentence:
    doc_idx: int
    source: str                 # "house" | "tech"
    tokens: tuple[str, ...]
    skill: tuple[tuple[int, int], ...]
    knowledge: tuple[tuple[int, int], ...]

    @property
    def all_spans(self) -> set[tuple[int, int]]:
        return set(self.skill) | set(self.knowledge)


def bio_to_spans(tags: list[str]) -> list[tuple[int, int]]:
    """Convert a BIO sequence to (start, end) spans. An ``I`` with no open span starts
    a new span (lenient, as in seqeval's default IOB handling)."""
    spans: list[tuple[int, int]] = []
    start = None
    for i, tag in enumerate(list(tags) + ["O"]):
        tag = tag.split("-")[0]
        if tag == "B" or tag == "O":
            if start is not None:
                spans.append((start, i))
                start = None
            if tag == "B":
                start = i
        elif tag == "I":
            if start is None:
                start = i
        else:
            raise ValueError(f"Unexpected BIO tag {tag!r}")
    return spans


def load_split(path: str | Path) -> list[GoldSentence]:
    out: list[GoldSentence] = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            r = json.loads(line)
            n = len(r["tokens"])
            if len(r["tags_skill"]) != n or len(r["tags_knowledge"]) != n:
                raise ValueError(f"{path}:{line_no}: tag/token length mismatch")
            out.append(
                GoldSentence(
                    doc_idx=int(r["idx"]),
                    source=r.get("source", ""),
                    tokens=tuple(r["tokens"]),
                    skill=tuple(bio_to_spans(r["tags_skill"])),
                    knowledge=tuple(bio_to_spans(r["tags_knowledge"])),
                )
            )
    return out


def load_skillspan(local_dir: str | Path, splits=("train", "dev", "test")) -> dict[str, list[GoldSentence]]:
    d = repo_path(local_dir)
    missing = [s for s in splits if not (d / f"{s}.json").is_file()]
    if missing:
        raise FileNotFoundError(
            f"SkillSpan split(s) {missing} not found in {d}. Run: "
            "python -m research.data.download skillspan"
        )
    return {s: load_split(d / f"{s}.json") for s in splits}
