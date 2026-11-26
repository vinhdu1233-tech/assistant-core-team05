# Lab 07 — M1 HTTP API Client / Issue #57

**Owner:** M1 (vinhdu1233-tech). **Base:** M3 setup PR #63 merged to `main` at `7f978125`.  
**Instructor source:** CSC10014 Lab 7 pp. 3, 6, 9–10, 12; M1 responsibility shown in the team assignment.  
**File ownership:** `ui/api_client.py`, M1-specific regression tests and this handoff note. No changes to M2's `ui/logic.py`, M3's `ui/app.py`, backend, or starter tests.

## Contract reviewed

| HTTP request | Actual Team05 FastAPI contract | Client behavior |
| --- | --- | --- |
| `GET /health` | 200 JSON `{"status":"ok","version":"1.0.0"}` | Healthy only for 200 and `status: ok`; any connection/timeout/bad JSON fails closed |
| `POST /v1/chat` | JSON `{"message": str, "session_id": str}` | Preserve caller's session ID; map 200 answer/intent/sources/path/escalate/degraded/request_id into ChatResult |
| 422 | Pydantic validation errors | Plain sentence asking for 1–2000 characters |
| 429 | FastAPI rate limiter | Plain sentence asking to wait a minute |
| Timeout | httpx timeout | Friendly retry message, no exception displayed |
| Connection / network error | httpx HTTPError | Friendly backend-not-reachable message |
| Other status | 4xx/5xx | Generic sentence with HTTP code, no response body or server exception leaked |
| 200 with malformed body | Incorrect upstream payload | `ok=False`, friendly invalid response message; no UI crash |
| `POST /v1/feedback` | `{"request_id":str,"rating":-1/0/1,"comment":str/null}`; 201 success, unknown ID 404 | Return True only on HTTP 201. Invalid local inputs or HTTP/network errors return False. Never retry feedback automatically. |

The UI uses HTTP only and does **not** import `assistant_core` or `assistant_api`. Backend remains responsible for database/authorization/persistent request metadata. Client closes connections through `close()` or its optional context-manager interface.

## Regression tests

```powershell
python -m pytest -q tests/test_lab07_api_client_m1.py
python -m pytest -q tests/test_ui.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

The focused suite covers each API route, session/request-ID propagation, standard and malformed success responses, all timeout classes, transport failures, 422, 429, HTTP 4xx/5xx, feedback rating boundaries, no silent duplicate POST, health errors, and exclusion of backend imports.

Two tests call the **actual FastAPI app** in-process via FastAPI TestClient and bridge all requests through the same HTTP request/response contract: real SQLite persistence, feedback -1, unknown request ID 404, validation 422, rate limit 429, distinct request IDs and hashed session ID. Those tests do not bind real ports, so they are not a substitute for a two-server manual browser demonstration.

## Automated real-port smoke (CI)

The new dedicated GitHub Actions workflow also starts **both actual local processes** on the CI runner: FastAPI (port 8000) and Streamlit (port 8501). It waits until both HTTP health endpoints return success, retrieves the Streamlit HTML page, calls the live FastAPI through this M1 AssistantClient, checks `request_id` and session propagation, posts -1 feedback, verifies the saved feedback via authenticated admin GET, rejects an unknown feedback ID, and checks HTTP 422. All requests use synthetic data and a disposable SQLite file; processes are killed at the end of the job.

[First verified two-server smoke success, CI #45762782196](https://github.com/vinhdu1233-tech/assistant-core-team05/actions/runs/45762782196): **63 M1 tests passed**, Ruff lint PASS, Ruff format PASS, and the live-port smoke PASS. A successful health request to Streamlit proves its server launched, **not** that a human clicked through every browser interaction. M3/M5 must still finish visual/UX and end-to-end browser acceptance checks after L1/L2 and F1 feedback UI wiring are complete.

## H2 reflection
`docs/lab07/m1-h2-reflection.md` provides the requested **two sentences** (one idea applied; one proposed improvement), marked as an AI-assisted draft for the M1 member to review after reading the assigned Google PAIR pages.

## Two-server smoke instructions (requires someone running on a computer)

With dependencies installed from `requirements.txt` and `pip install -e .`, from the repository root:

**Terminal 1:**
```powershell
uvicorn assistant_api.main:create_app --factory --reload
```

**Terminal 2:**
```powershell
$env:ASSISTANT_API_URL = "http://127.0.0.1:8000"
streamlit run ui/app.py
```

Visit `http://127.0.0.1:8501`; verify no red backend banner, a thesis question returns a source, its answer has a request ID for feedback, and 👍/👎 can send to the API. Restart API, check page becomes unreachable then recovers. Submit an empty/oversized question and trigger rate limiting. The chat UI is a separate member's file; note that the setup UI can currently thank the user after a failed feedback POST, which **requires an M3 fix in `ui/app.py`** before claiming end-to-end feedback UX fully correct.

**Coordination:** PR #65 (M2 L1/L2) and warm-up U2–U4 are separate tasks that were still pending on base at the time of this handoff. Do not disable or skip their tests just to make the M1 PR appear green. CI must be evaluated with these known base failures attributed accurately.

## AI assistance
ChatGPT assisted with code, tests, and documentation. All network/database tests use synthetic IDs/data; no real student information or private API keys are committed. Have a teammate review this PR before merging to main.
