# Lab 06 — Team 05 integration guide (M3)

Source: [CSC10014 public_materials / lab06](https://github.com/CSC10014-at-fit-hcmus/public_materials/tree/main/lab06)

## Integration branch and safety

Base: `main` (Lab 05), integration branch: `setup/lab06-rag`.
We ported the **new** RAG modules, document KB, evaluation scripts, structured LLM adapter, and response/config fields from the instructor's starter while **retaining Team 05's** customized Python API, DB persistence, weather endpoint, rate limiter, and previous tests. Do not replace `src/assistant_api/main.py`, `db.py`, `router.py`, or `knowledge.py` wholesale with instructor starter copies.

For no-cost offline use, keep `LLM_PROVIDER=stub` and `RETRIEVAL_KIND=bm25`; Ollama is optional. Never commit `.env`, API keys, real student data or `assistant.db`.

## Members and file ownership

| Member | Issue | Main ownership |
|---|---|---|
| M1 @vinhdu1233-tech | #46 | A1 in `src/assistant_core/rag/answerer.py` |
| M2 @TuanTu2205 | #42 | Part C search notes: `docs/lab6/part_c_retrieval.md` |
| M3 @tree312-coder | #47 | setup, S1–S3, integration and regression |
| M4 @dmdung2520 | #43 | A2 in `src/assistant_core/llm.py` |
| M5 @fumeneko | #45 | H1 in `eval/cases.jsonl`, `docs/lab6/h1_extra_cases.md` |
| M6 @lnmthi | #44 | F comparison in `docs/lab6/path_comparison.md` |

Create feature branches **from** `setup/lab06-rag`, and open PRs **into** `setup/lab06-rag`; do not target old main before team integration. The starter A1/A2 TODOs remain intentionally uncompleted in this setup PR for M1/M4.

## Setup / validation (Windows PowerShell)

```powershell
git fetch origin
git switch setup/lab06-rag
py -m pip install -r requirements.txt
py -m pip install -e .
py -m pytest -q practice/test_mini_search.py
py -m pytest -q tests/test_rag.py
py -m pytest -q
py -m ruff check .
py -m ruff format --check .
py eval/compare_paths.py
```

The RAG tests for A1 and A2 **will fail until M1 and M4 submit their PRs**. Run the final full suite only after both are integrated. Keep the original 20 evaluation cases intact before M5 extends the dataset. Record actual measured output, not the tutorial's example numbers.

Review whether `KB_DIR` resolves from the repo root. Always run `eval/compare_paths.py` from that root, not `eval/`. After all PRs are reviewed and checks are green, merge the integrated work to `main`. Member 1 can then publish the `v0.6-ai` tag.

H2 reflection is a **must** in the tutorial; each member should provide their own five-line explanation.
