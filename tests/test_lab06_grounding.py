import json

import pytest

from assistant_core.errors import ProviderError
from assistant_core.llm import parse_draft


def test_valid_citation_is_accepted():
    raw = json.dumps(
        {
            "answer": "The thesis requires 120 credits.",
            "source_ids": ["H26#5.3"],
            "confidence": 0.9,
            "abstain": False,
        }
    )

    draft = parse_draft(raw, {"H26#5.3"})

    assert draft.source_ids == ["H26#5.3"]
    assert draft.abstain is False


def test_invented_citation_is_rejected():
    raw = json.dumps(
        {
            "answer": "Unsupported answer.",
            "source_ids": ["H26#9.9"],
            "confidence": 0.9,
            "abstain": False,
        }
    )

    with pytest.raises(ProviderError):
        parse_draft(raw, {"H26#5.3"})


def test_empty_citations_are_rejected_for_non_abstaining_answer():
    raw = json.dumps(
        {
            "answer": "Unsupported answer.",
            "source_ids": [],
            "confidence": 0.9,
            "abstain": False,
        }
    )

    with pytest.raises(ProviderError):
        parse_draft(raw, {"H26#5.3"})


def test_abstaining_answer_without_citations_is_accepted():
    raw = json.dumps(
        {
            "answer": "",
            "source_ids": [],
            "confidence": 0.0,
            "abstain": True,
        }
    )

    draft = parse_draft(raw, {"H26#5.3"})

    assert draft.abstain is True
    assert draft.source_ids == []


def test_malformed_json_is_rejected():
    with pytest.raises(ProviderError):
        parse_draft("This is not JSON", {"H26#5.3"})


def test_invalid_confidence_is_rejected():
    raw = json.dumps(
        {
            "answer": "Some answer.",
            "source_ids": ["H26#5.3"],
            "confidence": 1.5,
            "abstain": False,
        }
    )

    with pytest.raises(ProviderError):
        parse_draft(raw, {"H26#5.3"})
