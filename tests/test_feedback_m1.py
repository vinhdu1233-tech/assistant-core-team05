"""Focused tests for Member 1's Lab 4 feedback endpoints (Issue #17)."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from assistant_api.main import create_app


@pytest.fixture
def feedback_client(settings, service):
    settings = settings.model_copy(update={"api_admin_key": "test-admin-key"})
    return TestClient(create_app(settings=settings, service=service))


def test_feedback_post_returns_201_with_sequential_ids_and_utc_time(feedback_client):
    ratings = (-1, 0, 1)
    for expected_id, rating in enumerate(ratings, start=1):
        response = feedback_client.post(
            "/v1/feedback",
            json={"request_id": f"req-{expected_id}", "rating": rating, "comment": "useful"},
        )
        assert response.status_code == 201
        item = response.json()
        assert item["id"] == expected_id
        assert item["rating"] == rating
        assert item["request_id"] == f"req-{expected_id}"
        assert item["comment"] == "useful"
        assert datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")).utcoffset() == timedelta(0)


def test_feedback_admin_list_requires_correct_key(feedback_client):
    saved = feedback_client.post("/v1/feedback", json={"request_id": "req-123", "rating": 1}).json()

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
    empty_id = feedback_client.post("/v1/feedback", json={"request_id": "", "rating": 0})
    long_comment = feedback_client.post(
        "/v1/feedback",
        json={"request_id": "req-123", "rating": 1, "comment": "x" * 501},
    )
    long_id = feedback_client.post(
        "/v1/feedback",
        json={"request_id": "r" * 65, "rating": 1},
    )
    missing_rating = feedback_client.post("/v1/feedback", json={"request_id": "missing-rating"})

    assert empty_id.status_code == 422
    assert long_comment.status_code == 422
    assert long_id.status_code == 422
    assert missing_rating.status_code == 422

    # Invalid submissions must not consume IDs or create feedback records.
    valid = feedback_client.post("/v1/feedback", json={"request_id": "valid", "rating": 0})
    assert valid.status_code == 201
    assert valid.json()["id"] == 1


def test_feedback_store_is_isolated_per_app(settings, service):
    settings = settings.model_copy(update={"api_admin_key": "test-admin-key"})
    first_app = TestClient(create_app(settings=settings, service=service))
    second_app = TestClient(create_app(settings=settings, service=service))
    first_app.post("/v1/feedback", json={"request_id": "first", "rating": 1})

    headers = {"X-API-Key": "test-admin-key"}
    assert len(first_app.get("/v1/feedback", headers=headers).json()) == 1
    assert second_app.get("/v1/feedback", headers=headers).json() == []
