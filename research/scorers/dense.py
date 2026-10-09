"""Full-text bi-encoder scorers: one embedding per document, cosine similarity.

JDs are long (300-700 words) compared with the encoders' windows (MiniLM 256 tokens,
mpnet 384, JobBERT-v2 64). ``long_text`` controls what happens:
  * ``chunk_mean`` (default): split the text into consecutive windows of at most
    ``window_tokens`` tokens (no overlap), embed each window, average the L2-normalised
    window embeddings and renormalise. Every part of the text counts.
  * ``truncate``: the model's own behaviour (only the first ``max_seq_length`` tokens).
Window embeddings are cached per window text, so shared windows are encoded once.

JobBERTScorer = this with TechWolf/JobBERT-v2, its "anchor" (job-title) head and
64-token windows. JobBERT-v2 was trained on job titles <-> skill lists, not documents;
it's used here as the available job-domain encoder, and the paper states that.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .base import BaseScorer


def token_windows(text: str, tokenizer, window_tokens: int) -> list[str]:
    """Split ``text`` into substrings of at most ``window_tokens`` tokenizer tokens."""
    if window_tokens <= 0:
        raise ValueError("window_tokens must be positive")
    enc = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True, verbose=False)
    offs = [o for o in enc["offset_mapping"] if o[1] > o[0]]
    if not offs:
        return [text] if text.strip() else []
    out = []
    for i in range(0, len(offs), window_tokens):
        chunk = offs[i : i + window_tokens]
        piece = text[chunk[0][0] : chunk[-1][1]].strip()
        if piece:
            out.append(piece)
    return out


class FullTextSBERTScorer(BaseScorer):
    def __init__(self, encoder, long_text: str = "chunk_mean", window_tokens: int | None = None,
                 name: str = "sbert"):
        """``encoder``: a CachedEncoder (or anything with ``encode`` and ``tokenizer``)."""
        if long_text not in ("chunk_mean", "truncate"):
            raise ValueError("long_text must be 'chunk_mean' or 'truncate'")
        self.name = name
        self.encoder = encoder
        self.long_text = long_text
        # leave room for [CLS]/[SEP]
        self.window_tokens = window_tokens or ((encoder.max_seq_length or 256) - 2)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        texts = list(texts)
        if self.long_text == "truncate":
            return self.encoder.encode(texts)
        windows = [token_windows(t, self.encoder.tokenizer, self.window_tokens) or [t] for t in texts]
        flat = list(dict.fromkeys(w for ws in windows for w in ws))
        vec = dict(zip(flat, self.encoder.encode(flat)))
        out = np.stack([np.mean([vec[w] for w in ws], axis=0) for ws in windows])
        return out / np.clip(np.linalg.norm(out, axis=1, keepdims=True), 1e-12, None)

    def score_batch(self, pairs: list[tuple[str, str]]) -> list[float]:
        if not pairs:
            return []
        texts = list(dict.fromkeys(t for p in pairs for t in p))
        emb = dict(zip(texts, self.embed(texts)))
        return [float(emb[r] @ emb[j]) for r, j in pairs]

    def score(self, resume: str, jd: str) -> float:
        return self.score_batch([(resume, jd)])[0]
