"""Member 5 Lab 07 D.4 UI scenario tests.

These tests exercise the Streamlit page with a deterministic mocked API client.
HTTP contract behavior is covered separately by Member 1's API-client tests.
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
    feedback = Mock(return_value=True)

    monkeypatch.setattr(AssistantClient, "healthy", healthy)
    monkeypatch.setattr(AssistantClient, "ask", ask)
    monkeypatch.setattr(AssistantClient, "send_feedback", feedback)

    app = AppTest.from_file(str(APP_PATH)).run()
    assert not app.exception
    return app, ask, healthy, feedback


def test_sidebar_example_submits_selected_question(ui_app):
    app, ask, _, _ = ui_app

    example = "Can I register my thesis with 118 credits?"
    app.button[0].click().run()

    assert not app.exception
    ask.assert_called_once_with(example, app.session_state["session_id"])
    assert any(message.value == example for message in app.markdown)


def test_thesis_answer_renders_sources(ui_app):
    app, ask, _, _ = ui_app
    ask.return_value = ChatResult(
        ok=True,
        answer="You may register your thesis after meeting the credit requirement.",
        intent="rule",
        sources=[
            {"id": "H26#5.3", "title": "Thesis registration"},
            {"id": "H26#5.4", "title": "Graduation requirements"},
        ],
        request_id="thesis-request",
    )

    app.chat_input[0].set_value("Can I register my thesis with 118 credits?").run()

    assert not app.exception
    assert any("thesis" in item.value.lower() for item in app.markdown)
    captions = [item.value for item in app.caption]
    assert any("H26#5.3" in value and "H26#5.4" in value for value in captions)


def test_out_of_domain_answer_shows_escalation_note(ui_app):
    app, ask, _, _ = ui_app
    ask.return_value = ChatResult(
        ok=True,
        answer="I cannot answer that question from the handbook.",
        escalate=True,
        request_id="escalation-request",
    )

    app.chat_input[0].set_value("Recommend a career based on my personality").run()

    assert not app.exception
    assert any(
        "Training Office, room I.101" in item.value for item in app.info
    )


def test_blank_question_shows_validation_without_api_call(ui_app):
    app, ask, _, _ = ui_app

    app.chat_input[0].set_value("   ").run()

    assert not app.exception
    ask.assert_not_called()
    assert any("Please type a question." in item.value for item in app.warning)


def test_feedback_buttons_submit_positive_and_negative_ratings(ui_app):
    app, ask, _, feedback = ui_app

    app.chat_input[0].set_value("Where is the library?").run()
    assert not app.exception

    app.button(key="up1").click().run()
    assert not app.exception
    feedback.assert_called_once_with("m5-request-1", 1)


def test_backend_stopped_shows_health_and_chat_errors(ui_app):
    app, ask, healthy, _ = ui_app
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
    assert any(
        "Cannot reach the assistant" in item.value for item in app.markdown
    )


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
def test_special_response_states_render_friendly_notes(ui_app, result, expected_note):
    app, ask, _, _ = ui_app
    ask.return_value = result

    app.chat_input[0].set_value("Please help with this question").run()

    assert not app.exception
    assert any(expected_note in item.value for item in app.info)
