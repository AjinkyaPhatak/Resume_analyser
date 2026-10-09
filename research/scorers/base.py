"""The single interface every matching method implements.

Scores are "higher = better fit". Scales differ between scorers (BM25 is unbounded,
cosine is in [-1, 1], the backend's match percent is in [0, 100]), so comparisons
across scorers use rank-based metrics or per-scorer normalisation, never raw values.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Scorer(Protocol):
    name: str

    def score(self, resume: str, jd: str) -> float: ...

    def score_batch(self, pairs: list[tuple[str, str]]) -> list[float]: ...


class BaseScorer:
    """Optional convenience base: subclasses implement ``score`` and get a loop-based
    ``score_batch``. Scorers that can batch efficiently (e.g. one encoder call for many
    documents) should override ``score_batch`` and keep ``score`` consistent with it.
    """

    name: str = "base"

    def score(self, resume: str, jd: str) -> float:
        raise NotImplementedError

    def score_batch(self, pairs: list[tuple[str, str]]) -> list[float]:
        return [float(self.score(r, j)) for r, j in pairs]

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"
