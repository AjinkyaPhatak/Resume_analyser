"""Phase 1 (optional): fine-tune a token classifier on SkillSpan train, select on dev.

    python -m research.experiments.train_extractor --config configs/train_extractor.yaml [--subset N]

Saves the best-dev model to ``finetune.output_dir/seed{seed}`` together with
``history.json`` and ``run_meta.json``. Test-split scores come from eval_extraction
(add the model as a ``token_classifier`` extractor), not from this script.
Practical only on a GPU: on this machine's CPU one epoch takes hours.
"""

from __future__ import annotations

import json

from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.common.provenance import write_run_metadata
from research.common.seed import get_device, make_rng
from research.data.skillspan import load_skillspan
from research.extraction.token_classifier import MultiLayerTagger
from research.extraction.train_tagger import TrainConfig, train_tagger


def main(argv=None):
    args = base_parser(__doc__, default_config="configs/train_extractor.yaml").parse_args(argv)
    cfg = setup_run(args)
    ft = cfg["finetune"]
    device = get_device(cfg.get("device", "auto"))
    data = load_skillspan(cfg["datasets"]["skillspan"]["local_dir"], splits=("train", "dev"))
    train, dev = data["train"], data["dev"]
    if cfg.get("subset"):
        rng = make_rng(cfg["seed"])
        train = [train[i] for i in sorted(rng.permutation(len(train))[: cfg["subset"]])]
        dev = [dev[i] for i in sorted(rng.permutation(len(dev))[: cfg["subset"]])]

    from transformers import AutoModel, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(ft["base_model"], revision=ft["revision"])
    enc = AutoModel.from_pretrained(ft["base_model"], revision=ft["revision"])
    model = MultiLayerTagger(enc, ft["layers"], dropout=ft["dropout"])
    tcfg = TrainConfig(
        lr=ft["lr"], weight_decay=ft["weight_decay"], batch_size=ft["batch_size"],
        eval_batch_size=ft["eval_batch_size"], max_epochs=ft["max_epochs"], patience=ft["patience"],
        warmup_ratio=ft["warmup_ratio"], max_grad_norm=ft["max_grad_norm"], max_length=ft["max_length"],
        seed=int(cfg["seed"]), device=device, amp=bool(ft.get("amp", True)),
    )
    out_dir = repo_path(ft["output_dir"]) / f"seed{cfg['seed']}"
    if cfg.get("subset"):
        out_dir = out_dir.with_name(out_dir.name + f"_subset{cfg['subset']}")
    print(f"device={device} train={len(train)} dev={len(dev)} -> {out_dir}")
    model, history = train_tagger(model, tok, train, dev, tcfg, log=lambda m: print(m, flush=True))
    model.save(out_dir, tok, extra={"base_model": ft["base_model"], "revision": ft["revision"],
                                    "best_dev_exact_f1": max(h["dev_exact_f1"] for h in history)})
    (out_dir / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    write_run_metadata(out_dir, cfg, extra={"device": device, "n_train": len(train), "n_dev": len(dev)})
    print(f"saved {out_dir}")


if __name__ == "__main__":
    main()
