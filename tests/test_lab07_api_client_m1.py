"""Lab 07 M1 (Issue #57): HTTP client contracts and failure handling."""

import json
import sqlite3
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from assistant_api.main import create_app
from assistant_core.config import Settings
from ui.api_client import AssistantClient

DATA = Path(__file__).resolve().parents[1] / "data"
VALID_CHAT = {
    "answer": "Students need 120 credits.",
    "intent": "rule",
    "sources": [{"id": "H26#5.3", "title": "5.3 Thesis registration"}],
    "path": "llm",
    "escalate": False,
    "degraded": False,
    "request_id": "request-123",
}


def client_with(handler):
    return AssistantClient("http://api.test", timeout_s=0.2, transport=httpx.MockTransport(handler))


def test_http_request_path_method_payload_and_response_preservation():
    seen = []

    def handler(req):
        seen.append(req)
        return httpx.Response(200, json=VALID_CHAT)

    with client_with(handler) as client:
        result = client.ask("Thesis credits?", "random-tab-session")
        assert client._http.is_closed is False
    assert client._http.is_closed is True
    assert len(seen) == 1
    assert seen[0].method == "POST"
    assert seen[0].url.path == "/v1/chat"
    assert json.loads(seen[0].content) == {
        "message": "Thesis credits?",
        "session_id": "random-tab-session",
    }
    assert result.ok is True
    assert result.answer == VALID_CHAT["answer"]
    assert result.intent == "rule"
    assert result.sources == VALID_CHAT["sources"]
    assert result.path == "llm"
    assert result.request_id == "request-123"
    assert not result.escalate and not result.degraded
    assert result.error == ""


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (httpx.ConnectError, "backend"),
        (httpx.ReadError, "backend"),
        (httpx.RemoteProtocolError, "backend"),
        (httpx.ConnectTimeout, "taking too long"),
        (httpx.ReadTimeout, "taking too long"),
        (httpx.WriteTimeout, "taking too long"),
        (httpx.PoolTimeout, "taking too long"),
    ],
)
def test_ask_network_failure_is_human_readable(exception, expected):
    def handler(req):
        raise exception("private network failure", request=req)

    result = client_with(handler).ask("question", "session")
    assert not result.ok and expected in result.error
    assert "private network failure" not in result.error
    assert result.request_id == ""


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (400, "error 400"),
        (401, "error 401"),
        (404, "error 404"),
        (408, "error 408"),
        (422, "type a question"),
        (429, "wait a minute"),
        (500, "error 500"),
        (502, "error 502"),
        (503, "error 503"),
        (504, "error 504"),
    ],
)
def test_ask_http_failures_show_friendly_errors(status_code, expected):
    result = client_with(lambda req: httpx.Response(status_code)).ask("question", "s1")
    assert not result.ok
    assert expected in result.error
    assert result.answer == "" and result.request_id == ""


@pytest.mark.parametrize(
    "payload",
    [
        [],
        None,
        "not-an-object",
        {},
        {"answer": "hi", "intent": "rule"},
        {"answer": "hi", "request_id": "r1"},
        {**VALID_CHAT, "request_id": ""},
        {**VALID_CHAT, "answer": None},
        {**VALID_CHAT, "sources": "invalid"},
        {**VALID_CHAT, "sources": [{}]},
        {**VALID_CHAT, "sources": [{"id": 3, "title": "x"}]},
        {**VALID_CHAT, "escalate": "false"},
        {**VALID_CHAT, "degraded": 1},
        {**VALID_CHAT, "path": None},
    ],
)
def test_ask_malformed_success_payload_fails_gracefully(payload):
    r = client_with(lambda req: httpx.Response(200, json=payload)).ask("hello", "s1")
    assert not r.ok
    assert "invalid response" in r.error
    assert r.request_id == "" and not r.sources


def test_ask_invalid_json_and_optional_defaults():
    bad = client_with(lambda req: httpx.Response(200, content=b"not JSON")).ask("hello", "s")
    assert not bad.ok and "invalid response" in bad.error
    minimal = {"answer": "ok", "intent": "rule", "request_id": "id"}
    result = client_with(lambda req: httpx.Response(200, json=minimal)).ask("hello", "s")
    assert result.ok
    assert result.sources == [] and result.path == ""
    assert result.escalate is False and result.degraded is False


@pytest.mark.parametrize(("rating", "status"), [(-1, 201), (0, 201), (1, 201), (-1, 404), (1, 422), (1, 500)])
def test_feedback_http_contract(rating, status):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(status)

    client = client_with(handler)
    success = client.send_feedback("chat-request-id", rating, "Good info")
    assert success is (status == 201)
    assert len(seen) == 1
    assert seen[0].method == "POST" and seen[0].url.path == "/v1/feedback"
    assert json.loads(seen[0].content) == {
        "request_id": "chat-request-id",
        "rating": rating,
        "comment": "Good info",
    }


@pytest.mark.parametrize("value", [None, "", "x" * 65])
def test_feedback_rejects_invalid_request_ids_without_sending(value):
    def handler(req):
        pytest.fail("Invalid feedback must not be posted")

    assert client_with(handler).send_feedback(value, 1) is False


