# Lab 07 — Team05 setup (Member 3)

Source: https://github.com/CSC10014-at-fit-hcmus/public_materials/tree/main/lab07

This PR adds the Lab07-specific UI scaffold without replacing Team05's existing Lab06 backend. Instructor's `ui/logic.py` retains the L1/L2 TODOs assigned to Member 2 (#58). Instructor's practice U2–U4 TODOs are also retained; they are not completed by the setup task.

## Windows PowerShell (from repository root)

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

Copy `.env.example` to `.env` only if needed; never commit secrets. If backend uses environment variables, load them in your shell before starting.

Terminal 1 (backend):

```powershell
uvicorn assistant_api.main:create_app --factory --reload
```

Terminal 2 (Streamlit):

```powershell
$env:ASSISTANT_API_URL = "http://127.0.0.1:8000"
streamlit run ui/app.py
```

Open http://127.0.0.1:8501 and verify the health banner is absent when backend is up. Backend API docs: http://127.0.0.1:8000/docs.

## Tests

```powershell
python -m pytest -q tests/test_ui.py
python -m pytest -q
python -m ruff check .
```

**Known pending work:** `tests/test_ui.py::test_format_sources` and `::test_status_note` will fail until Member 2 implements L1/L2 in `ui/logic.py`. Practice U2–U4 tests will fail until assigned separately. Do not mark these as passing prematurely. To run the practice tests, execute `python -m pytest -q test_hello_streamlit.py` from `lab07/practice` (or run from repo root with the test file path and adjust the AppTest file path as necessary).

## F1 manual acceptance check

1. Ask a valid question and wait for a response with a `request_id`.
2. Confirm 👍 and 👎 appear together.
3. Click 👎; the UI posts `rating=-1` to `/v1/feedback` and shows a thank-you toast.
4. Confirm the answer no longer offers rating buttons after rerun.
5. Confirm the feedback endpoint's response with backend logs/API tests. The starter UI currently records the vote locally even if `send_feedback` returns false; a follow-up hardening task can change this behavior if required.

## Collaboration

Merge setup PR first. Members 1 and 2 should branch from updated `main`; Member 3 owns `ui/app.py`, Member 1 owns `ui/api_client.py`, Member 2 owns `ui/logic.py`. M4/M5/M6 use the worksheets and UI for validation after integration.
