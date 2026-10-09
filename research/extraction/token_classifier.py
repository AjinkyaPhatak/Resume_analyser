"""Extractor (d): a fine-tuned token-classification model (one encoder, two BIO heads).

SkillSpan has two independent, possibly overlapping layers (skill, knowledge), so a
single tag sequence can't represent them. We use one shared encoder with one 3-way
(O/B/I) linear head per layer, trained with the sum of the per-layer cross-entropies.
Zhang et al. (2022) train separate models per layer; the shared encoder halves
inference cost, and we note the difference when comparing with their numbers.

Word-level labels go on the first sub-token of each word; other sub-tokens are ignored
in the loss (-100). At inference a word's tag is the argmax at its first sub-token.
Words cut off by ``max_length`` are tagged O, and the number of truncated sentences is
counted and reported.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import torch
from torch import nn

from research.data.skillspan import bio_to_spans

from .base import TypedSpan, dedupe_spans

TAGS = ("O", "B", "I")
TAG2ID = {t: i for i, t in enumerate(TAGS)}
IGNORE = -100


class MultiLayerTagger(nn.Module):
    def __init__(self, encoder: nn.Module, layers: Sequence[str] = ("skill", "knowledge"), dropout: float = 0.1):
        super().__init__()
        self.encoder = encoder
        self.layers = tuple(layers)
        hidden = encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.heads = nn.ModuleDict({name: nn.Linear(hidden, len(TAGS)) for name in self.layers})

    def forward(self, input_ids, attention_mask, **_) -> dict[str, torch.Tensor]:
        h = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        h = self.dropout(h)
        return {name: head(h) for name, head in self.heads.items()}

    def loss(self, logits: dict[str, torch.Tensor], labels: dict[str, torch.Tensor]) -> torch.Tensor:
        ce = nn.CrossEntropyLoss(ignore_index=IGNORE)
        return sum(ce(logits[n].reshape(-1, len(TAGS)), labels[n].reshape(-1)) for n in self.layers)

    # --- persistence --------------------------------------------------------------
    def save(self, out_dir: str | Path, tokenizer, extra: dict | None = None) -> None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        self.encoder.config.save_pretrained(out)
        tokenizer.save_pretrained(out)
        torch.save(self.state_dict(), out / "tagger_state.pt")
        meta = {"layers": list(self.layers), "tags": list(TAGS), **(extra or {})}
        (out / "tagger_config.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, model_dir: str | Path, device: str = "cpu"):
        from transformers import AutoConfig, AutoModel, AutoTokenizer

        d = Path(model_dir)
        meta = json.loads((d / "tagger_config.json").read_text(encoding="utf-8"))
        encoder = AutoModel.from_config(AutoConfig.from_pretrained(d))
        model = cls(encoder, meta["layers"])
        model.load_state_dict(torch.load(d / "tagger_state.pt", map_location=device, weights_only=True))
        model.to(device).eval()
        return model, AutoTokenizer.from_pretrained(d), meta


def encode_batch(
    tokenizer,
    token_lists: Sequence[Sequence[str]],
    tags_by_layer: dict[str, Sequence[Sequence[str]]] | None = None,
    max_length: int = 256,
):
    """Tokenise pre-split words; optionally align word-level BIO tags to sub-tokens.

    Returns (batch dict of tensors, list of word_ids per item, n_truncated).
    """
    enc = tokenizer(
        [list(t) for t in token_lists],
        is_split_into_words=True,
        truncation=True,
        max_length=max_length,
        padding=True,
        return_tensors="pt",
    )
    word_ids = [enc.word_ids(i) for i in range(len(token_lists))]
    n_truncated = 0
    for i, toks in enumerate(token_lists):
        seen = {w for w in word_ids[i] if w is not None}
        if len(seen) < len(toks):
            n_truncated += 1
    batch = {"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]}
    if tags_by_layer is not None:
        labels = {}
        for layer, tag_lists in tags_by_layer.items():
            lab = torch.full(enc["input_ids"].shape, IGNORE, dtype=torch.long)
            for i, tags in enumerate(tag_lists):
                prev = None
                for j, w in enumerate(word_ids[i]):
                    if w is not None and w != prev:
                        lab[i, j] = TAG2ID[tags[w]]
                    prev = w
            labels[layer] = lab
        batch["labels"] = labels
    return batch, word_ids, n_truncated


def spans_to_bio(n: int, spans: Sequence[tuple[int, int]]) -> list[str]:
    """Inverse of bio_to_spans for non-overlapping spans within one layer."""
    tags = ["O"] * n
    for s, e in spans:
        tags[s] = "B"
        for k in range(s + 1, e):
            tags[k] = "I"
    return tags


@torch.no_grad()
def predict_tags(model: MultiLayerTagger, tokenizer, token_lists, device="cpu",
                 batch_size=32, max_length=256, amp: bool = True) -> tuple[list[dict[str, list[str]]], int]:
    """Word-level BIO tags per layer for each sentence, plus the truncation count."""
    model.eval()
    out: list[dict[str, list[str]]] = []
    n_trunc = 0
    for b in range(0, len(token_lists), batch_size):
        chunk = token_lists[b : b + batch_size]
        batch, word_ids, t = encode_batch(tokenizer, chunk, max_length=max_length)
        n_trunc += t
        with torch.autocast(device_type="cuda", dtype=torch.float16,
                            enabled=amp and str(device).startswith("cuda")):
            logits = model(batch["input_ids"].to(device), batch["attention_mask"].to(device))
        preds = {n: l.argmax(-1).cpu() for n, l in logits.items()}
        for i, toks in enumerate(chunk):
            item = {}
            for layer in model.layers:
                tags = ["O"] * len(toks)
                prev = None
                for j, w in enumerate(word_ids[i]):
                    if w is not None and w != prev:
                        tags[w] = TAGS[int(preds[layer][i, j])]
                    prev = w
                item[layer] = tags
            out.append(item)
    return out, n_trunc


class TokenClassifierExtractor:
    """Wraps a saved MultiLayerTagger behind the Extractor interface.

    Raw text is split into sentences (spaCy rule-based ``sentencizer``) and words
    (spaCy's rule-based English tokenizer; no statistical models), because the tagger
    was trained on single SkillSpan sentences and long JDs would otherwise be truncated.
    Each sentence is tagged separately; span offsets refer to the whole text.
    """

    def __init__(self, model_dir: str | Path, device: str = "cpu", batch_size: int = 32,
                 max_length: int = 256, name: str = "finetuned"):
        import spacy

        self.name = name
        self.device = device
        self.batch_size = batch_size
        self.max_length = max_length
        self.model, self.tokenizer, self.meta = MultiLayerTagger.load(model_dir, device)
        self._tok = spacy.blank("en")
        self._tok.add_pipe("sentencizer")
        self.n_truncated = 0

    def _spans(self, tokens, tags_by_layer, offsets=None) -> list[TypedSpan]:
        spans = []
        for layer, tags in tags_by_layer.items():
            for s, e in bio_to_spans(tags):
                sc, ec = (offsets[s][0], offsets[e - 1][1]) if offsets else (-1, -1)
                spans.append(TypedSpan(s, e, " ".join(tokens[s:e]), layer, "model", sc, ec))
        return dedupe_spans(spans)

    def extract_tokens_batch(self, token_lists, batch_size: int | None = None) -> list[list[TypedSpan]]:
        token_lists = [list(t) for t in token_lists]
        preds, t = predict_tags(self.model, self.tokenizer, token_lists, self.device,
                                batch_size or self.batch_size, self.max_length)
        self.n_truncated += t
        return [self._spans(toks, p) for toks, p in zip(token_lists, preds)]

    def extract_tokens(self, tokens) -> list[TypedSpan]:
        return self.extract_tokens_batch([tokens])[0]

    def _sentences(self, text: str):
        """[(words, char offsets, index of first word in the whole text)] per sentence."""
        doc = self._tok(text)
        out, base = [], 0
        for sent in doc.sents:
            toks = [t for t in sent if not t.is_space]
            if toks:
                out.append(([t.text for t in toks], [(t.idx, t.idx + len(t.text)) for t in toks], base))
                base += len(toks)
        return out

    def extract_batch(self, texts, batch_size: int | None = None) -> list[list[TypedSpan]]:
        sents_per_text = [self._sentences(t) for t in texts]
        flat = [(i, s) for i, ss in enumerate(sents_per_text) for s in ss]
        preds, t = predict_tags(self.model, self.tokenizer, [s[0] for _, s in flat], self.device,
                                batch_size or self.batch_size, self.max_length)
        self.n_truncated += t
        spans: list[list[TypedSpan]] = [[] for _ in texts]
        for (i, (words, offs, base)), p in zip(flat, preds):
            for sp in self._spans(words, p, offs):
                spans[i].append(TypedSpan(sp.start + base, sp.end + base, sp.text, sp.label, sp.source,
                                          sp.start_char, sp.end_char))
        return [dedupe_spans(x) for x in spans]

    def extract(self, text: str) -> list[TypedSpan]:
        return self.extract_batch([text])[0]

    def texts(self, text: str) -> list[str]:
        return list(dict.fromkeys(s.text for s in self.extract(text)))
