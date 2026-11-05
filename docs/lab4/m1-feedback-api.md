# M1 — Lab 4 Feedback API (Issue #17)

## API contract

| Method | Path | Request | Success | Expected errors |
| --- | --- | --- | --- | --- |
| POST | `/v1/feedback` | JSON: `request_id` (1–64 chars), `rating` (-1/0/1), optional `comment` (max 500 chars) | 201: validated feedback with sequential `id` and UTC `created_at` | 422 invalid request |
| GET | `/v1/feedback` | `X-API-Key` admin header | 200: feedback items stored in this app instance | 401 missing/wrong key |

The storage is an in-memory list, scoped to each FastAPI app instance; a server restart clears it.
The existing `require_admin` FastAPI dependency remains in place.

## Test evidence and commands

CI result for the original M1 implementation (`a57f44a`):
[GitHub Actions run #49](https://github.com/vinhdu1233-tech/assistant-core-team05/actions/runs/41838268373)
reported **74 passed, 3 failed, 1 skipped**. The failed tests were
`test_chat_fee` (T1, M2) and `test_weather_ok` /
`test_weather_down_returns_503` (T4, M5), because those endpoints
were still placeholders in the shared base. The M1 feedback tests and
the P1–P5 warm-up tests passed in that run. This is **not** evidence of
a green full-suite CI. Recheck the latest run after integration.

Focused tests:

```bash
python -m pytest -q tests/test_api.py -k feedback
python -m pytest -q tests/test_feedback_m1.py
```

Personal warm-up P1–P5:

```bash
python -m pytest -q practice/test_hello_api.py
cd practice
uvicorn hello_api:app --reload
```

Manual check from the repository root after installing the project
(`python -m pip install -e .`). Use a throwaway local demo key here; never
commit actual keys or `.env`. Start the server in Terminal 1:

```bash
API_ADMIN_KEY=local-demo-key python -m uvicorn assistant_api.main:create_app --factory --reload
```

Run these in Terminal 2:

```bash
curl -i -X POST http://127.0.0.1:8000/v1/feedback \
  -H 'Content-Type: application/json' \
  -d '{"request_id":"abc123","rating":1,"comment":"Helpful"}'

# Expected: 401 without a key
curl -i http://127.0.0.1:8000/v1/feedback

# Expected: 200 with the saved feedback
curl -i http://127.0.0.1:8000/v1/feedback \
  -H 'X-API-Key: local-demo-key'

# Expected: 422 for a rating outside -1, 0, 1
curl -i -X POST http://127.0.0.1:8000/v1/feedback \
  -H 'Content-Type: application/json' \
  -d '{"request_id":"invalid","rating":5}'
```

Capture actual successful feedback requests in Swagger
(`http://127.0.0.1:8000/docs`) if individual evidence is requested.
A successful **chat** screenshot must be captured only after M2 T1 is
integrated. No screenshots are claimed in this document.

## Team dependencies before final submission

- T1 `POST /v1/chat` (M2) must be integrated before capturing the required **successful chat call in `/docs`**. Do not use a fabricated screenshot.
- T4 `GET /v1/weather` (M5) and other pending tasks must be merged before expecting the full suite to pass.
- Do not merge the setup PR to `main` until integration checks are green.
- The final `v0.4-api` tag belongs to the Tech Lead after all reviewed feature PRs are integrated.
