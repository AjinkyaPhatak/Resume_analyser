import json
import random

import numpy as np
import pytest

from research.common.cli import base_parser, setup_run
from research.common.config import apply_overrides, deep_merge, get_dotted, load_config
from research.common.embedding_cache import CachedEncoder, EmbeddingCache, text_key
from research.common.provenance import git_info, write_run_metadata
from research.common.seed import get_device, set_seed
from research.scorers.base import BaseScorer, Scorer


# --- config -------------------------------------------------------------------

def _write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_deep_merge_does_not_mutate_inputs():
    base = {"a": {"b": 1, "c": 2}, "d": 3}
    over = {"a": {"b": 10}}
    merged = deep_merge(base, over)
    assert merged == {"a": {"b": 10, "c": 2}, "d": 3}
    assert base["a"]["b"] == 1


def test_load_config_inherits_and_overrides(tmp_path):
    _write(tmp_path / "parent.yaml", "seed: 1\nscorer:\n  agg: maxsim_mean\n  k: 5\n")
    child = _write(tmp_path / "child.yaml", "base: parent.yaml\nscorer:\n  agg: hungarian\n")
    cfg = load_config(child, ["scorer.k=7", "new.list=[a, b]"])
    assert cfg["seed"] == 1
    assert cfg["scorer"] == {"agg": "hungarian", "k": 7}
    assert cfg["new"]["list"] == ["a", "b"]
    assert "base" not in cfg


def test_load_config_detects_cycles(tmp_path):
    _write(tmp_path / "a.yaml", "base: b.yaml\n")
    _write(tmp_path / "b.yaml", "base: a.yaml\n")
    with pytest.raises(ValueError, match="cycle"):
        load_config(tmp_path / "a.yaml")


def test_override_requires_equals():
    with pytest.raises(ValueError):
        apply_overrides({}, ["no_equals_sign"])


def test_get_dotted_default():
    assert get_dotted({"a": {"b": 2}}, "a.b") == 2
    assert get_dotted({"a": {}}, "a.x", None) is None
    with pytest.raises(KeyError):
        get_dotted({}, "a.b")


def test_repo_base_config_loads():
    cfg = load_config("configs/base.yaml")
    assert isinstance(cfg["seed"], int)
    assert cfg["device"] in ("auto", "cpu", "cuda")


def test_cli_subset_and_seed(tmp_path):
    cfg_path = _write(tmp_path / "c.yaml", "seed: 5\n")
    args = base_parser("t").parse_args(["--config", str(cfg_path), "--subset", "20"])
    cfg = setup_run(args)
    assert cfg["subset"] == 20
    a = random.random()
    setup_run(args)
    assert random.random() == a


def test_cli_rejects_nonpositive_subset(tmp_path):
    cfg_path = _write(tmp_path / "c.yaml", "seed: 5\n")
    args = base_parser("t").parse_args(["--config", str(cfg_path), "--subset", "0"])
    with pytest.raises(SystemExit):
        setup_run(args)


# --- seeding / device -----------------------------------------------------------

def test_set_seed_reproducible():
    torch = pytest.importorskip("torch")
    set_seed(123)
    a = (random.random(), np.random.rand(), torch.rand(1).item())
    set_seed(123)
    b = (random.random(), np.random.rand(), torch.rand(1).item())
    assert a == b


def test_get_device():
    assert get_device("cpu") == "cpu"
    assert get_device("auto") in ("cpu", "cuda")
    with pytest.raises(ValueError):
        get_device("tpu")


# --- provenance -----------------------------------------------------------------

def test_write_run_metadata(tmp_path):
    path = write_run_metadata(tmp_path, {"seed": 1}, extra={"note": "x"})
    meta = json.loads(path.read_text(encoding="utf-8"))
    assert meta["config"] == {"seed": 1}
    assert meta["note"] == "x"
    assert set(meta["git"]) == {"commit", "dirty", "branch"}


