"""Seeding and device selection."""

from __future__ import annotations

import os
import random
import warnings

import numpy as np


def set_seed(seed: int, deterministic: bool = False) -> None:
    """Seed Python, NumPy and torch (CPU + all CUDA devices).

    ``PYTHONHASHSEED`` only affects interpreters started *after* this call (e.g.
    DataLoader workers or subprocesses); the current process's str-hash order is
    fixed at startup. Code that needs a stable order must therefore sort rather than
    rely on set/dict iteration of strings.

    ``deterministic=True`` additionally asks torch for deterministic kernels
    (warn-only, since some ops have no deterministic implementation).
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch
    except ImportError:
        return
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.use_deterministic_algorithms(True, warn_only=True)
        torch.backends.cudnn.benchmark = False


def make_rng(seed: int) -> np.random.Generator:
    """A local NumPy generator. Prefer passing these around over global state."""
    return np.random.default_rng(seed)


def get_device(preference: str = "auto") -> str:
    """Resolve ``auto`` | ``cpu`` | ``cuda`` to a usable device string.

    ``auto`` uses CUDA when available and falls back to CPU. Asking for ``cuda``
    without one available falls back to CPU with a warning instead of crashing, so
    configs stay portable between machines.
    """
    preference = (preference or "auto").lower()
    if preference == "cpu":
        return "cpu"
    try:
        import torch

        has_cuda = torch.cuda.is_available()
    except ImportError:
        has_cuda = False
    if preference in ("auto", "cuda"):
        if has_cuda:
            return "cuda"
        if preference == "cuda":
            warnings.warn("CUDA requested but not available; falling back to CPU.")
        return "cpu"
    raise ValueError(f"Unknown device preference: {preference!r}")
