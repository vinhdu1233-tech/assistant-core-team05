# Lab 07 — Member 5 Part E test results and regression checklist

Related assignment: Issue #61.

## Scope and ownership

This PR covers Member 5's Part E work: end-to-end UI scenarios, regression tests, and recording test evidence. It does not implement or modify features owned by M1 (`ui/api_client.py`), M2 (`ui/logic.py`), or M3 (`ui/app.py`).

## Automated Streamlit scenarios

Run the M5-owned UI regression suite:

`tests/test_lab07_m5_e2e.py`

It uses Streamlit AppTest with a deterministic mocked `AssistantClient` to verify:

- A sidebar sample question is submitted with the active session ID.
- A thesis question mentioning 118 credits displays the answer and multiple source references.
- An out-of-scope question displays the Training Office escalation note.
- Empty and overlength questions are rejected before an API request is made.
- A stopped backend displays the health warning and friendly chat error.
- A rate-limit error (429 response surfaced by the client) is displayed without a traceback.
- Degraded and escalation response states display their status notes.

These tests validate the UI response to client outcomes. They do not pretend to replace real HTTP integration or manual browser testing.

## Existing member-owned regression coverage

The integrated test plan also relies on the following separately owned work:

- **M1 / PR #66:** `tests/test_lab07_api_client_m1.py` covers HTTP request/response contracts, backend connectivity, timeout/error handling, HTTP 429, and a real FastAPI rate-limit test. It also exercises actual local FastAPI and Streamlit server startup in its workflow.
- **M3 / PR #69:** `tests/test_lab07_feedback_ui.py` covers 👍 and 👎 success, failed submissions, confirmation state, and retry behavior.
- **M2 / merged PR #65:** `ui/logic.py` provides source formatting and escalation/degraded status notes used by the UI.

M5 does not duplicate the M1 HTTP contract tests or M3 feedback confirmation tests. Confirm those PRs are merged into the integration branch before treating the combined test suite as the final integrated result.

## D.4 scenario checklist

| Scenario | M5 / team test coverage | Manual browser evidence |
|---|---|---|
| Sidebar example question | M5 AppTest | Pending |
| Thesis question with 118 credits and sources | M5 AppTest verifies answer/source rendering; M1 covers real HTTP/backend integration | Pending: verify the actual answer against the running backend |
| Out-of-domain question | M5 AppTest verifies escalation note | Pending |
| Empty question | M5 AppTest verifies validation and no API call | Pending |
| Overlength invalid question | M5 AppTest verifies validation and no API call | Pending |
| 👍 / 👎 feedback | M3 AppTest verifies both ratings, failed save, and retry | Pending |
| Backend stopped | M5 AppTest verifies health warning and friendly error; M1 covers connection failures | Pending |
| HTTP 429 rate limit | M1 real FastAPI/client regression; M5 verifies friendly UI rendering | Pending |
| Degraded mode | M5 AppTest verifies the degraded status note | Pending |

Do not mark manual browser checks complete based only on AppTest or HTTP tests. Record observed browser results after launching the integrated application.

## Commands

From the repository root, after the member PRs have been integrated:

```powershell
python -m pytest -q tests/test_lab07_m5_e2e.py
python -m pytest -q tests/test_lab07_api_client_m1.py
python -m pytest -q tests/test_lab07_feedback_ui.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

For the manual browser check, follow the project's setup instructions, start FastAPI and Streamlit in separate terminals, then visit http://127.0.0.1:8501. Test the scenarios above, including stopping FastAPI while the UI is open.

## Evidence status and limitations

- The M5 AppTest cases are automated UI tests with a mocked client.
- M1's rate-limit test exercises the real FastAPI app through TestClient; M5's rate-limit UI test verifies the resulting friendly message is rendered.
- M3 owns feedback UI behavior and its dedicated regression tests.
- Manual browser checks are still pending; this document does not claim they were performed.
- Run the commands above on the integrated branch and record the actual CI/local results. Do not attribute unrelated baseline failures to M5 or report unobserved tests as passing.