@pytest.mark.parametrize("rating", [-2, 2, True, 1.0, None])
def test_feedback_rejects_invalid_ratings_without_sending(rating):
    def handler(req):
        pytest.fail("Invalid feedback must not be posted")

    assert client_with(handler).send_feedback("id1", rating) is False


@pytest.mark.parametrize("comment", ["x" * 501, 123])
def test_feedback_rejects_invalid_comments_without_sending(comment):
    def handler(req):
        pytest.fail("Invalid feedback must not be posted")

    assert client_with(handler).send_feedback("id1", 1, comment) is False


@pytest.mark.parametrize("exception", [httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError])
def test_feedback_transport_failure_never_claims_success(exception):
    def handler(req):
        raise exception("private details", request=req)

    assert client_with(handler).send_feedback("req1", -1) is False


def test_feedback_does_not_retry_on_server_failure():
    requests = []

    def handler(req):
        requests.append(req)
        return httpx.Response(503)

    assert client_with(handler).send_feedback("req1", 1) is False
    assert len(requests) == 1


@pytest.mark.parametrize(("status", "payload", "expected"), [
    (200, {"status": "ok", "version": "1.0.0"}, True),
    (200, {"status": "degraded"}, False),
    (200, [], False),
    (200, {}, False),
    (503, {"status": "ok"}, False),
    (404, {"status": "ok"}, False),
])
def test_health_checks_status_and_response_contract(status, payload, expected):
    seen = []

    def handler(req):
        seen.append(req)
        return httpx.Response(status, json=payload)

    assert client_with(handler).healthy() is expected
    assert len(seen) == 1 and seen[0].method == "GET"
    assert seen[0].url.path == "/health"


def test_health_invalid_body_and_connection_down():
    assert client_with(lambda req: httpx.Response(200, content=b"broken JSON")).healthy() is False

    def offline(req):
        raise httpx.ConnectError("offline", request=req)

    assert client_with(offline).healthy() is False


def test_ui_client_does_not_import_backend_code():
    source = (Path(__file__).resolve().parents[1] / "ui" / "api_client.py").read_text(encoding="utf-8")
    assert "import assistant_core" not in source
    assert "from assistant_core" not in source
    assert "import assistant_api" not in source
    assert "from assistant_api" not in source


def test_full_http_contract_with_actual_fastapi_and_sqlite(tmp_path):
    """Real FastAPI routes via TestClient; no external socket or mocked backend handler."""
    db_path = tmp_path / "m1_lab07_integration.sqlite"
    settings = Settings(
        data_dir=DATA,
        kb_dir=DATA / "kb",
        database_url=f"sqlite:///{db_path}",
        session_salt="synthetic-test-secret",
        api_admin_key="synthetic-admin-key",
        rate_limit_per_min=30,
    )
    with TestClient(create_app(settings=settings)) as api:
        def bridge(request):
            response = api.request(
                request.method, request.url.path, content=request.content, headers={"content-type": "application/json"}
            )
            return httpx.Response(response.status_code, content=response.content, headers=response.headers)

        with client_with(bridge) as client:
            assert client.healthy()
            first = client.ask("tuition for 18 credits and 2 retake", "browser-tab-1")
            second = client.ask("tuition for 18 credits and 2 retake", "browser-tab-1")
            assert first.ok and second.ok
            assert first.request_id and second.request_id and first.request_id != second.request_id
            assert first.answer == "Your tuition is 9,450,000 VND."
            assert client.send_feedback(first.request_id, -1, "test comment")
            assert client.send_feedback("nonexistent-request", 1) is False
            assert not client.ask("", "browser-tab-1").ok

        authenticated = api.get("/v1/feedback", headers={"X-API-Key": "synthetic-admin-key"})
        assert authenticated.status_code == 200
        rows = authenticated.json()
        assert len(rows) == 1 and rows[0]["request_id"] == first.request_id
        assert rows[0]["rating"] == -1
        assert rows[0]["comment"] == "test comment"

    assert db_path.exists()
    with sqlite3.connect(db_path) as db:
        columns = [row[1] for row in db.execute("PRAGMA table_info(chat_session)").fetchall()]
        assert "id" in columns
        stored_ids = [row[0] for row in db.execute("SELECT id FROM chat_session").fetchall()]
        assert stored_ids and "browser-tab-1" not in stored_ids


def test_real_fastapi_rate_limit_message(tmp_path):
    settings = Settings(
        data_dir=DATA,
        kb_dir=DATA / "kb",
        database_url=f"sqlite:///{tmp_path / 'rate_limit.sqlite'}",
        session_salt="synthetic-test-secret",
        rate_limit_per_min=1,
    )
    with TestClient(create_app(settings=settings)) as api:
        def bridge(request):
            result = api.request(
                request.method, request.url.path, content=request.content, headers={"content-type": "application/json"}
            )
            return httpx.Response(result.status_code, content=result.content)

        with client_with(bridge) as client:
            assert client.ask("hello", "tab-2").ok
            throttled = client.ask("hello again", "tab-2")
            assert not throttled.ok and "wait a minute" in throttled.error
