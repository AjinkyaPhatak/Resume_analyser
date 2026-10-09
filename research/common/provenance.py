"""Run provenance: git commit, environment, and the exact config, logged per run."""

from __future__ import annotations

import datetime as _dt
import json
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

# Packages whose versions are recorded with every run.
_TRACKED_PACKAGES = (
    "numpy",
    "scipy",
    "scikit-learn",
    "torch",
    "transformers",
    "sentence-transformers",
    "spacy",
    "pyyaml",
)


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip()


def git_info() -> dict[str, Any]:
    """Commit hash and whether the working tree has uncommitted changes.

    A dirty tree means the hash alone does not reproduce the run; the flag is
    logged so results from dirty trees can be spotted and rerun.
    """
    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain")
    return {
        "commit": commit,
        "dirty": bool(status) if status is not None else None,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
    }


def package_versions(packages: tuple[str, ...] = _TRACKED_PACKAGES) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in packages:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def run_metadata(cfg: dict, extra: dict | None = None) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "argv": sys.argv,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "git": git_info(),
        "packages": package_versions(),
        "config": cfg,
    }
    try:
        import torch

        meta["cuda_available"] = torch.cuda.is_available()
        if meta["cuda_available"]:
            meta["cuda_device"] = torch.cuda.get_device_name(0)
    except ImportError:
        meta["cuda_available"] = None
    if extra:
        meta.update(extra)
    return meta


def write_run_metadata(out_dir: str | Path, cfg: dict, extra: dict | None = None) -> Path:
    """Write ``run_meta.json`` (config + git hash + env) into ``out_dir``."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "run_meta.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(run_metadata(cfg, extra), f, indent=2, default=str)
    return path
