"""Shared argparse setup so every experiment has the same flags.

    python -m research.experiments.<name> --config configs/main.yaml [--subset N] [--set k=v ...]
"""

from __future__ import annotations

import argparse

from .config import load_config
from .seed import set_seed


def base_parser(description: str, default_config: str | None = None) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument(
        "--config",
        default=default_config,
        required=default_config is None,
        help="YAML config (absolute, cwd-relative, or relative to research/).",
    )
    p.add_argument(
        "--subset",
        type=int,
        default=None,
        metavar="N",
        help="Use only the first N items (after seeded shuffling) for a quick run.",
    )
    p.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override a config value by dotted key; repeatable.",
    )
    return p


def setup_run(args: argparse.Namespace) -> dict:
    """Load config, record --subset in it, and seed everything."""
    cfg = load_config(args.config, args.overrides)
    if args.subset is not None:
        if args.subset <= 0:
            raise SystemExit("--subset must be a positive integer")
        cfg["subset"] = args.subset
    set_seed(int(cfg["seed"]), deterministic=bool(cfg.get("deterministic", False)))
    return cfg
