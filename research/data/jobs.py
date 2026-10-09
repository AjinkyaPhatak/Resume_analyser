"""Job-description loader.

Primary source: Kaggle "LinkedIn Job Postings (2023-2024)" by arshkon
(https://www.kaggle.com/datasets/arshkon/linkedin-job-postings), CC BY-SA 4.0. It
needs a Kaggle login, so it's downloaded by hand (see research/data/README.md); only
``postings.csv`` is used. Required columns: ``job_id``, ``title``, ``description``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from research.common.config import repo_path

_WS = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    """Lower-case, unify separators, collapse whitespace. Keeps words like 'sr', 'ii'."""
    t = str(title).lower()
    t = re.sub(r"[‐-―]", "-", t)
    t = re.sub(r"[/|,;:()\[\]]", " ", t)
    return _WS.sub(" ", t).strip()


def load_postings(path: str | Path, min_words: int = 50) -> tuple[pd.DataFrame, dict]:
    """Load postings.csv -> DataFrame[jd_id, title, title_norm, text, n_words] + cleaning stats."""
    p = repo_path(path)
    if not p.is_file():
        raise FileNotFoundError(
            f"Job postings not found at {p}. Download the Kaggle dataset "
            "'arshkon/linkedin-job-postings' and put postings.csv there "
            "(see research/data/README.md)."
        )
    raw = pd.read_csv(p, usecols=lambda c: c in {"job_id", "title", "description"}, dtype=str)
    missing = {"job_id", "title", "description"} - set(raw.columns)
    if missing:
        raise ValueError(f"{p} lacks columns {sorted(missing)}")
    n0 = len(raw)
    df = raw.dropna(subset=["title", "description"]).copy()
    n_na = n0 - len(df)
    df["text"] = df["description"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    df["n_words"] = df["text"].str.split().str.len()
    short = df["n_words"] < min_words
    df = df[~short]
    dup = df["text"].duplicated(keep="first")
    df = df[~dup]
    out = pd.DataFrame({
        "jd_id": "li-" + df["job_id"].astype(str),
        "title": df["title"].astype(str).str.strip(),
        "title_norm": df["title"].map(normalize_title),
        "text": df["text"],
        "n_words": df["n_words"],
    }).reset_index(drop=True)
    if out["jd_id"].duplicated().any():
        raise ValueError("duplicate job_id values in postings")
    stats = {"raw": n0, "missing_title_or_description": n_na, "too_short": int(short.sum()),
             "duplicate_description": int(dup.sum()), "kept": len(out)}
    return out, stats
