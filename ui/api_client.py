"""HTTP-only adapter between the Streamlit UI and the Team05 FastAPI backend.

No backend package is imported here: a UI rerun opens an HTTP client, while
the API is responsible for routing, persistence, validation, and security.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx


@dataclass
class ChatResult:
    ok: bool
    answer: str = ""
    intent: str = ""
    sources: list[dict] = field(default_factory=list)
    path: str = ""
    escalate: bool = False
    degraded: bool = False
    request_id: str = ""
    error: str = ""  # A user-facing sentence, never a raw exception or server detail.


class AssistantClient:
    """Small synchronous HTTP client for Streamlit; injectable transport for tests."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout_s: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._http = httpx.Client(base_url=base_url, timeout=timeout_s, transport=transport)

    def close(self) -> None:
        """Release connections when the client is no longer needed."""
        self._http.close()

    def __enter__(self) -> AssistantClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    @staticmethod
    def _chat_result(data: object) -> ChatResult:
        """Validate the required API contract before letting the UI render it."""
        if not isinstance(data, dict):
            raise ValueError("Chat response must be an object")

        answer, intent, request_id = (
            data.get("answer"),
            data.get("intent"),
            data.get("request_id"),
        )
        if not isinstance(answer, str) or not isinstance(intent, str) or not intent:
            raise ValueError("Missing answer or intent")
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("Missing request ID")

        sources = data.get("sources", [])
        if not isinstance(sources, list) or any(
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not isinstance(item.get("title"), str)
            for item in sources
        ):
            raise ValueError("Invalid sources")
        path = data.get("path", "")
        escalate = data.get("escalate", False)
        degraded = data.get("degraded", False)
        if not isinstance(path, str) or not isinstance(escalate, bool) or not isinstance(degraded, bool):
            raise ValueError("Invalid chat status flags")

        return ChatResult(
            ok=True,
            answer=answer,
            intent=intent,
            sources=sources,
            path=path,
            escalate=escalate,
            degraded=degraded,
            request_id=request_id,
        )

    def ask(self, message: str, session_id: str) -> ChatResult:
        """POST the unmodified session ID and question to /v1/chat."""
        try:
            response = self._http.post("/v1/chat", json={"message": message, "session_id": session_id})
        except httpx.TimeoutException:
            return ChatResult(ok=False, error="The assistant is taking too long. Please try again.")
        except httpx.HTTPError:
            return ChatResult(ok=False, error="Cannot reach the assistant backend. Is it running?")

        if response.status_code == 422:
            return ChatResult(ok=False, error="Please type a question (1–2000 characters).")
        if response.status_code == 429:
            return ChatResult(ok=False, error="Too many questions in a short time. Please wait a minute.")
        if response.status_code != 200:
            return ChatResult(ok=False, error=f"Something went wrong on our side (error {response.status_code}).")

        try:
            return self._chat_result(response.json())
        except (ValueError, TypeError):
            return ChatResult(ok=False, error="The assistant returned an invalid response. Please try again.")

    def send_feedback(self, request_id: str, rating: int, comment: str | None = None) -> bool:
        """Post a rating for a real response; never silently retry a write."""
        if (
            not isinstance(request_id, str)
            or not request_id
            or len(request_id) > 64
            or type(rating) is not int
            or rating not in (-1, 0, 1)
            or (comment is not None and (not isinstance(comment, str) or len(comment) > 500))
        ):
            return False
        try:
            response = self._http.post(
                "/v1/feedback",
                json={"request_id": request_id, "rating": rating, "comment": comment},
            )
        except httpx.HTTPError:
            return False
        return response.status_code == 201

    def healthy(self) -> bool:
        """Only a 200 response with the FastAPI health contract counts as healthy."""
        try:
            response = self._http.get("/health")
            return (
                response.status_code == 200
                and isinstance((data := response.json()), dict)
                and data.get("status") == "ok"
            )
        except (httpx.HTTPError, ValueError, TypeError):
            return False
