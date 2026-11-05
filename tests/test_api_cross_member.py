"""Extra integration regression tests for Lab 4 Team 05 (M2, M3, M4, M5, M6).

Run after all feature PRs are integrated into setup/lab04-api. No network calls.
This file supplements, and does not replace, tests/test_api.py.
"""

import re

import httpx
import pytest
from fastapi.testclient import TestClient

from assistant_api.main import create_app
from assistant_api.ratelimit import RateLimiter
from assistant_api.weather import WeatherClient

WEATHER_JSON = {
    "current": {
        "time": "2026-11-05T09:00",
        "temperature_2m": 30.5,
        "weather_code": 3,
        "wind_speed_10m": 7.2,
    }
}


def weather_client(handler):
    return WeatherClient(
        "https://weather.example.test/forecast",
        10.7626,
        106.6822,
        retries=0,
        transport=httpx.MockTransport(handler),
    )


def test_m2_chat_has_distinct_valid_request_ids(settings, service):
    client = TestClient(create_app(settings=settings, service=service))
    ids = []
    for _ in range(3):
        result = client.post("/v1/chat", json={"message": "tuition for 18 credits and 2 retake"})
        assert result.status_code == 200
        body = result.json()
        assert body["intent"] == "fee"
        assert body["answer"]
        assert isinstance(body["sources"], list)
        assert isinstance(body["degraded"], bool)
        assert re.fullmatch(r"[0-9a-f]{12}", body["request_id"])
        ids.append(body["request_id"])
    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": "a" * 2001},
        {"message": "hi", "session_id": "x" * 65},
        {"message": 123},
    ],
)
def test_m2_chat_invalid_payload_is_consistent_422(settings, service, payload):
    client = TestClient(create_app(settings=settings, service=service))
    result = client.post("/v1/chat", json=payload)
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "invalid_request"


def test_m3_openapi_lists_all_integrated_routes(settings, service):
    client = TestClient(create_app(settings=settings, service=service))
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert {"/health", "/v1/chat", "/v1/feedback", "/v1/offices", "/v1/weather"} <= set(paths)
    assert "post" in paths["/v1/chat"]
    assert {"get", "post"} <= set(paths["/v1/feedback"])


def test_m4_offices_match_core_records_and_fields(settings, service):
    client = TestClient(create_app(settings=settings, service=service))
    result = client.get("/v1/offices")
    assert result.status_code == 200
    expected = [
        {"name": office.name, "room": office.room, "hours": office.hours}
        for office in service.offices.all()
    ]
    assert expected
    assert result.json() == expected
    assert all(set(item) == {"name", "room", "hours"} for item in result.json())


def test_m5_weather_uses_fresh_cache_without_second_upstream_call(settings, service):
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return httpx.Response(200, json=WEATHER_JSON)

    client = TestClient(create_app(settings=settings, service=service, weather=weather_client(handler)))
    first = client.get("/v1/weather")
    second = client.get("/v1/weather")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["stale"] is False
    assert first.json()["temperature_c"] == 30.5
    assert calls["count"] == 1


def test_m5_upstream_http_500_maps_to_standard_503(settings, service):
    client = TestClient(
        create_app(
            settings=settings,
            service=service,
            weather=weather_client(lambda request: httpx.Response(500)),
        )
    )
    result = client.get("/v1/weather")
    assert result.status_code == 503
    assert result.json()["error"]["code"] == "weather_service_unavailable"


def test_m6_chat_limit_returns_standard_429(settings, service):
    restricted = settings.model_copy(update={"rate_limit_per_min": 2})
    client = TestClient(create_app(settings=restricted, service=service))
    statuses = [client.post("/v1/chat", json={"message": "hi"}).status_code for _ in range(3)]
    assert statuses == [200, 200, 429]
    denied = client.post("/v1/chat", json={"message": "hi"})
    assert denied.status_code == 429
    assert denied.json()["error"]["code"] == "too_many_requests"


def test_m6_rate_limit_is_per_app_instance(settings, service):
    restricted = settings.model_copy(update={"rate_limit_per_min": 1})
    first = TestClient(create_app(settings=restricted, service=service))
    second = TestClient(create_app(settings=restricted, service=service))
    assert first.post("/v1/chat", json={"message": "hi"}).status_code == 200
    assert first.post("/v1/chat", json={"message": "hi"}).status_code == 429
    assert second.post("/v1/chat", json={"message": "hi"}).status_code == 200


def test_m6_limiter_tracks_distinct_clients():
    limiter = RateLimiter(per_minute=1)
    assert limiter.allow("client-a")
    assert not limiter.allow("client-a")
    assert limiter.allow("client-b")
