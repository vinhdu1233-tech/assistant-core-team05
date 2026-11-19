# Lab 6 — M1 A1: safe abstention (Issue #46)

Base: `setup/lab06-rag` (PR #48). Reference: tutorial Part E, p. 13; H2 p. 19.

## Implementation
- Search the configured index for the top k results.
- If no hits exist OR the best score is strictly below `self.min_score`, immediately return `ESCALATE_MSG` with `Intent.UNKNOWN`, `path="abstain"`, `escalate=True`, `confidence=0.0`, no sources and no degraded answer.
- Guard runs before constructing the prompt, calling the LLM or executing model-requested tools. Applies to both retrieval-only and LLM routes.
- At or above the threshold, keep the original source quotation / generation / provider fallback behavior. Threshold is configurable (BM25 default 2.0); TF-IDF scores use a different scale.

## Verification matrix

| Check | Evidence |
| --- | --- |
| No results; zero / low score; several weak hits | Parameterized focused tests with and without a model |
| No LLM, prompt or tool invocation | Spy/mock assertions |
| Exact threshold and above; configurable threshold | Parameterized tests; valid answer retains source |
| Real BM25 / out-of-scope and student card | Official sample KB, offline StubLLM |
| Privacy guard | Three sample private queries; search and LLM never called |
| Deterministic tuition | 18 normal credits and 2 retake credits under default rates; no search or LLM |
| Escalation output | Message, path, intent, confidence, sources, flag checks |

Run from repo root:
```bash
python -m pytest -q tests/test_lab06_abstain.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

The original tests are unchanged. M4 owns A2 citation validation in `llm.py`; if it remains a TODO, the official citation test may fail in the full suite independently of A1. Do not suppress it to make CI green.

## Scope and handoff
H2 individual reflection is in `docs/lab6/h2_m1.md`. S1–S3, Part C, A2, H1 and the final Part F comparison are assigned to other members. M3 integrates and reviews PRs; M1 publishes `v0.6-ai` only after final reviewed integration into main and green CI (tutorial pp. 18 and 20). No release tag or merge is made in this feature PR. AI assistance used to implement, test and document; verify the reflection before LMS submission.
