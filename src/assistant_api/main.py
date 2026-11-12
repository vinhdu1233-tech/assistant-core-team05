"""FastAPI application — Lab 4 STARTER.  Run:  uvicorn assistant_api.main:create_app --factory --reload

Most of the file is given. Complete the four TODOs (T1–T4); the tests in tests/test_api.py tell you when you are done.

Endpoints (v1): GET /health, POST /v1/chat, POST /v1/feedback, GET /v1/feedback (admin), GET /v1/weather
"""

from __future__ import annotations

import uuid  # noqa: F401
from datetime import datetime, timezone  # noqa: F401
from time import perf_counter

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from assistant_api.db import Repository, init_db, make_engine
from assistant_api.ratelimit import RateLimiter
from assistant_api.schemas import ChatRequest, ChatResponse, ErrorResponse, FeedbackIn, FeedbackOut, Weather
from assistant_api.weather import ExternalServiceError, WeatherClient  # noqa: F401
from assistant_core import AssistantService, Message, build_service  # noqa: F401
from assistant_core.config import Settings, load_settings
from assistant_core.models import Intent


def create_app(
    settings: Settings | None = None, service: AssistantService | None = None, weather: WeatherClient | None = None
) -> FastAPI:
    settings = settings or load_settings()
    service = service or build_service(settings)
    weather = weather or WeatherClient(
        settings.weather_url, settings.campus_lat, settings.campus_lon, timeout_s=settings.weather_timeout_s
    )
    limiter = RateLimiter(settings.rate_limit_per_min)  # used only in the BONUS task
    engine = make_engine(settings.database_url)
    init_db(engine)
    repo = Repository(engine, settings.session_salt)

    app = FastAPI(
        title="Study Assistant API", version="1.0.0", description="Backend of the CSC10014 Smart Virtual Assistant."
    )

    def error(code: int, key: str, message: str) -> JSONResponse:
        return JSONResponse(status_code=code, content={"error": {"code": key, "message": message}})

    @app.exception_handler(RequestValidationError)
    async def on_validation(_: Request, exc: RequestValidationError):
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"][1:]) or "body"
        return error(422, "invalid_request", f"{field}: {first['msg']}")

    @app.exception_handler(HTTPException)
    async def on_http(_: Request, exc: HTTPException):
        return error(exc.status_code, str(exc.detail).lower().replace(" ", "_"), str(exc.detail))

    def require_admin(x_api_key: str | None = Header(default=None)) -> None:
        if not settings.api_admin_key or x_api_key != settings.api_admin_key:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid API key")

    @app.get("/health", tags=["ops"])
    def health() -> dict:
        return {"status": "ok", "version": app.version}

    @app.get("/v1/offices", tags=["offices"])
    def list_offices() -> list[dict[str, str]]:
        return [
            {
                "name": office.name,
                "room": office.room,
                "hours": office.hours,
            }
            for office in service.offices.all()
        ]

    @app.post(
        "/v1/chat",
        response_model=ChatResponse,
        tags=["chat"],
        responses={422: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
    )
    def chat(req: ChatRequest, request: Request) -> ChatResponse:
        client_ip = request.client.host if request.client else "unknown"

        if not limiter.allow(client_ip):
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many requests",
            )

        start = perf_counter()
        resp = service.handle(Message(text=req.message, session_id=req.session_id))
        latency_ms = (perf_counter() - start) * 1000

        request_id = uuid.uuid4().hex[:12]

        repo.record_interaction(
            raw_session=req.session_id,
            request_id=request_id,
            intent=resp.intent.value if hasattr(resp.intent, "value") else str(resp.intent),
            topic=None,
            resolved=resp.intent != Intent.UNKNOWN,
            degraded=resp.degraded,
            latency_ms=latency_ms,
        )

        return ChatResponse(
            **resp.model_dump(),
            request_id=request_id,
        )

    def feedback_to_response(item) -> FeedbackOut:
        created_at = item.created_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        else:
            created_at = created_at.astimezone(timezone.utc)

        return FeedbackOut(
            id=item.id,
            request_id=item.request_id,
            rating=item.rating,
            comment=item.comment,
            created_at=created_at,
        )

    @app.post("/v1/feedback", response_model=FeedbackOut, status_code=201, tags=["feedback"])
    def add_feedback(fb: FeedbackIn) -> FeedbackOut:
        item = repo.add_feedback(
            request_id=fb.request_id,
            rating=fb.rating,
            comment=fb.comment,
        )

        if item is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Request ID not found",
            )

        return feedback_to_response(item)

    @app.get(
        "/v1/feedback",
        response_model=list[FeedbackOut],
        tags=["feedback"],
        dependencies=[Depends(require_admin)],
    )
    def list_feedback() -> list[FeedbackOut]:
        items = repo.list_feedback()
        return [feedback_to_response(item) for item in items]

    @app.get("/v1/weather", response_model=Weather, tags=["external"], responses={503: {"model": ErrorResponse}})
    def campus_weather() -> Weather:
        try:
            return weather.current()
        except ExternalServiceError:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Weather service unavailable") from None

    return app
