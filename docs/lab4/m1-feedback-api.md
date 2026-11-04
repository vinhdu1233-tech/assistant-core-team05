# M1 — Lab 4 Feedback API (Issue #17)

## API contract

| Method | Path | Request | Success | Expected errors |
| --- | --- | --- | --- | --- |
| POST | `/v1/feedback` | JSON: `request_id` (1–64 chars), `rating` (-1/0/1), optional `comment` (max 500 chars) | 201: validated feedback with sequential `id` and UTC `created_at` | 422 invalid request |
| GET | `/v1/feedback` | `X-API-Key` admin header | 200: feedback items stored in this app instance | 401 missing/wrong key |

The storage is an in-memory list, scoped to each FastAPI app instance; a server restart clears it.
The existing `require_admin` FastAPI dependency remains in place.

## Evidence and commands

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

Manual check (start the app server first; use the configured key from your **local** `.env`):

```bash
curl -i -X POST http://127.0.0.1:8000/v1/feedback \
  -H 'Content-Type: application/json' \
  -d '{"request_id":"abc123","rating":1,"comment":"Helpful"}'

curl -i http://127.0.0.1:8000/v1/feedback
curl -i http://127.0.0.1:8000/v1/feedback -H 'X-API-Key: <your local API_ADMIN_KEY>'
```

## Team dependencies before final submission

- T1 `POST /v1/chat` (M2) must be integrated before capturing the required **successful chat call in `/docs`**. Do not use a fabricated screenshot.
- T4 `GET /v1/weather` (M5) and other pending tasks must be merged before expecting the full suite to pass.
- Do not merge the setup PR to `main` until integration checks are green.
- The final `v0.4-api` tag belongs to the Tech Lead after all reviewed feature PRs are integrated.
