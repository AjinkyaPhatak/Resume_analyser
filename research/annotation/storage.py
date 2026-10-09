"""Annotation storage: one append-only CSV per annotator (no Streamlit dependency).

Every save appends a row (pair_id, rating, comment, timestamp_utc). When a pair is rated
more than once, the LATEST row wins, so changing your mind never deletes history.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

FIELDS = ["pair_id", "rating", "comment", "timestamp_utc"]
_SAFE = re.compile(r"[^a-z0-9_-]+")


def annotator_id(name: str) -> str:
    """Filesystem-safe id from a free-text name ("Priya S." -> "priya_s")."""
    ident = _SAFE.sub("_", name.strip().lower()).strip("_")
    if not ident:
        raise ValueError("annotator name must contain letters or digits")
    return ident


def labels_path(labels_dir: str | Path, name: str) -> Path:
    return Path(labels_dir) / f"{annotator_id(name)}.csv"


def save_rating(path: Path, pair_id: str, rating: int, comment: str = "", scale=(0, 1, 2, 3)) -> None:
    if rating not in scale:
        raise ValueError(f"rating must be one of {list(scale)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({"pair_id": pair_id, "rating": int(rating), "comment": (comment or "").strip(),
                    "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})


def load_ratings(path: Path) -> pd.DataFrame:
    """Latest rating per pair for one annotator (empty frame if none yet)."""
    if not Path(path).exists():
        return pd.DataFrame(columns=FIELDS)
    df = pd.read_csv(path, dtype={"pair_id": str, "comment": str}, keep_default_na=False)
    return df.drop_duplicates("pair_id", keep="last").reset_index(drop=True)


def annotator_order(pair_ids: list[str], name: str) -> list[str]:
    """Per-annotator random order (seeded by the annotator id) to avoid order effects."""
    seed = int(hashlib.sha256(annotator_id(name).encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    return [pair_ids[i] for i in rng.permutation(len(pair_ids))]


def load_all(labels_dir: str | Path) -> pd.DataFrame:
    """Wide table: rows = pair_id, columns = annotator ids, values = latest ratings."""
    frames = {}
    for p in sorted(Path(labels_dir).glob("*.csv")):
        r = load_ratings(p)
        if len(r):
            frames[p.stem] = r.set_index("pair_id")["rating"].astype(int)
    return pd.DataFrame(frames).sort_index()
