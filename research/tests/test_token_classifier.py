"""Fine-tuning code tested with a tiny randomly initialised BERT. No downloads."""

from pathlib import Path

import pytest
import torch

from research.data.skillspan import load_split
from research.extraction.token_classifier import (
    IGNORE, TAG2ID, MultiLayerTagger, TokenClassifierExtractor, encode_batch, predict_tags, spans_to_bio,
)
from research.extraction.train_tagger import TrainConfig, evaluate_tagger, train_tagger

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture()
def tiny(tmp_path):
    from transformers import BertConfig, BertModel, BertTokenizerFast

    sents = load_split(FIX / "skillspan_tiny.json")
    words = sorted(({w for s in sents for w in s.tokens} | {"Strong"}) - {"Python"})  # force Py ##thon
    vocab = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "Py", "##thon"] + words
    vocab = {w: i for i, w in enumerate(dict.fromkeys(vocab))}
    # transformers 5.x: pass the vocab dict; vocab_file= is silently ignored
    tok = BertTokenizerFast(vocab=vocab, do_lower_case=False)
    torch.manual_seed(0)
    cfg = BertConfig(vocab_size=len(vocab), hidden_size=32, num_hidden_layers=1,
                     num_attention_heads=2, intermediate_size=64, max_position_embeddings=64)
    return MultiLayerTagger(BertModel(cfg), dropout=0.0), tok, sents


def test_spans_to_bio_roundtrip():
    from research.data.skillspan import bio_to_spans

    assert spans_to_bio(5, [(0, 2), (3, 4)]) == ["B", "I", "O", "B", "O"]
    assert bio_to_spans(spans_to_bio(5, [(0, 2), (3, 4)])) == [(0, 2), (3, 4)]


def test_labels_only_on_first_subtoken(tiny):
    _, tok, _ = tiny
    tokens = ["Python", "and", "Python"]  # "Python" -> Py ##thon (2 sub-tokens)
    batch, word_ids, n_trunc = encode_batch(tok, [tokens], {"skill": [["B", "O", "B"]]})
    lab = batch["labels"]["skill"][0].tolist()
    ids = word_ids[0]
    assert n_trunc == 0
    for j, w in enumerate(ids):
        if w is None or (j > 0 and ids[j - 1] == w):
            assert lab[j] == IGNORE
    firsts = [lab[j] for j, w in enumerate(ids) if w is not None and (j == 0 or ids[j - 1] != w)]
    assert firsts == [TAG2ID["B"], TAG2ID["O"], TAG2ID["B"]]


def test_truncation_counted_and_tagged_O(tiny):
    model, tok, _ = tiny
    preds, n_trunc = predict_tags(model, tok, [["Python"] * 40], max_length=16)
    assert n_trunc == 1
    assert len(preds[0]["skill"]) == 40
    assert all(t == "O" for t in preds[0]["skill"][7:])  # 14 content slots = 7 two-piece words


def test_training_overfits_tiny_fixture(tiny, tmp_path):
    model, tok, sents = tiny
    cfg = TrainConfig(lr=5e-3, batch_size=3, max_epochs=60, patience=60, warmup_ratio=0.0,
                      seed=0, log_every=0, max_length=32)
    model, hist = train_tagger(model, tok, sents, sents, cfg, log=lambda *_: None)
    assert hist[-1]["train_loss"] < hist[0]["train_loss"]
    assert evaluate_tagger(model, tok, sents, cfg)["exact_f1"] == 1.0

    # save -> load through the Extractor wrapper gives the same spans
    model.save(tmp_path / "m", tok)
    ex = TokenClassifierExtractor(tmp_path / "m")
    spans = ex.extract_tokens(list(sents[0].tokens))
    assert {(s.start, s.end, s.label) for s in spans} == {(0, 2, "skill"), (4, 5, "knowledge")}
    assert all(s.source == "model" for s in spans)
    raw = ex.extract("Manage budgets and use Python .")
    assert {s.text for s in raw} == {"Manage budgets", "Python"}
    assert raw[0].start_char == 0


def test_tiny_tokenizer_has_real_vocab(tiny):
    _, tok, _ = tiny
    assert tok.tokenize("Python") == ["Py", "##thon"]
    assert "[UNK]" not in tok.tokenize("Manage budgets and use")
