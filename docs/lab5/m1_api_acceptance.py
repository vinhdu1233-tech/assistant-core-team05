"""Lab 5 M1 HTTP acceptance tests — run ONLY after M3 integrates SQLite.

These tests are intentionally named m1_api_acceptance.py (not test_*.py)
so the normal repository pytest discovery does not run them against the
Lab 5 starter's in-memory FastAPI endpoints.

After M3's FastAPI integration, run explicitly from the repository root:
    python -m pytest -q docs/lab5/m1_api_acceptance.py
"""

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from assistant_api.main import create_app
from assistant_core.config import Settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ADMIN_KEY = "m1-integration-test-only"


def settings_for_temp_database(tmp_path):
    return Settings(
        data_dir=DATA_DIR,
        database_url=f"sqlite:///{tmp_path / 'feedback_integration.db'}",
        session_salt="m1-demo-salt-never-use-in-production",
        api_admin_key=ADMIN_KEY,
        rate_limit_per_min=30,
    )


def create_real_interaction(client, session_id="test-session-01"):
    response = client.post(
        "/v1/chat",
        json={"message": "tuition for 18 credits and 2 retake", "session_id": session_id},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["request_id"]
    return result["request_id"]


def test_http_feedback_valid_id_201_invalid_id_404_admin_401_and_restart(tmp_path):
    settings = settings_for_temp_database(tmp_path)
    headers = {"X-API-Key": ADMIN_KEY}
    with TestClient(create_app(settings=settings)) as client:
        request_id = create_real_interaction(client)

        created = client.post(
            "/v1/feedback",
            json={"request_id": request_id, "rating": 1, "comment": "useful"},
        )
        assert created.status_code == 201, created.text
        item = created.json()
        assert isinstance(item["id"], int) and item["id"] > 0
        assert item["request_id"] == request_id
        assert item["rating"] == 1
        assert item["comment"] == "useful"
        assert item["created_at"]

        missing_id = client.post(
            "/v1/feedback",
            json={"request_id": "no-such-response", "rating": -1},
        )
        assert missing_id.status_code == 404, missing_id.text

        assert client.get("/v1/feedback").status_code == 401
        assert client.get("/v1/feedback", headers={"X-API-Key": "bad-key"}).status_code == 401

        authorized = client.get("/v1/feedback", headers=headers)
        assert authorized.status_code == 200
        assert [row["id"] for row in authorized.json()] == [item["id"]]

    # A newly created FastAPI application must retrieve the same saved data.
    with TestClient(create_app(settings=settings)) as restarted_client:
        response = restarted_client.get("/v1/feedback", headers=headers)
        assert response.status_code == 200
        assert [row["id"] for row in response.json()] == [item["id"]]


def test_http_feedback_validation_and_newest_first(tmp_path):
    settings = settings_for_temp_database(tmp_path)
    with TestClient(create_app(settings=settings)) as client:
        first_request = create_real_interaction(client, session_id="s-1")
        second_request = create_real_interaction(client, session_id="s-2")

        invalid_rating = client.post("/v1/feedback", json={"request_id": first_request, "rating": 5})
        oversized_comment = client.post(
            "/v1/feedback",
            json={"request_id": first_request, "rating": 0, "comment": "x" * 501},
        )
        assert invalid_rating.status_code == 422
        assert oversized_comment.status_code == 422

        first = client.post("/v1/feedback", json={"request_id": first_request, "rating": 1})
        second = client.post("/v1/feedback", json={"request_id": second_request, "rating": -1})
        assert first.status_code == second.status_code == 201

        result = client.get("/v1/feedback", headers={"X-API-Key": ADMIN_KEY})
        assert result.status_code == 200
        assert [item["request_id"] for item in result.json()] == [
            second_request,
            first_request,
        ]


def test_http_interaction_keeps_only_metadata_and_session_hash(tmp_path):
    settings = settings_for_temp_database(tmp_path)
    raw_session = "raw-student-session-value"
    raw_message = "tuition for 18 credits and 2 retake"
    with TestClient(create_app(settings=settings)) as client:
        assert create_real_interaction(client, session_id=raw_session)

    database_path = tmp_path / "feedback_integration.db"
    assert database_path.is_file()
    with sqlite3.connect(database_path) as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(interaction)").fetchall()}
        assert "message" not in columns
        assert "question" not in columns
        assert "raw_message" not in columns

        sessions = [row[0] for row in db.execute("SELECT id FROM chat_session").fetchall()]
        assert sessions
        assert raw_session not in sessions
        assert all(len(session_id) == 16 for session_id in sessions)

        # The full question must not be serialized into any interaction field.
        rows = db.execute("SELECT * FROM interaction").fetchall()
        assert rows
        assert all(raw_message not in str(row) for row in rows)
