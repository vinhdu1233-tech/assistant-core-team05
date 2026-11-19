"""Regression tests for mode-aware A1 defaults and homogeneous Hybrid relevance."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from assistant_core.config import Settings, load_settings
from assistant_core.errors import ConfigError
from assistant_core.llm import StubLLM
from assistant_core.models import Message
from assistant_core.rag.answerer import RagAnswerer
from assistant_core.rag.chunker import Chunk, load_folder
from assistant_core.rag.index import Hit, Index, make_index
from assistant_core.service import build_service

DATA = Path(__file__).resolve().parents[1] / "data"
MODES = [("bm25", 2.0), ("tfidf", 0.25), ("hybrid", 0.25)]


@pytest.mark.parametrize(("kind", "expected"), MODES)
@pytest.mark.parametrize("explicit_blank", [False, True])
def test_environment_defaults(monkeypatch, kind, expected, explicit_blank):
    monkeypatch.setenv("RETRIEVAL_KIND", kind)
    monkeypatch.delenv("RETRIEVAL_MIN_SCORE", raising=False)
    if explicit_blank:
        monkeypatch.setenv("RETRIEVAL_MIN_SCORE", "")
    assert load_settings(env_file=None).retrieval_min_score == expected
    assert Settings(retrieval_kind=kind).retrieval_min_score == expected


@pytest.mark.parametrize(("kind", "expected"), MODES)
def test_explicit_threshold_override(monkeypatch, kind, expected):
    override = expected / 2
    monkeypatch.setenv("RETRIEVAL_KIND", kind)
    monkeypatch.setenv("RETRIEVAL_MIN_SCORE", str(override))
    assert load_settings(env_file=None).retrieval_min_score == override
    assert Settings(retrieval_kind=kind, retrieval_min_score=override).retrieval_min_score == override


@pytest.mark.parametrize("kind", ["tfidf", "hybrid"])
@pytest.mark.parametrize("bad", ["2.0", "-1", "nan", "inf", "not-a-number"])
def test_invalid_cosine_threshold_rejected(monkeypatch, kind, bad):
    monkeypatch.setenv("RETRIEVAL_KIND", kind)
    monkeypatch.setenv("RETRIEVAL_MIN_SCORE", bad)
    with pytest.raises(ConfigError):
        load_settings(env_file=None)


@pytest.mark.parametrize("bad", [-1, float("nan"), float("inf")])
def test_invalid_direct_bm25_threshold_rejected(bad):
    with pytest.raises(ValidationError):
        Settings(retrieval_min_score=bad)
    with pytest.raises(ValueError):
        RagAnswerer(make_index("bm25", []), None, min_score=bad)


@pytest.mark.parametrize("kind", ["tfidf", "hybrid"])
def test_direct_cosine_threshold_above_one_rejected(kind):
    with pytest.raises(ValidationError):
        Settings(retrieval_kind=kind, retrieval_min_score=2.0)
    with pytest.raises(ValueError):
        RagAnswerer(make_index(kind, []), None, min_score=2.0)


@pytest.mark.parametrize(("kind", "expected"), MODES)
@pytest.mark.parametrize("provider", ["stub", "template"])
def test_real_service_defaults_allow_evidence_and_abstain_without_it(kind, expected, provider):
    settings = Settings(data_dir=DATA, kb_dir=DATA / "kb", retrieval_kind=kind, llm_provider=provider)
    service = build_service(settings)
    assert service.rag is not None
    assert service.rag.min_score == expected
    if provider == "stub":
        service.rag.llm = Mock(wraps=StubLLM())

    unknown = service.handle(Message(text="what is the capital of France"))
    assert unknown.path == "abstain" and unknown.escalate and unknown.confidence == 0.0
    assert not unknown.sources
    if provider == "stub":
        service.rag.llm.complete.assert_not_called()

    known = service.handle(Message(text="can I register my thesis with 118 credits"))
    assert known.path == ("llm" if provider == "stub" else "retrieval")
    assert known.sources[0].id == "H26#5.3"
    assert "120" in known.answer
    if provider == "stub":
        service.rag.llm.complete.assert_called_once()


@pytest.mark.parametrize(("kind", "expected"), MODES)
def test_direct_default_threshold_and_real_weak_match(kind, expected):
    chunk = Chunk("T#1", "T", "1 Rules", "thesis credits", "1", "Training Office")
    index = make_index(kind, [chunk])
    model = Mock(wraps=StubLLM())
    answerer = RagAnswerer(index, model)
    assert answerer.min_score == expected
    hits = index.search("thesis", 3)
    assert hits
    # Set the explicit threshold slightly above the real matched score (still in range).
    threshold = hits[0].score + 0.01
    result = RagAnswerer(index, model, min_score=threshold).answer("thesis")
    assert result.path == "abstain" and result.escalate and not result.sources
    model.complete.assert_not_called()


def test_hybrid_uses_cosine_for_every_returned_hit():
    chunks = load_folder(DATA / "kb")
    hybrid = make_index("hybrid", chunks)
    tfidf = make_index("tfidf", chunks)
    for question in ("thesis credits", "late registration", "library books", "student card"):
        hits = hybrid.search(question, len(chunks))
        scores = {hit.chunk.id: hit.score for hit in tfidf.search(question, len(chunks))}
        assert hits
        for hit in hits:
            assert 0.0 <= hit.score <= 1.0
            assert hit.score == scores[hit.chunk.id]


@pytest.mark.parametrize("score", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_retrieval_evidence_abstains_before_model(score):
    chunk = Chunk("T#1", "T", "1 Rules", "thesis credits", "1", "Training Office")
    index = Mock(spec=Index)
    index.search.return_value = [Hit(chunk, score)]
    model = Mock(wraps=StubLLM())
    result = RagAnswerer(index, model).answer("thesis")
    assert result.path == "abstain" and result.escalate and result.confidence == 0.0
    assert not result.sources
    model.complete.assert_not_called()


@pytest.mark.parametrize(
    ("question", "source", "score"),
    [
        ("can I register my thesis with 118 credits", "H26#5.3", 4.914),
        ("How can I reset my IT account password?", "S26#2", 10.311),
        ("How long may I borrow library books?", "S26#1", 8.719),
        ("What happens if I register my thesis late?", "H26#5.4", 4.899),
    ],
)
def test_bm25_preserves_m2_recorded_retrieval_results(question, source, score):
    chunks = load_folder(DATA / "kb")
    assert len(chunks) == 14
    hit = make_index("bm25", chunks).search(question)[0]
    assert hit.chunk.id == source
    assert hit.score == pytest.approx(score, abs=0.001)
