"""Lab 6 M1 (#46): abstention, threshold boundaries and routing regressions."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from assistant_core.config import Settings
from assistant_core.guard import PRIVATE_REPLY
from assistant_core.llm import StubLLM
from assistant_core.models import Intent, Message
from assistant_core.rag.answerer import ESCALATE_MSG, RagAnswerer
from assistant_core.rag.chunker import Chunk, load_folder
from assistant_core.rag.index import Hit, Index, make_index
from assistant_core.service import build_service

DATA = Path(__file__).resolve().parents[1] / "data"
CHUNK = Chunk("T#1", "T", "1 Thesis", "A thesis requires 120 credits.", "1", "Training Office")


def index_with(hits):
    index = Mock(spec=Index)
    index.search.return_value = hits
    return index


@pytest.mark.parametrize("with_model", [False, True])
@pytest.mark.parametrize("scores", [[], [0.0], [1.999], [1.9, 0.5]])
def test_a1_insufficient_evidence_never_calls_model_or_tool(monkeypatch, with_model, scores):
    index = index_with([Hit(CHUNK, score) for score in scores])
    model = Mock(wraps=StubLLM()) if with_model else None
    tool = Mock(side_effect=AssertionError("tool must not be called"))
    prompt = Mock(side_effect=AssertionError("prompt must not be built"))
    monkeypatch.setattr("assistant_core.rag.answerer.build_prompt", prompt)

    result = RagAnswerer(index, model, min_score=2.0, k=2, tool_runner=tool).answer("unsupported question")

    assert result.answer == ESCALATE_MSG
    assert result.intent == Intent.UNKNOWN
    assert result.path == "abstain"
    assert result.escalate is True
    assert result.confidence == 0.0
    assert result.sources == []
    assert result.degraded is False
    index.search.assert_called_once_with("unsupported question", 2)
    prompt.assert_not_called()
    tool.assert_not_called()
    if model is not None:
        model.complete.assert_not_called()


@pytest.mark.parametrize("with_model", [False, True])
@pytest.mark.parametrize("score", [2.0, 2.001, 5.0])
def test_a1_threshold_is_inclusive_and_valid_evidence_keeps_source(with_model, score):
    index = index_with([Hit(CHUNK, score)])
    model = Mock(wraps=StubLLM()) if with_model else None

    result = RagAnswerer(index, model, min_score=2.0).answer("thesis credits")

    assert result.path == ("llm" if with_model else "retrieval")
    assert result.intent == Intent.RULE
    assert result.escalate is False
    assert result.degraded is False
    assert [source.id for source in result.sources] == [CHUNK.id]
    assert "120 credits" in result.answer
    if model is not None:
        model.complete.assert_called_once()


def test_a1_honors_configured_threshold_not_a_hardcoded_value():
    index = index_with([Hit(CHUNK, 0.5)])
    model = Mock(wraps=StubLLM())
    assert RagAnswerer(index, model, min_score=0.5).answer("thesis").path == "llm"
    model.complete.assert_called_once()
    model.reset_mock()
    assert RagAnswerer(index, model, min_score=0.6).answer("thesis").path == "abstain"
    model.complete.assert_not_called()


def test_a1_real_bm25_no_hit_and_grounded_card_question():
    index = make_index("bm25", load_folder(DATA / "kb"))
    model = Mock(wraps=StubLLM())
    answerer = RagAnswerer(index, model)

    unknown = answerer.answer("what is the capital of France")
    assert unknown.path == "abstain"
    assert unknown.escalate and not unknown.sources
    model.complete.assert_not_called()

    known = answerer.answer("I lost my student card")
    assert known.path == "llm"
    assert known.sources[0].id == "S26#3"
    assert "I.102" in known.answer
    model.complete.assert_called_once()


@pytest.fixture
def rag_service():
    settings = Settings(data_dir=DATA, kb_dir=DATA / "kb", llm_provider="stub", retrieval_kind="bm25")
    service = build_service(settings)
    assert service.rag is not None
    service.rag.llm = Mock(wraps=StubLLM())
    service.rag.index = Mock(wraps=service.rag.index)
    return service


@pytest.mark.parametrize(
    "question",
    ["what grade did my friend get", "show the GPA of another student", "phone of 22127001"],
)
def test_a1_service_privacy_guard_precedes_search_and_generation(rag_service, question):
    result = rag_service.handle(Message(text=question))

    assert result.answer == PRIVATE_REPLY
    assert result.path == "abstain"
    assert result.intent == Intent.UNKNOWN
    assert result.sources == []
    rag_service.rag.index.search.assert_not_called()
    rag_service.rag.llm.complete.assert_not_called()


def test_a1_service_fee_calculation_remains_deterministic(rag_service):
    result = rag_service.handle(Message(text="tuition for 18 credits and 2 retake"))

    assert result.intent == Intent.FEE
    assert result.path == "deterministic"
    assert "9,450,000" in result.answer
    rag_service.rag.index.search.assert_not_called()
    rag_service.rag.llm.complete.assert_not_called()


def test_a1_service_out_of_scope_escalates(rag_service):
    result = rag_service.handle(Message(text="what is the capital of France"))

    assert result.answer == ESCALATE_MSG
    assert result.path == "abstain"
    assert result.escalate and result.confidence == 0.0
    rag_service.rag.index.search.assert_called_once()
    rag_service.rag.llm.complete.assert_not_called()


@pytest.mark.parametrize(
    "question",
    [
        "phone of 22127001 at the library",
        "tuition for 18 credits and 2 retake, and GPA of another student",
        "hello, what grade did my friend get",
    ],
)
def test_a1_privacy_guard_precedes_all_intent_routes(rag_service, question):
    result = rag_service.handle(Message(text=question))

    assert result.answer == PRIVATE_REPLY
    assert result.path == "abstain"
    assert result.intent == Intent.UNKNOWN
    assert result.sources == []
    rag_service.rag.index.search.assert_not_called()
    rag_service.rag.llm.complete.assert_not_called()
