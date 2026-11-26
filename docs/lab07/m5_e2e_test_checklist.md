# Lab 07 — Member 5 Part E test results and regression checklist

Related assignment: Issue #61.

## Integrated browser run (M2)

The following results were observed on the combined #66–#70 candidate with Chrome, a running Streamlit UI, FastAPI and a temporary SQLite database. Browser inputs were automated with Playwright. The primary backend used the offline stub model. This run is separate from the earlier M5-only and participant evidence below.

| Browser action | Observed result |
| --- | --- |
| Click the thesis example in the sidebar | The question and answer appeared. The answer showed a two-credit shortfall for 118 credits, the 120-credit policy and source H26#5.3. See [before](evidence/before.png) and [after](evidence/after.png). |
| Ask what the capital of France is | The status note directed the student to the Training Office, room I.101. |
| Press Enter in an empty chat box, then separately submit 2,001 characters | Empty input left the chat history unchanged. The overlength message produced the validation warning. |
| Give one positive and one negative rating | Chrome showed a confirmation toast for each. The backend returned both persisted ratings through its feedback endpoint. |
| Submit the lost-card question at 390 × 844 | The answer and S26#3 appeared with the input visible and no page-level horizontal overflow. See [phone view](evidence/phone.png). |
| Stop FastAPI and submit another question | The UI showed a backend warning and a friendly chat error. See [offline view](evidence/backend-down.png). |
| Restart FastAPI with an unavailable local AI provider and a one-request rate limit | The first thesis response displayed its source-document fallback note. The next question produced the friendly rate-limit message. |

Local integrated checks: 310 pytest cases passed with one dependency deprecation warning. Ruff lint and format checks passed (64 Python files). Both Lab 6 offline comparisons ran to completion; the stub answered 14/20 and 17/25 correctly.

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

## D.4 scenario checklist on the original M5 branch

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

### M5 pull-request CI evidence

The PR #70 merge-ref workflow run [#45819969398](https://github.com/vinhdu1233-tech/assistant-core-team05/actions/runs/45819969398) completed successfully on Ubuntu with Python 3.11.18:

| Check | Result |
|---|---|
| `python -m pytest -q` | **237 passed, 1 warning** |
| `python -m ruff check .` | **Passed** |
| `python -m ruff format --check .` | **Passed — 60 files already formatted** |
| Lab 6 original 20-case comparison | **Passed** |
| Lab 6 expanded 25-case comparison | **Passed** |

This run checks the M5 branch against the then-current `main` (including merged M2 PR #65). It does **not** include the still-open M1 PR #66 or M3 PR #69, so it is not evidence for their pending changes or for the fully integrated team branch.

### Ownership and remaining validation

- The M5 AppTest cases are automated UI tests with a deterministic mocked client. M5 verifies how the page renders the friendly 429 result; M1 owns the HTTP contract and real FastAPI rate-limit tests.
- M3 owns 👍/👎 feedback behavior and its dedicated tests in PR #69. M5 does not duplicate those tests or modify `ui/app.py`.
- Manual browser checks are still pending; this document does not claim they were performed.
- After M1 #66 and M3 #69 are merged, rerun the listed suites and full CI on the integrated branch. Record the new results separately; do not attribute unrelated failures to M5 or report unobserved tests as passing.
