import httpx

from ui.api_client import AssistantClient, ChatResult
from ui.logic import format_sources, status_note, validate_input

OK = {
    "answer": "Room B.201",
    "intent": "office",
    "sources": [{"id": "S26#1", "title": "1 Library borrowing"}],
    "degraded": False,
    "escalate": False,
    "path": "deterministic",
    "request_id": "abc123",
}


def client_with(handler) -> AssistantClient:
    return AssistantClient("http://api.test", transport=httpx.MockTransport(handler))


def test_ask_ok():
    r = client_with(lambda req: httpx.Response(200, json=OK)).ask(
        "where is the library", "s1"
    )
    assert r.ok and r.answer == "Room B.201" and r.request_id == "abc123"


def test_ask_backend_down():
    def boom(req):
        raise httpx.ConnectError("refused", request=req)

    r = client_with(boom).ask("hi", "s1")
    assert not r.ok and "backend" in r.error


def test_ask_timeout():
    def timeout(req):
        raise httpx.ReadTimeout("timed out", request=req)

    r = client_with(timeout).ask("hi", "s1")
    assert not r.ok
    assert r.error == "The assistant is taking too long. Please try again."


def test_ask_validation_and_server_errors():
    assert (
        "type a question"
        in client_with(lambda req: httpx.Response(422)).ask("", "s").error
    )
    assert (
        "error 500"
        in client_with(lambda req: httpx.Response(500)).ask("x", "s").error
    )


def test_ask_rate_limited_429():
    r = client_with(lambda req: httpx.Response(429)).ask("hello", "s1")
    assert not r.ok
    assert r.error == "Too many questions in a short time. Please wait a minute."


def test_ask_degraded_response():
    payload = {
        **OK,
        "degraded": True,
        "path": "document_fallback",
    }
    r = client_with(lambda req: httpx.Response(200, json=payload)).ask(
        "where is the library", "s1"
    )
    assert r.ok
    assert r.degraded is True
    assert r.path == "document_fallback"


def test_feedback():
    assert client_with(lambda req: httpx.Response(201, json={})).send_feedback(
        "abc123", 1
    )


def test_feedback_rejected():
    assert not client_with(lambda req: httpx.Response(500)).send_feedback(
        "abc123", -1
    )


def test_health_status():
    assert client_with(lambda req: httpx.Response(200)).healthy()
    assert not client_with(lambda req: httpx.Response(503)).healthy()


def test_health_backend_down():
    def boom(req):
        raise httpx.ConnectError("refused", request=req)

    assert not client_with(boom).healthy()


def test_validate_input():
    assert validate_input("   ") == "Please type a question."
    assert validate_input("x" * 2001).startswith("Your question is too long")
    assert validate_input("hello") is None


def test_format_sources():
    assert format_sources([]) == ""
    assert format_sources(OK["sources"]) == "Sources: S26#1 — 1 Library borrowing"


def test_status_note():
    assert "Training Office" in status_note(ChatResult(ok=True, escalate=True))
    assert status_note(ChatResult(ok=True)) is None
