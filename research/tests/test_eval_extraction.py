"""Report-writing logic of eval_extraction, on hand-made metric rows (test-only values)."""

from research.experiments.eval_extraction import write_markdown


def _rows(name, split, exact_f1, partial_f1):
    out = []
    for view in ("all", "skill", "knowledge"):
        for mode, f1 in (("exact", exact_f1), ("partial", partial_f1)):
            out.append({"extractor": name, "split": split, "group": "all", "view": view, "mode": mode,
                        "precision": f1, "recall": f1, "f1": f1, "n_pred": 10, "n_gold": 10})
    return out


def test_seed_group_mean_sd(tmp_path):
    rows = _rows("m_s1", "test", 0.2, 0.4) + _rows("m_s2", "test", 0.4, 0.6) + _rows("solo", "test", 0.1, 0.3)
    cfg = {
        "eval": {"splits": ["test"]},
        "datasets": {"skillspan": {"hf_id": "x/y", "revision": "abcdef123"}},
        "extractors": [
            {"name": "m_s1", "seed_group": "m"}, {"name": "m_s2", "seed_group": "m"}, {"name": "solo"},
            {"name": "m_s3", "seed_group": "m"},  # not run -> must not enter the mean
        ],
    }
    out = tmp_path / "x.md"
    write_markdown(out, rows, {"m_s3": "missing"}, cfg, {"test": 5}, {})
    text = out.read_text(encoding="utf-8")
    assert "| m | 2 | test | 0.300 ± 0.141 | 0.500 ± 0.141 |" in text
    assert "m_s3" in text and "missing" in text  # listed under Not run
