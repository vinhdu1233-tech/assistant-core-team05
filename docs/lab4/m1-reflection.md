# Lab 4 — H2 Reflection (Member 1)

1. In Lab 3, I called `service.handle()` directly within Python, so the caller needed to use our Python code.
2. In Lab 4, FastAPI lets an external client send JSON over HTTP, validates the request with Pydantic, and returns JSON with an HTTP status code.
3. For my Lab 4 task, I implemented `POST /v1/feedback` to save ratings with IDs and UTC timestamps, and `GET /v1/feedback` to let authorized admins read them.
4. I tested that valid feedback returns HTTP 201, invalid ratings return HTTP 422, and missing or incorrect admin keys return HTTP 401.
5. Compared with a direct function call, an HTTP API is easier to connect to websites or mobile apps, but it also requires careful input validation and access control.
