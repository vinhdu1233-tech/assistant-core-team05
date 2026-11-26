from pathlib import Path
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from ui.api_client import AssistantClient

APP_PATH = Path(__file__).resolve().parents[1] / "ui" / "app.py"
REQUEST_ID = "feedback-test-123"
WARNING = "Could not save your feedback. Please try again."


@pytest.fixture
def feedback_app(monkeypatch):
    monkeypatch.setattr(AssistantClient, "healthy", lambda self: True)

    send_feedback = Mock(return_value=True)
    monkeypatch.setattr(AssistantClient, "send_feedback", send_feedback)

    app = AppTest.from_file(str(APP_PATH))

    app.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "The library is in Room B.201.",
            "request_id": REQUEST_ID,
        }
    ]
    app.session_state["rated"] = set()

    app.run()
    assert not app.exception

    return app, send_feedback


@pytest.mark.parametrize(
    ("button_key", "rating"),
    [("up0", 1), ("down0", -1)],
)
def test_feedback_success(feedback_app, button_key, rating):
    app, send_feedback = feedback_app

    app.button(key=button_key).click().run()

    assert not app.exception
    send_feedback.assert_called_once_with(REQUEST_ID, rating)
    assert REQUEST_ID in app.session_state["rated"]
    assert not app.warning

    app.run()

    assert not app.exception
    send_feedback.assert_called_once_with(REQUEST_ID, rating)

    keys = [button.key for button in app.button]
    assert "up0" not in keys
    assert "down0" not in keys
    expected = "Thanks for your feedback!" if rating == 1 else "Thanks — we will look at this answer."
    assert any(message.value == expected for message in app.success)


@pytest.mark.parametrize(
    ("button_key", "rating"),
    [("up0", 1), ("down0", -1)],
)
def test_feedback_failure(feedback_app, button_key, rating):
    app, send_feedback = feedback_app
    send_feedback.return_value = False

    app.button(key=button_key).click().run()

    assert not app.exception
    send_feedback.assert_called_once_with(REQUEST_ID, rating)
    assert REQUEST_ID not in app.session_state["rated"]
    assert any(w.value == WARNING for w in app.warning)

    keys = [button.key for button in app.button]
    assert "up0" in keys
    assert "down0" in keys
    assert not app.success


@pytest.mark.parametrize(
    ("button_key", "rating"),
    [("up0", 1), ("down0", -1)],
)
def test_feedback_retry_after_failure(feedback_app, button_key, rating):
    app, send_feedback = feedback_app
    send_feedback.side_effect = [False, True]

    app.button(key=button_key).click().run()

    assert not app.exception
    assert REQUEST_ID not in app.session_state["rated"]
    assert any(w.value == WARNING for w in app.warning)

    app.button(key=button_key).click().run()

    assert not app.exception
    assert REQUEST_ID in app.session_state["rated"]
    assert send_feedback.call_count == 2
    assert all(call.args == (REQUEST_ID, rating) for call in send_feedback.call_args_list)

    app.run()

    assert not app.exception
    assert send_feedback.call_count == 2

    keys = [button.key for button in app.button]
    assert "up0" not in keys
    assert "down0" not in keys
    expected = "Thanks for your feedback!" if rating == 1 else "Thanks — we will look at this answer."
    assert any(message.value == expected for message in app.success)
