"""Span-level precision / recall / F1 for extraction, micro-averaged over sentences.

Spans are (start, end) token offsets, end exclusive, compared within a sentence.

* exact:   a predicted span is correct iff a gold span has identical boundaries.
* partial: a predicted span is correct iff it overlaps some gold span by >= 1 token;
           a gold span is recalled iff some predicted span overlaps it by >= 1 token.
           Precision and recall are counted separately (not a 1-1 matching), so several
           short predictions inside one long gold span are all counted correct. This
           is lenient by design and is reported next to exact match, never instead of it.
Duplicate boundaries are collapsed before counting, on both sides.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

Span = tuple[int, int]


def _overlaps(a: Span, b: Span) -> bool:
    return a[0] < b[1] and b[0] < a[1]


@dataclass
class PRFCounter:
    """Accumulates counts; ``n_pred_correct`` and ``n_gold_found`` differ for partial."""

    n_pred: int = 0
    n_gold: int = 0
    n_pred_correct: int = 0
    n_gold_found: int = 0

    def add(self, pred: Iterable[Span], gold: Iterable[Span], mode: str) -> None:
        pred, gold = set(pred), set(gold)
        self.n_pred += len(pred)
        self.n_gold += len(gold)
        if mode == "exact":
            hit = len(pred & gold)
            self.n_pred_correct += hit
            self.n_gold_found += hit
        elif mode == "partial":
            self.n_pred_correct += sum(any(_overlaps(p, g) for g in gold) for p in pred)
            self.n_gold_found += sum(any(_overlaps(g, p) for p in pred) for g in gold)
        else:
            raise ValueError(f"mode must be 'exact' or 'partial', got {mode!r}")

    @property
    def precision(self) -> float:
        return self.n_pred_correct / self.n_pred if self.n_pred else 0.0

    @property
    def recall(self) -> float:
        return self.n_gold_found / self.n_gold if self.n_gold else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    def as_dict(self) -> dict:
        return {
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "n_pred": self.n_pred,
            "n_gold": self.n_gold,
        }


@dataclass
class SpanEvaluator:
    """Evaluate one extractor over many sentences, for several gold/pred views at once.

    ``views`` maps a view name to (pred label set or None for all, gold layer name).
    """

    views: dict[str, tuple[frozenset[str] | None, str]] = field(
        default_factory=lambda: {
            "all": (None, "all"),
            "skill": (frozenset({"skill", "verb_phrase"}), "skill"),
            "knowledge": (frozenset({"knowledge"}), "knowledge"),
        }
    )
    counters: dict[tuple[str, str, str], PRFCounter] = field(default_factory=dict)

    def add(self, pred_spans, gold_by_layer: dict[str, Iterable[Span]], group: str = "all") -> None:
        groups = ("all",) if group == "all" else ("all", group)
        for view, (labels, layer) in self.views.items():
            pred = {(s.start, s.end) for s in pred_spans if labels is None or s.label in labels}
            gold = set(gold_by_layer[layer])
            for g in groups:
                for mode in ("exact", "partial"):
                    key = (g, view, mode)
                    self.counters.setdefault(key, PRFCounter()).add(pred, gold, mode)

    def rows(self) -> list[dict]:
        out = []
        for (group, view, mode), c in sorted(self.counters.items()):
            out.append({"group": group, "view": view, "mode": mode, **c.as_dict()})
        return out
