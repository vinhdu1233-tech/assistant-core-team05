# Lab 07 — Member 5 D.4 end-to-end verification

Related assignment: Issue #61.

## Automated UI scenarios

`tests/test_lab07_m5_e2e.py` exercises the Streamlit page with a deterministic mocked `AssistantClient`:

- Sidebar example selection submits the selected question.
- A thesis question renders the answer and multiple source references.
- An out-of-domain response displays the Training Office escalation note.
- Blank input displays validation feedback without calling the API.
- Positive feedback submits rating +1.
- Backend health failure and chat failure display friendly UI messages.
- Degraded and escalation states display the appropriate status notes.

Member 1's dedicated `tests/test_lab07_api_client_m1.py` and CI cover HTTP contract behavior, including 429, timeouts, malformed responses, backend connectivity, feedback persistence, and real localhost FastAPI/Streamlit process startup. Member 3's `tests/test_lab07_feedback_ui.py` covers positive/negative feedback confirmation, failed submissions, and retry behavior.

## Manual D.4 browser acceptance

The AppTest cases are automated UI tests, not a claim that a person manually clicked through a browser. Complete this table after running the integrated application in a browser:

| Scenario | Expected result | Status |
|---|---|---|
| Sidebar example | Selecting an example submits it | Automated AppTest; manual browser check pending |
| Thesis question, 118 credits and sources | Answer and source references are visible | Automated UI rendering test; verify actual answer against backend in browser |
| Out-of-domain escalation | Training Office, room I.101 is displayed | Automated AppTest; manual browser check pending |
| Blank question | Friendly validation, no API request | Automated AppTest; manual browser check pending |
| 👍 / 👎 feedback | Rating is saved; confirmation only after success; failed save can retry | Covered by M3 feedback AppTests; manual browser check pending |
| Backend stopped | Health warning and friendly chat failure | Automated AppTest; manual browser check pending |
| Friendly error handling | No traceback or raw server exception | M1 API-client regression tests; manual browser check pending |

## Commands

From repository root:

```powershell
python -m pytest -q tests/test_lab07_m5_e2e.py
python -m pytest -q tests/test_lab07_api_client_m1.py
python -m pytest -q tests/test_lab07_feedback_ui.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

For manual browser acceptance, follow the two-terminal startup instructions in `docs/lab07/setup.md`, then visit http://127.0.0.1:8501.

## Verification boundaries

- M1's PR #66 was open when this checklist was prepared; its tests and workflow are referenced as the intended API-client coverage and must be available on the integration branch before the combined suite can be considered complete.
- M3's PR #69 was open when this checklist was prepared; its feedback retry/confirmation tests should be included after integration.
- M2's source/status implementation is already merged in PR #65.
- The full repository suite has known unrelated Lab 07 warm-up U2–U4 failures and formatting issues reported by the member PRs. Record the actual current CI results; do not hide or relabel baseline failures.
- The AppTest suite uses mocked HTTP client methods to test UI behavior. It does not replace M1's real FastAPI contract tests or manual human browser acceptance.
- No local test or browser result is claimed by this document. Update the status table only with observed results.
