"""Candidate pools: for each JD, N bios with a controlled relevant/irrelevant mix.

Per pool (defaults in configs/data_prep.yaml):
  * ``n_relevant`` bios of the JD's occupation, half female and half male;
  * ``n_candidates - n_relevant`` bios of other occupations, half female and half male.
    By default the other occupation is drawn uniformly for each slot (so the huge
    professor/physician classes don't dominate); ``proportional`` samples bios directly.
Bios are drawn without replacement within a pool and may reappear across pools.
Everything uses one seeded ``numpy.random.Generator``.

Output: a long DataFrame, one row per (jd_id, bio_id), with binary + graded relevance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .relevance import Relevance


class PoolError(ValueError):
    pass


def _take(rng, ids: np.ndarray, k: int, what: str) -> list:
    if k > len(ids):
        raise PoolError(f"need {k} {what}, only {len(ids)} available")
    return list(rng.choice(ids, size=k, replace=False))


def build_pools(bios: pd.DataFrame, jds: pd.DataFrame, rel: Relevance, n_candidates: int,
                n_relevant: int, rng: np.random.Generator,
                irrelevant_sampling: str = "uniform_occupation") -> pd.DataFrame:
    if n_relevant % 2 or (n_candidates - n_relevant) % 2:
        raise ValueError("n_relevant and n_candidates - n_relevant must be even for gender balance")
    if irrelevant_sampling not in ("uniform_occupation", "proportional"):
        raise ValueError(f"unknown irrelevant_sampling {irrelevant_sampling!r}")
    by = {key: g["bio_id"].to_numpy() for key, g in bios.groupby(["occupation", "gender"])}
    occs = sorted(bios["occupation"].unique())
    bio_occ = dict(zip(bios["bio_id"], bios["occupation"]))
    bio_gender = dict(zip(bios["bio_id"], bios["gender"]))
    half_rel, half_irr = n_relevant // 2, (n_candidates - n_relevant) // 2

    rows = []
    for jd in jds.sort_values("jd_id").itertuples(index=False):
        occ = jd.occupation
        chosen: list = []
        for g in ("F", "M"):
            chosen += _take(rng, by.get((occ, g), np.array([])), half_rel, f"{g} {occ} bios")
        others = [o for o in occs if o != occ]
        for g in ("F", "M"):
            if irrelevant_sampling == "proportional":
                pool_ids = np.concatenate([by[(o, g)] for o in others if (o, g) in by])
                chosen += _take(rng, pool_ids, half_irr, f"{g} non-{occ} bios")
            else:
                picked: set = set()
                guard = 0
                while len(picked) < half_irr:
                    guard += 1
                    if guard > half_irr * 100:
                        raise PoolError(f"could not fill irrelevant {g} slots for {occ}")
                    o = others[rng.integers(len(others))]
                    ids = by.get((o, g))
                    if ids is None or len(ids) == 0:
                        continue
                    b = ids[rng.integers(len(ids))]
                    picked.add(b)
                chosen += sorted(picked)
        for b in chosen:
            rows.append({"jd_id": jd.jd_id, "jd_occupation": occ, "bio_id": b,
                         "bio_occupation": bio_occ[b], "bio_gender": bio_gender[b],
                         "rel_binary": rel.binary(bio_occ[b], occ), "rel_graded": rel.graded(bio_occ[b], occ)})
    return pd.DataFrame(rows)


def select_jds(jds: pd.DataFrame, per_occupation: int, min_per_occupation: int, dev_fraction: float,
               rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Sample up to ``per_occupation`` JDs per occupation and split them into dev/test JDs.

    Occupations with fewer than ``min_per_occupation`` mapped JDs get no pools (their
    bios still appear as irrelevant candidates). Returns (dev_jds, test_jds, coverage).
    """
    dev_parts, test_parts, coverage = [], [], {}
    for occ, g in jds.sort_values("jd_id").groupby("occupation"):
        n_avail = len(g)
        if n_avail < min_per_occupation:
            coverage[occ] = {"available": n_avail, "used": 0, "dev": 0, "test": 0}
            continue
        take = g.iloc[rng.permutation(n_avail)[: min(per_occupation, n_avail)]]
        n_dev = int(round(dev_fraction * len(take)))
        dev_parts.append(take.iloc[:n_dev])
        test_parts.append(take.iloc[n_dev:])
        coverage[occ] = {"available": n_avail, "used": len(take), "dev": n_dev, "test": len(take) - n_dev}
    cat = lambda parts: (pd.concat(parts, ignore_index=True) if parts else jds.iloc[0:0])  # noqa: E731
    return cat(dev_parts), cat(test_parts), coverage