def test_git_info_finds_commit():
    info = git_info()
    if info["commit"] is None:
        pytest.skip("git not available")
    assert len(info["commit"]) == 40


# --- embedding cache ------------------------------------------------------------

class _CountingEncoder:
    """Deterministic fake encoder: vector derived from the text hash."""

    def __init__(self):
        self.calls: list[list[str]] = []

    def __call__(self, texts):
        self.calls.append(list(texts))
        out = []
        for t in texts:
            rng = np.random.default_rng(int(text_key(t)[:8], 16))
            out.append(rng.normal(size=8))
        return np.array(out)


def test_cached_encoder_only_encodes_misses(tmp_path):
    fake = _CountingEncoder()
    enc = CachedEncoder("fake-model", cache_dir=tmp_path, encode_fn=fake)
    v1 = enc.encode(["python", "java", "python"])
    assert v1.shape == (3, 8)
    assert fake.calls == [["python", "java"]]  # deduplicated
    np.testing.assert_allclose(v1[0], v1[2])
    np.testing.assert_allclose(np.linalg.norm(v1, axis=1), 1.0, rtol=1e-5)

    v2 = enc.encode(["java", "sql"])
    assert fake.calls[-1] == ["sql"]
    np.testing.assert_allclose(v2[0], v1[1])


def test_cache_persists_across_instances(tmp_path):
    fake = _CountingEncoder()
    CachedEncoder("fake-model", cache_dir=tmp_path, encode_fn=fake).encode(["a", "b"])
    fake2 = _CountingEncoder()
    enc2 = CachedEncoder("fake-model", cache_dir=tmp_path, encode_fn=fake2)
    enc2.encode(["a", "b"])
    assert fake2.calls == []
    assert enc2.n_encoded == 0


def test_encoder_without_cache_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake = _CountingEncoder()
    enc = CachedEncoder("fake-model", cache_dir=None, encode_fn=fake)
    v = enc.encode(["a", "b", "a"])
    assert v.shape == (3, 8) and enc.cache is None
    enc.encode(["a"])
    assert fake.calls == [["a", "b"], ["a"]]       # nothing remembered between calls
    assert list(tmp_path.iterdir()) == []


def test_cache_namespaces_are_isolated(tmp_path):
    a = CachedEncoder("model-a", cache_dir=tmp_path, encode_fn=_CountingEncoder())
    b = CachedEncoder("model-a", cache_dir=tmp_path, normalize=False, encode_fn=_CountingEncoder())
    a.encode(["x"])
    assert len(a.cache) == 1
    assert len(b.cache) == 0
    assert a.cache.path != b.cache.path


def test_cache_roundtrip_exact(tmp_path):
    cache = EmbeddingCache("ns", tmp_path)
    vec = np.arange(5, dtype=np.float32)
    cache.put_many({"k": vec})
    np.testing.assert_array_equal(cache.get_many(["k", "missing"])["k"], vec)


def test_encode_empty_raises(tmp_path):
    enc = CachedEncoder("m", cache_dir=tmp_path, encode_fn=_CountingEncoder())
    with pytest.raises(ValueError):
        enc.encode([])


# --- scorer interface -----------------------------------------------------------

class _OverlapScorer(BaseScorer):
    name = "overlap"

    def score(self, resume, jd):
        r, j = set(resume.lower().split()), set(jd.lower().split())
        return len(r & j) / max(len(j), 1)


def test_scorer_protocol_and_batch():
    s = _OverlapScorer()
    assert isinstance(s, Scorer)
    pairs = [("python sql", "python sql"), ("cooking", "python sql")]
    assert s.score_batch(pairs) == [1.0, 0.0]


def test_protocol_rejects_incomplete_object():
    class NotAScorer:
        name = "x"

        def score(self, resume, jd):
            return 0.0

    assert not isinstance(NotAScorer(), Scorer)
