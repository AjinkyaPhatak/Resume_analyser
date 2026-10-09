"""BiasBios loader (De-Arteaga et al., 2019; HF ``LabHC/bias_in_bios``, Ravfogel et al. 2020 version).

``hard_text`` is the biography with its first sentence removed (the sentence that
states the occupation, and usually the full name). Gender is binary in the source data
(0 = male, 1 = female); we keep that coding and say so wherever results are reported.

Splits:
  * ``official`` (default): the train/dev/test split shipped with the dataset, which
    prior work on this version uses. Keeping it makes numbers comparable.
  * ``stratified``: a fresh split of the pooled data, stratified on
    (occupation, gender), with a fixed seed and configurable fractions.
Both apply the same cleaning: drop empty/very short bios, drop duplicate texts within a
split, and drop dev/test bios whose text also appears in an earlier split (leakage).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.common.config import repo_path

# Label order from the dataset card (LabHC/bias_in_bios README).
PROFESSIONS = (
    "accountant", "architect", "attorney", "chiropractor", "comedian", "composer", "dentist",
    "dietitian", "dj", "filmmaker", "interior_designer", "journalist", "model", "nurse",
    "painter", "paralegal", "pastor", "personal_trainer", "photographer", "physician", "poet",
    "professor", "psychologist", "rapper", "software_engineer", "surgeon", "teacher", "yoga_teacher",
)
GENDERS = ("M", "F")  # index = source label
SPLITS = ("train", "dev", "test")


def _split_file(local_dir: Path, split: str) -> Path:
    matches = sorted((local_dir / "data").glob(f"{split}-*.parquet"))
    if not matches:
        raise FileNotFoundError(
            f"BiasBios {split} parquet not found under {local_dir}/data. Run: "
            "python -m research.data.download biasbios"
        )
    return matches[0]


def load_raw(local_dir: str | Path) -> dict[str, pd.DataFrame]:
    d = repo_path(local_dir)
    return {s: pd.read_parquet(_split_file(d, s)) for s in SPLITS}


def to_frame(raw: pd.DataFrame, split: str) -> pd.DataFrame:
    if not {"hard_text", "profession", "gender"} <= set(raw.columns):
        raise ValueError(f"Unexpected BiasBios columns: {list(raw.columns)}")
    df = pd.DataFrame({
        "bio_id": [f"{split}-{i}" for i in range(len(raw))],
        "text": raw["hard_text"].astype(str).str.strip(),
        "occupation_id": raw["profession"].astype(int),
        "gender_id": raw["gender"].astype(int),
        "split": split,
    })
    if not df["occupation_id"].between(0, len(PROFESSIONS) - 1).all():
        raise ValueError("profession label out of range")
    if not df["gender_id"].isin([0, 1]).all():
        raise ValueError("gender label not in {0, 1}")
    df["occupation"] = df["occupation_id"].map(dict(enumerate(PROFESSIONS)))
    df["gender"] = df["gender_id"].map(dict(enumerate(GENDERS)))
    df["n_words"] = df["text"].str.split().str.len()
    return df


def clean(frames: dict[str, pd.DataFrame], min_words: int = 5) -> tuple[dict[str, pd.DataFrame], dict]:
    """Apply the cleaning rules in split order (train, dev, test). Returns frames + counts."""
    stats: dict[str, dict[str, int]] = {}
    seen: set[str] = set()
    out = {}
    for split in SPLITS:
        df = frames[split]
        n0 = len(df)
        short = df["n_words"] < min_words
        df = df[~short]
        dup = df["text"].duplicated(keep="first")
        df = df[~dup]
        leak = df["text"].isin(seen)
        df = df[~leak]
        seen.update(df["text"])
        out[split] = df.reset_index(drop=True)
        stats[split] = {"raw": n0, "too_short": int(short.sum()), "duplicate_in_split": int(dup.sum()),
                        "overlaps_earlier_split": int(leak.sum()), "kept": len(df)}
    return out, stats


def stratified_resplit(frames: dict[str, pd.DataFrame], seed: int,
                       fractions: tuple[float, float, float] = (0.65, 0.10, 0.25)) -> dict[str, pd.DataFrame]:
    """Pool all splits and re-split, stratified on occupation x gender."""
    from sklearn.model_selection import train_test_split

    if abs(sum(fractions) - 1.0) > 1e-9:
        raise ValueError("fractions must sum to 1")
    pool = pd.concat(frames.values(), ignore_index=True)
    strata = pool["occupation"] + "|" + pool["gender"]
    rest, test = train_test_split(pool, test_size=fractions[2], stratify=strata, random_state=seed)
    rest_strata = rest["occupation"] + "|" + rest["gender"]
    dev_share = fractions[1] / (fractions[0] + fractions[1])
    train, dev = train_test_split(rest, test_size=dev_share, stratify=rest_strata, random_state=seed)
    out = {}
    for name, df in (("train", train), ("dev", dev), ("test", test)):
        df = df.sort_values("bio_id").reset_index(drop=True).copy()
        df["split"] = name
        out[name] = df
    return out


def load_biasbios(cfg: dict) -> tuple[dict[str, pd.DataFrame], dict]:
    """Load, clean and split according to ``cfg['biasbios']``. Returns (frames, stats)."""
    bcfg = cfg.get("biasbios", {})
    raw = load_raw(cfg["datasets"]["biasbios"]["local_dir"])
    frames = {s: to_frame(raw[s], s) for s in SPLITS}
    frames, stats = clean(frames, min_words=int(bcfg.get("min_words", 5)))
    strategy = bcfg.get("split_strategy", "official")
    if strategy == "stratified":
        frames = stratified_resplit(frames, int(cfg["seed"]), tuple(bcfg.get("fractions", (0.65, 0.10, 0.25))))
    elif strategy != "official":
        raise ValueError(f"split_strategy must be 'official' or 'stratified', got {strategy!r}")
    return frames, {"cleaning": stats, "split_strategy": strategy}
