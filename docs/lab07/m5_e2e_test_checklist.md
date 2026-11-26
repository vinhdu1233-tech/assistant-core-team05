# Lab 07 — Member 5 end-to-end test checklist

Related assignment: https://github.com/vinhdu1233-tech/assistant-core-team05/issues/61

## Scope

This contribution adds isolated regression coverage around the existing HTTP UI client. It does not change ui/api_client.py, ui/app.py, or ui/logic.py, which are owned by other members.

## Automated regression coverage

The additions to tests/test_ui.py cover:

- HTTP 429 returns the rate-limit message instead of being treated as a successful answer.
- A successful chat response with degraded=true preserves the degraded flag and response path.
- A request timeout returns the friendly timeout message.
- A failed feedback request returns False.
- Health checks distinguish HTTP 200 from HTTP 503 and connection failure.

The pre-existing tests remain in place for normal chat, backend connection failure, HTTP 422/500, successful feedback, input validation, source formatting, and escalation notes.

## D.4 browser scenario checklist

These are manual browser checks. Do not mark a scenario passed until it has been run against the integrated FastAPI and Streamlit applications.

| D.4 scenario | Expected result | Status |
|---|---|---|
| Sidebar example | Selecting an example submits it as the question | Not run |
| Thesis question with 118 credits and sources | Answer and source references are displayed | Blocked: verify integrated backend and Member 2 source formatting |
| Out-of-domain escalation | Escalation note points to Training Office, room I.101 | Blocked: Member 2's status_note() is not implemented on current main |
| Blank question | UI shows validation warning and does not call chat API | Not run |
| 👍 and 👎 feedback | Each rating submits the corresponding value and the UI reflects the result | Not run; confirm feedback endpoint integration |
| Backend stopped | Health warning is visible and chat failure is friendly | Not run |
| Friendly error handling | HTTP errors/timeouts are displayed without a traceback | Automated client tests added; browser check not run |

## Commands to run after integration

From the repository root, in the project's configured virtual environment:

```powershell
python -m pytest -q tests/test_ui.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

For manual browser checks, start the FastAPI backend in one terminal:

```powershell
uvicorn assistant_api.main:create_app --factory --reload
```

Then start Streamlit in a second terminal:

```powershell
$env:ASSISTANT_API_URL = "http://127.0.0.1:8000"
streamlit run ui/app.py
```

Open http://127.0.0.1:8501.

## Integration notes and limitations

- Issue #57 (API client integration) and Issue #58 (source display/escalation notes) had no submitted implementation PRs when this checklist was prepared.
- The current main still contains NotImplementedError in format_sources() and status_note(); the existing tests for those functions are expected to fail until Issue #58 is integrated.
- The automated tests added here use httpx.MockTransport. They verify client behavior deterministically; they do not prove that the live FastAPI and Streamlit processes interoperate.
- No full-suite, Ruff, or manual browser result is claimed in this document. Record actual command output and browser evidence after the dependent work is merged.
