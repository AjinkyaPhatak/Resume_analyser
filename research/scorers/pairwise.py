"""Pairwise scorers: a cross-encoder (accuracy ceiling) and an optional LLM judge.

Both cache every (resume, jd) score on disk (common/pair_cache.py), so reruns and
unchanged counterfactuals cost nothing.
"""

from __future__ import annotations

import math
import re

from research.common.pair_cache import PairScoreCache, pair_key

from .base import BaseScorer


class _CachedPairScorer(BaseScorer):
    namespace: str

    def _compute(self, pairs: list[tuple[str, str]]) -> list[float]:
        raise NotImplementedError

    def score_batch(self, pairs: list[tuple[str, str]]) -> list[float]:
        if not pairs:
            return []
        hits = self.cache.get_many(pairs)
        todo = list(dict.fromkeys(p for p in pairs if pair_key(*p) not in hits))
        if todo:
            scores = self._compute(todo)
            self.cache.put_many(dict(zip(todo, scores)))
            hits.update({pair_key(*p): s for p, s in zip(todo, scores)})
        # SQLite stores NaN as NULL; map it back to NaN
        return [math.nan if hits[pair_key(*p)] is None else float(hits[pair_key(*p)]) for p in pairs]

    def score(self, resume: str, jd: str) -> float:
        return self.score_batch([(resume, jd)])[0]


class CrossEncoderScorer(_CachedPairScorer):
    """MS MARCO cross-encoder; input is (query=JD, passage=resume), output the raw logit.

    The pair is cut to ``max_length`` tokens; sentence-transformers truncates the
    longer side first, which is the JD, so the (short) bio is normally kept whole.
    """

    def __init__(self, model_name: str, revision: str | None = None, device: str = "cpu",
                 max_length: int = 512, batch_size: int = 32, name: str = "cross_encoder"):
        self.name = name
        self.model_name, self.revision, self.device = model_name, revision, device
        self.max_length, self.batch_size = max_length, batch_size
        self.cache = PairScoreCache(f"ce|{model_name}|rev={revision}|maxlen={max_length}")
        self._model = None

    def _compute(self, pairs):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, revision=self.revision, device=self.device,
                                       max_length=self.max_length)
        preds = self._model.predict([(j, r) for r, j in pairs], batch_size=self.batch_size,
                                    show_progress_bar=False, convert_to_numpy=True)
        return [float(x) for x in preds]


DEFAULT_PROMPT = (
    "You are screening candidates for a job.\n\n"
    "JOB DESCRIPTION:\n{jd}\n\n"
    "CANDIDATE PROFILE:\n{resume}\n\n"
    "On a scale from 0 to 100, how well does the candidate fit this job? "
    "Answer with a single integer only.\nScore:"
)

_SCORE_PATTERNS = (
    re.compile(r"(?i)\bscore\s*[:=]?\s*(\d{1,3}(?:\.\d+)?)"),
    re.compile(r"(\d{1,3}(?:\.\d+)?)\s*(?:/\s*100|out of 100)"),
    re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)(?![\d.])"),
)


def parse_score(text: str) -> float:
    """First plausible 0-100 number in an LLM answer, preferring 'Score: N' and 'N/100'.

    Returns NaN when nothing in range is found; callers count and report NaNs.
    """
    for pat in _SCORE_PATTERNS:
        for m in pat.finditer(text or ""):
            v = float(m.group(1))
            if 0 <= v <= 100:
                return v
    return math.nan


class LLMJudgeScorer(_CachedPairScorer):
    """Open-weights instruction model asked for a 0-100 fit score (greedy decoding).

    Off by default (slow). Unparseable answers become NaN and are counted in
    ``n_unparsed``; NaNs are kept in the cache so they aren't silently retried.
    """

    def __init__(self, model_name: str, revision: str | None = None, device: str = "cpu",
                 prompt: str = DEFAULT_PROMPT, max_new_tokens: int = 8, max_input_tokens: int = 1536,
                 batch_size: int = 4, name: str = "llm_judge"):
        self.name = name
        self.model_name, self.revision, self.device = model_name, revision, device
        self.prompt, self.max_new_tokens, self.max_input_tokens = prompt, max_new_tokens, max_input_tokens
        self.batch_size = batch_size
        import hashlib

        ph = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8]
        self.cache = PairScoreCache(f"llm|{model_name}|rev={revision}|prompt={ph}|maxin={max_input_tokens}")
        self._model = self._tok = None
        self.n_unparsed = 0

    def _load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tok = AutoTokenizer.from_pretrained(self.model_name, revision=self.revision, padding_side="left")
        dtype = torch.float16 if str(self.device).startswith("cuda") else torch.float32
        self._model = AutoModelForCausalLM.from_pretrained(self.model_name, revision=self.revision,
                                                           dtype=dtype).to(self.device).eval()

    def _messages(self, resume: str, jd: str) -> str:
        # Trim the JD by tokens so the whole prompt fits max_input_tokens.
        ids = self._tok(jd, add_special_tokens=False)["input_ids"]
        budget = max(64, self.max_input_tokens - len(self._tok(resume, add_special_tokens=False)["input_ids"]) - 120)
        jd = self._tok.decode(ids[:budget]) if len(ids) > budget else jd
        msgs = [{"role": "user", "content": self.prompt.format(jd=jd, resume=resume)}]
        return self._tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    def _compute(self, pairs):
        import torch

        if self._model is None:
            self._load()
        out = []
        for b in range(0, len(pairs), self.batch_size):
            chunk = pairs[b : b + self.batch_size]
            enc = self._tok([self._messages(r, j) for r, j in chunk], return_tensors="pt", padding=True).to(self.device)
            with torch.no_grad():
                gen = self._model.generate(**enc, max_new_tokens=self.max_new_tokens, do_sample=False)
            texts = self._tok.batch_decode(gen[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
            for t in texts:
                v = parse_score(t)
                self.n_unparsed += math.isnan(v)
                out.append(v)
        return out
