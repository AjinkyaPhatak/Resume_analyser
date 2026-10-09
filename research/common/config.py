"""YAML config loading.

Every hyperparameter lives in a YAML file under ``research/configs/``. A config may
inherit from another via a top-level ``base:`` key (a path relative to the file that
declares it); the child is deep-merged over the parent. Command-line overrides use
dotted keys, e.g. ``--set scorer.aggregation=hungarian``; values are parsed as YAML so
``--set seed=7`` gives an int and ``--set models=[a,b]`` gives a list.

Configs are plain nested dicts so they serialise to JSON unchanged for run logs.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

RESEARCH_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RESEARCH_ROOT.parent
CONFIG_DIR = RESEARCH_ROOT / "configs"

_MISSING = object()


def deep_merge(base: dict, override: dict) -> dict:
    """Return a new dict: ``override`` merged recursively over ``base``."""
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def resolve_config_path(path: str | Path) -> Path:
    """Accept absolute paths, cwd-relative paths, or paths relative to research/ ."""
    p = Path(path)
    for candidate in (p, Path.cwd() / p, RESEARCH_ROOT / p, CONFIG_DIR / p):
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"Config not found: {path}")


def _load_with_bases(path: Path, seen: tuple[Path, ...] = ()) -> dict:
    if path in seen:
        chain = " -> ".join(str(s) for s in (*seen, path))
        raise ValueError(f"Config inheritance cycle: {chain}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Top level of {path} must be a mapping")
    base_ref = data.pop("base", None)
    if base_ref is None:
        return data
    parent = _load_with_bases((path.parent / base_ref).resolve(), (*seen, path))
    return deep_merge(parent, data)


def set_dotted(cfg: dict, dotted_key: str, value: Any) -> None:
    keys = dotted_key.split(".")
    node = cfg
    for k in keys[:-1]:
        if not isinstance(node.get(k), dict):
            node[k] = {}
        node = node[k]
    node[keys[-1]] = value


def get_dotted(cfg: dict, dotted_key: str, default: Any = _MISSING) -> Any:
    node: Any = cfg
    for k in dotted_key.split("."):
        if not isinstance(node, dict) or k not in node:
            if default is _MISSING:
                raise KeyError(dotted_key)
            return default
        node = node[k]
    return node


def apply_overrides(cfg: dict, overrides: list[str] | None) -> dict:
    out = copy.deepcopy(cfg)
    for item in overrides or []:
        if "=" not in item:
            raise ValueError(f"Override must look like key=value, got: {item!r}")
        key, raw = item.split("=", 1)
        set_dotted(out, key.strip(), yaml.safe_load(raw))
    return out


def repo_path(p: str | Path) -> Path:
    """Paths in configs are relative to the repo root (or absolute)."""
    p = Path(p)
    return p if p.is_absolute() else REPO_ROOT / p


def load_config(path: str | Path, overrides: list[str] | None = None) -> dict:
    """Load a YAML config (resolving ``base:`` inheritance) and apply overrides."""
    resolved = resolve_config_path(path)
    cfg = _load_with_bases(resolved)
    cfg = apply_overrides(cfg, overrides)
    cfg["_config_path"] = str(resolved)
    return cfg
