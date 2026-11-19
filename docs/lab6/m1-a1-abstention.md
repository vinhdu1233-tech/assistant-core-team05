# Lab 6 — M1 A1: safe abstention (Issue #46)

Base: `setup/lab06-rag` (PR #48). Reference: tutorial Part E, p. 13; H2 p. 19.

## Implementation
- Search the configured index for the top k results.
- If no hits exist OR the best score is strictly below `self.min_score`, immediately return `ESCALATE_MSG` with `Intent.UNKNOWN`, `path="abstain"`, `escalate=True`, `confidence=0.0`, no sources and no degraded answer.
- Guard runs before constructing the prompt, calling the LLM or executing model-requested tools. Applies to both retrieval-only and LLM routes.
- At or above the threshold, keep the original source quotation / generation / provider fallback behavior. Threshold is configurable. The post-merge follow-up keeps BM25 at 2.0 and gives TF-IDF/Hybrid separate cosine defaults.

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

## Post-merge follow-up to PR #49

PR #49 was merged before the reviews from M5/M6/M3. The follow-up changes are on a new branch from integrated main, for team review (not a direct main edit).

| Retrieval mode | Score used for abstention | Default minimum |
| --- | --- | --- |
| BM25 | Original BM25 relevance; not a probability | 2.0 (tutorial) |
| TF-IDF | Cosine similarity, 0 to 1 | 0.25 |
| Hybrid | Cosine relevance of the RRF-ranked item, 0 to 1 | 0.25 |

Hybrid keeps reciprocal-rank fusion (RRF) for ordering, but no longer returns a mixture of BM25 and cosine scores when deciding whether to abstain. Rank-only RRF scores are not calibrated evidence scores. A1 checks the first ranked hit, as specified in the tutorial; it does not choose a different source if the first hit is weak.

Leave RETRIEVAL_MIN_SCORE unset/blank to pick the mode default. Explicit numeric overrides are honored; a value above 1 is rejected for cosine modes instead of silently making all questions abstain. Existing configurations explicitly setting 2.0 must remove that setting (or use a cosine-range override) when switching modes. Invalid negative/non-finite thresholds are rejected, and a non-finite top score fails closed before LLM or tools. The 0.25 default is a provisional engineering choice for this small sample KB, not a universal calibrated threshold or a guarantee against hallucinations.

New tests exercise full service construction with each mode, direct answerer defaults, weak/no-hit and boundary cases, explicit env overrides, invalid configurations, homogeneous Hybrid scoring and real known-source queries. BM25 behavior is preserved. Reviewers raised a broader retrieval limitation: a high lexical score can still be off-topic (e.g. E19), which requires better retrieval/answer evaluation rather than claiming that A1 proves semantic grounding.
