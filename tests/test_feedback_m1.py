"""Regression tests for feedback endpoints with Lab 5 SQLite persistence."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from assistant_api.main import create_app


@pytest.fixture
def feedback_client(settings, service, tmp_path):
    settings = settings.model_copy(
        update={
            "api_admin_key": "test-admin-key",
            "database_url": f"sqlite:///{(tmp_path / 'feedback.db').as_posix()}",
        }
    )
    return TestClient(create_app(settings=settings, service=service))


def create_request_id(client, session_id="test-session"):
    response = client.post(
        "/v1/chat",
        json={
            "message": "tuition for 18 credits",
            "session_id": session_id,
        },
    )
    assert response.status_code == 200
    return response.json()["request_id"]


def test_feedback_post_returns_201_with_sequential_ids_and_utc_time(feedback_client):
    for expected_id, rating in enumerate((-1, 0, 1), start=1):
        request_id = create_request_id(feedback_client, f"session-{expected_id}")

        response = feedback_client.post(
            "/v1/feedback",
            json={"request_id": request_id, "rating": rating, "comment": "useful"},
        )

        assert response.status_code == 201
        item = response.json()
        assert item["id"] == expected_id
        assert item["rating"] == rating
        assert item["request_id"] == request_id
        assert item["comment"] == "useful"
        assert datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")).utcoffset() == timedelta(0)


def test_feedback_admin_list_requires_correct_key(feedback_client):
    request_id = create_request_id(feedback_client)
    response = feedback_client.post(
        "/v1/feedback",
        json={"request_id": request_id, "rating": 1},
    )
    assert response.status_code == 201
    saved = response.json()

    missing = feedback_client.get("/v1/feedback")
    invalid = feedback_client.get("/v1/feedback", headers={"X-API-Key": "wrong-key"})
    authorized = feedback_client.get("/v1/feedback", headers={"X-API-Key": "test-admin-key"})

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert authorized.status_code == 200
    assert authorized.json() == [saved]


@pytest.mark.parametrize("rating", [-2, 2, 5])
def test_feedback_rejects_invalid_rating(feedback_client, rating):
    response = feedback_client.post(
        "/v1/feedback",
        json={"request_id": "invalid-rating", "rating": rating},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_feedback_rejects_invalid_payload(feedback_client):
    request_id = create_request_id(feedback_client)

    empty_id = feedback_client.post("/v1/feedback", json={"request_id": "", "rating": 0})
    long_comment = feedback_client.post(
        "/v1/feedback",
        json={"request_id": request_id, "rating": 1, "comment": "x" * 501},
    )
    long_id = feedback_client.post("/v1/feedback", json={"request_id": "r" * 65, "rating": 1})
    missing_rating = feedback_client.post("/v1/feedback", json={"request_id": request_id})

    assert empty_id.status_code == 422
    assert long_comment.status_code == 422
    assert long_id.status_code == 422
    assert missing_rating.status_code == 422

    valid = feedback_client.post(
        "/v1/feedback",
        json={"request_id": request_id, "rating": 0},
    )
    assert valid.status_code == 201
    assert valid.json()["id"] == 1


def test_feedback_persists_across_app_instances(settings, service, tmp_path):
    settings = settings.model_copy(
        update={
            "api_admin_key": "test-admin-key",
            "database_url": f"sqlite:///{(tmp_path / 'shared.db').as_posix()}",
        }
    )

    first_app = TestClient(create_app(settings=settings, service=service))
    request_id = create_request_id(first_app)

    saved = first_app.post(
        "/v1/feedback",
        json={"request_id": request_id, "rating": 1},
    )
    assert saved.status_code == 201

    second_app = TestClient(create_app(settings=settings, service=service))
    headers = {"X-API-Key": "test-admin-key"}

    first_items = first_app.get("/v1/feedback", headers=headers).json()
    second_items = second_app.get("/v1/feedback", headers=headers).json()

    assert len(first_items) == 1
    assert second_items == first_items
