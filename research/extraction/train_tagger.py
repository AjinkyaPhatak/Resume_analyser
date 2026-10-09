"""Fine-tuning loop for MultiLayerTagger on SkillSpan-style data.

Model selection uses dev exact-match span F1 (skill ∪ knowledge). The test split is
never seen here; it's scored afterwards by eval_extraction.
"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass

import torch

from research.data.skillspan import GoldSentence
from research.metrics.span_metrics import SpanEvaluator

from .token_classifier import MultiLayerTagger, encode_batch, predict_tags, spans_to_bio


@dataclass
class TrainConfig:
    lr: float = 5e-5
    weight_decay: float = 0.01
    batch_size: int = 16
    eval_batch_size: int = 64
    max_epochs: int = 10
    patience: int = 3
    warmup_ratio: float = 0.1
    max_grad_norm: float = 1.0
    max_length: int = 256
    seed: int = 13
    device: str = "cpu"
    log_every: int = 50
    amp: bool = True             # fp16 autocast; only takes effect on CUDA


def _gold_tags(sent: GoldSentence) -> dict[str, list[str]]:
    n = len(sent.tokens)
    return {"skill": spans_to_bio(n, sent.skill), "knowledge": spans_to_bio(n, sent.knowledge)}


def evaluate_tagger(model, tokenizer, sents: list[GoldSentence], cfg: TrainConfig) -> dict:
    preds, n_trunc = predict_tags(model, tokenizer, [list(s.tokens) for s in sents], cfg.device,
                                  cfg.eval_batch_size, cfg.max_length, amp=cfg.amp)
    from research.data.skillspan import bio_to_spans
    from .base import TypedSpan

    ev = SpanEvaluator()
    for sent, p in zip(sents, preds):
        spans = [TypedSpan(s, e, "", layer, "model") for layer, tags in p.items() for s, e in bio_to_spans(tags)]
        ev.add(spans, {"all": sent.all_spans, "skill": sent.skill, "knowledge": sent.knowledge})
    by = {(r["group"], r["view"], r["mode"]): r for r in ev.rows()}
    return {
        "exact_f1": by[("all", "all", "exact")]["f1"],
        "partial_f1": by[("all", "all", "partial")]["f1"],
        "exact_p": by[("all", "all", "exact")]["precision"],
        "exact_r": by[("all", "all", "exact")]["recall"],
        "n_truncated": n_trunc,
    }


def train_tagger(model: MultiLayerTagger, tokenizer, train: list[GoldSentence], dev: list[GoldSentence],
                 cfg: TrainConfig, log=print) -> tuple[MultiLayerTagger, list[dict]]:
    """Train; return the model loaded with its best-dev-F1 weights, plus the history."""
    from transformers import get_linear_schedule_with_warmup

    torch.manual_seed(cfg.seed)
    gen = torch.Generator().manual_seed(cfg.seed)
    model.to(cfg.device)
    no_decay = ("bias", "LayerNorm.weight", "layer_norm.weight")
    groups = [
        {"params": [p for n, p in model.named_parameters() if not any(k in n for k in no_decay)],
         "weight_decay": cfg.weight_decay},
        {"params": [p for n, p in model.named_parameters() if any(k in n for k in no_decay)],
         "weight_decay": 0.0},
    ]
    opt = torch.optim.AdamW(groups, lr=cfg.lr)
    steps_per_epoch = (len(train) + cfg.batch_size - 1) // cfg.batch_size
    total = steps_per_epoch * cfg.max_epochs
    sched = get_linear_schedule_with_warmup(opt, int(cfg.warmup_ratio * total), total)

    use_amp = cfg.amp and str(cfg.device).startswith("cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    best_f1, best_state, bad_epochs, history = -1.0, None, 0, []
    for epoch in range(1, cfg.max_epochs + 1):
        model.train()
        t0 = time.perf_counter()
        order = torch.randperm(len(train), generator=gen).tolist()
        running = 0.0
        for step, b in enumerate(range(0, len(order), cfg.batch_size), 1):
            sents = [train[i] for i in order[b : b + cfg.batch_size]]
            tags = [_gold_tags(s) for s in sents]
            batch, _, _ = encode_batch(
                tokenizer, [s.tokens for s in sents],
                {layer: [t[layer] for t in tags] for layer in model.layers}, cfg.max_length,
            )
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=use_amp):
                logits = model(batch["input_ids"].to(cfg.device), batch["attention_mask"].to(cfg.device))
                loss = model.loss(logits, {k: v.to(cfg.device) for k, v in batch["labels"].items()})
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.max_grad_norm)
            scaler.step(opt)
            scaler.update()
            sched.step()
            opt.zero_grad()
            running += loss.item()
            if cfg.log_every and step % cfg.log_every == 0:
                log(f"epoch {epoch} step {step}/{steps_per_epoch} loss {running / step:.4f}")
        dev_m = evaluate_tagger(model, tokenizer, dev, cfg)
        rec = {"epoch": epoch, "train_loss": running / max(steps_per_epoch, 1),
               "seconds": time.perf_counter() - t0, **{f"dev_{k}": v for k, v in dev_m.items()}}
        history.append(rec)
        log(f"epoch {epoch}: loss {rec['train_loss']:.4f} dev exact F1 {dev_m['exact_f1']:.4f} "
            f"partial F1 {dev_m['partial_f1']:.4f} ({rec['seconds']:.0f}s)")
        if dev_m["exact_f1"] > best_f1:
            best_f1, bad_epochs = dev_m["exact_f1"], 0
            best_state = copy.deepcopy({k: v.detach().cpu() for k, v in model.state_dict().items()})
        else:
            bad_epochs += 1
            if bad_epochs >= cfg.patience:
                log(f"early stop after epoch {epoch} (best dev exact F1 {best_f1:.4f})")
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model, history
