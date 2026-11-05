# Lab 4 — H2 Reflection (M2)

1. In Lab 3, I called `service.handle()` directly from Python code to process a user message.
2. In Lab 4, users can send an HTTP POST request to `/v1/chat` instead of calling the Python function directly.
3. FastAPI receives the JSON input, validates it using Pydantic, and forwards the message to the existing service.
4. The service returns an answer, which FastAPI converts into a JSON response with an HTTP status code and a request ID.
5. The HTTP approach is more flexible because websites, mobile apps, and other services can use the same backend without depending on its internal Python code.