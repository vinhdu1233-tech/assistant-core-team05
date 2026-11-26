"""Member 5 Lab 07 Part E regression tests for Streamlit UI states.

The tests isolate the Streamlit page with a deterministic AssistantClient.
HTTP contract and feedback-submission behavior are covered by M1 and M3.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from ui.api_client import AssistantClient, ChatResult

APP_PATH = Path(__file__).resolve().parents[1] / "ui" / "app.py"


@pytest.fixture
def ui_app(monkeypatch):
    healthy = Mock(return_value=True)
    ask = Mock(
        return_value=ChatResult(
            ok=True,
            answer="The library is in Room B.201.",
            intent="office",
            sources=[{"id": "S26#1", "title": "Library borrowing"}],
            request_id="m5-request-1",
        )
    )

    monkeypatch.setattr(AssistantClient, "healthy", healthy)
    monkeypatch.setattr(AssistantClient, "ask", ask)

    app = AppTest.from_file(str(APP_PATH)).run()
    assert not app.exception
    return app, ask, healthy


def test_sidebar_example_submits_selected_question(ui_app):
    app, ask, _ = ui_app

    example = "Can I register my thesis with 118 credits?"
    app.button[0].click().run()

    assert not app.exception
    ask.assert_called_once_with(example, app.session_state["session_id"])
    assert any(message.value == example for message in app.markdown)


def test_thesis_answer_renders_answer_and_multiple_sources(ui_app):
    app, ask, _ = ui_app
    expected_answer = "You may register your thesis after meeting the credit requirement."
    ask.return_value = ChatResult(
        ok=True,
        answer=expected_answer,
        intent="rule",
        sources=[
            {"id": "H26#5.3", "title": "Thesis registration"},
            {"id": "H26#5.4", "title": "Graduation requirements"},
        ],
        request_id="thesis-request",
    )

    app.chat_input[0].set_value("Can I register my thesis with 118 credits?").run()

    assert not app.exception
    assert any(expected_answer in item.value for item in app.markdown)
    captions = [item.value for item in app.caption]
    assert any("H26#5.3" in value and "H26#5.4" in value for value in captions)


def test_out_of_domain_answer_shows_escalation_note(ui_app):
    app, ask, _ = ui_app
    ask.return_value = ChatResult(
        ok=True,
        answer="I cannot answer that question from the handbook.",
        escalate=True,
        request_id="escalation-request",
    )

    app.chat_input[0].set_value("Recommend a career based on my personality").run()

    assert not app.exception
    assert any("Training Office, room I.101" in item.value for item in app.info)


@pytest.mark.parametrize(
    ("question", "expected_warning"),
    [
        ("   ", "Please type a question."),
        ("x" * 2001, "Your question is too long"),
    ],
)
def test_invalid_question_is_rejected_before_api_call(ui_app, question, expected_warning):
    app, ask, _ = ui_app

    app.chat_input[0].set_value(question).run()

    assert not app.exception
    ask.assert_not_called()
    assert any(expected_warning in item.value for item in app.warning)


def test_backend_stopped_shows_health_and_chat_errors(ui_app):
    app, ask, healthy = ui_app
    healthy.return_value = False
    ask.return_value = ChatResult(
        ok=False,
        error="Cannot reach the assistant. Is the backend running?",
    )

    app = AppTest.from_file(str(APP_PATH)).run()
    assert not app.exception
    assert any("backend is not reachable" in item.value.lower() for item in app.error)

    app.chat_input[0].set_value("Where is the library?").run()

    assert not app.exception
    assert any("Cannot reach the assistant" in item.value for item in app.markdown)


def test_rate_limit_error_is_displayed_without_traceback(ui_app):
    app, ask, _ = ui_app
    ask.return_value = ChatResult(
        ok=False,
        error="Too many questions in a short time. Please wait a minute.",
    )

    app.chat_input[0].set_value("Where is the library?").run()

    assert not app.exception
    assert any("Please wait a minute" in item.value for item in app.markdown)


@pytest.mark.parametrize(
    ("result", "expected_note"),
    [
        (
            ChatResult(
                ok=True,
                answer="The source document provides this information.",
                degraded=True,
                request_id="degraded-request",
            ),
            "Shown directly from the source document",
        ),
        (
            ChatResult(
                ok=True,
                answer="I could not find this in the official documents.",
                escalate=True,
                degraded=True,
                request_id="escalated-degraded-request",
            ),
            "Training Office, room I.101",
        ),
    ],
)
def test_degraded_and_escalated_response_states_render_notes(ui_app, result, expected_note):
    app, ask, _ = ui_app
    ask.return_value = result

    app.chat_input[0].set_value("Please help with this question").run()

    assert not app.exception
    assert any(expected_note in item.value for item in app.info)
