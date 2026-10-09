"""Disk-backed embedding cache keyed by (model namespace, sha256(text)).

One SQLite file per model namespace under the cache dir. Only cache misses are sent
to the encoder, so reruns over the same texts cost nothing. The namespace includes
the model name plus anything that changes the vectors (normalisation, an optional
user tag such as a max sequence length or prompt), so changing any of these never
returns stale vectors.

The encoder is injectable (``encode_fn``) so tests run without downloading models.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Callable, Sequence

import numpy as np

from .config import RESEARCH_ROOT

DEFAULT_CACHE_DIR = RESEARCH_ROOT / ".cache" / "embeddings"

EncodeFn = Callable[[list[str]], np.ndarray]


def text_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_filename(namespace: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "__", namespace)
    digest = hashlib.sha256(namespace.encode("utf-8")).hexdigest()[:8]
    return f"{slug}.{digest}.sqlite"


class EmbeddingCache:
    """Raw get/put store for one namespace."""

    def __init__(self, namespace: str, cache_dir: str | Path = DEFAULT_CACHE_DIR):
        self.namespace = namespace
        self.path = Path(cache_dir) / _safe_filename(namespace)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS emb (key TEXT PRIMARY KEY, dim INTEGER, vec BLOB)"
        )
        self._conn.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
        self._conn.execute(
            "INSERT OR IGNORE INTO meta (k, v) VALUES ('namespace', ?)", (namespace,)
        )
        self._conn.commit()

    def get_many(self, keys: Sequence[str]) -> dict[str, np.ndarray]:
        found: dict[str, np.ndarray] = {}
        unique = list(dict.fromkeys(keys))
        # SQLite caps bound parameters; query in chunks.
        for i in range(0, len(unique), 500):
            chunk = unique[i : i + 500]
            marks = ",".join("?" * len(chunk))
            rows = self._conn.execute(
                f"SELECT key, dim, vec FROM emb WHERE key IN ({marks})", chunk
            ).fetchall()
            for key, dim, blob in rows:
                found[key] = np.frombuffer(blob, dtype=np.float32, count=dim).copy()
        return found

    def put_many(self, items: dict[str, np.ndarray]) -> None:
        rows = []
        for key, vec in items.items():
            v = np.ascontiguousarray(vec, dtype=np.float32).ravel()
            rows.append((key, int(v.shape[0]), v.tobytes()))
        self._conn.executemany("INSERT OR REPLACE INTO emb (key, dim, vec) VALUES (?, ?, ?)", rows)
        self._conn.commit()

    def __len__(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM emb").fetchone()[0])

    def close(self) -> None:
        self._conn.close()


class CachedEncoder:
    """Sentence-transformers encoder with a transparent disk cache.

    ``encode(texts)`` returns a float32 array of shape (len(texts), dim) in input
    order. Vectors are L2-normalised when ``normalize=True`` (the default), so a dot
    product is cosine similarity.
    """

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
        batch_size: int = 64,
        normalize: bool = True,
        cache_dir: str | Path | None = DEFAULT_CACHE_DIR,
        tag: str = "",
        encode_fn: EncodeFn | None = None,
        revision: str | None = None,
        max_seq_length: int | None = None,
        task: str | None = None,
    ):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.normalize = normalize
        self.revision = revision
        self.max_seq_length = max_seq_length
        self.task = task
        parts = [model_name, f"normalize={normalize}"]
        if revision:
            parts.append(f"rev={revision}")
        if max_seq_length:
            parts.append(f"maxlen={max_seq_length}")
        if task:
            parts.append(f"task={task}")
        if tag:
            parts.append(tag)
        self.namespace = "|".join(parts)
        # cache_dir=None: nothing is written to disk (the web app scores user resumes)
        self.cache = EmbeddingCache(self.namespace, cache_dir) if cache_dir is not None else None
        self._encode_fn = encode_fn
        self._model = None
        self.n_encoded = 0  # texts actually sent to the model (cache misses)

    def _default_encode(self, texts: list[str]) -> np.ndarray:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self.device, revision=self.revision)
            if self.max_seq_length:
                self._model.max_seq_length = self.max_seq_length
        kwargs = {"task": self.task} if self.task else {}
        return self._model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
            **kwargs,
        )

    @property
    def tokenizer(self):
        """The model's tokenizer, loaded without the model weights."""
        if getattr(self, "_tokenizer", None) is None:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, revision=self.revision)
        return self._tokenizer

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        texts = list(texts)
        if not texts:
            raise ValueError("encode() called with no texts")
        keys = [text_key(t) for t in texts]
        hits = self.cache.get_many(keys) if self.cache is not None else {}
        missing: dict[str, str] = {}
        for k, t in zip(keys, texts):
            if k not in hits and k not in missing:
                missing[k] = t
        if missing:
            fn = self._encode_fn or self._default_encode
            vecs = np.asarray(fn(list(missing.values())), dtype=np.float32)
            if self._encode_fn is not None and self.normalize:
                norms = np.linalg.norm(vecs, axis=1, keepdims=True)
                vecs = vecs / np.clip(norms, 1e-12, None)
            new = dict(zip(missing.keys(), vecs))
            if self.cache is not None:
                self.cache.put_many(new)
            hits.update(new)
            self.n_encoded += len(missing)
        return np.stack([hits[k] for k in keys])
