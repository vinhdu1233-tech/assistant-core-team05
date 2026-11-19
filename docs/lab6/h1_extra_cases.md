# Lab 6 — M5 H1: five additional evaluation cases (Issue #45)

## Added cases

The original E01–E20 cases are preserved. This change keeps exactly five additional cases, E21–E25, for 25 unique cases total.

| ID | Category | Question focus | Expected behavior |
|---|---|---|---|
| E21 | normal | Thesis registration opening and closing weeks | Cite `H26#5.3` |
| E22 | normal | Whether an online library renewal is allowed when another student has reserved the book | Cite `S26#1` |
| E23 | normal | Lost student-card replacement fee and application location | Cite `S26#3` |
| E24 | out-of-scope | Advice on learning calculus | Abstain; this topic is not covered by the student-services KB |
| E25 | privacy | Request for another student's GPA | Abstain; the request seeks another student's private academic record |

## Review follow-up: improve question diversity

The reviewer noted that the first wording of E21–E23 was too close to existing E01, E15 and E05. I narrowed the new questions to different facts within the same verified KB sections:

- E21 tests the thesis-registration window (week 1 through week 3), rather than repeating E01's accumulated-credit threshold.
- E22 tests the renewal restriction when another student has reserved the book, rather than repeating E15's loan duration.
- E23 tests the replacement fee and application location, rather than repeating E05's generic lost-card query.

This keeps the three verified source IDs while testing distinct facts. E01–E20 are unchanged.

## Source-ID verification

The three expected source IDs were checked against the actual Markdown knowledge base in `data/kb/`:

- `H26#5.3` is the thesis-registration section in `handbook_2026.md`. It states that registration opens in week 1 and closes in week 3.
- `S26#1` is the library-borrowing section in `services_2026.md`. It states that a book can be renewed once online only if no one else has reserved it.
- `S26#3` is the student-card replacement section in `services_2026.md`. It states that replacement costs 50,000 VND and is handled at Student Affairs (room I.102), with the new card ready in 3 working days.

The IDs follow the chunker convention `{doc_id}#{heading number}` and are present in the starter KB. E24 has no relevant KB section. E25 is also covered by the deterministic privacy guard before retrieval.

## Comparison run

The required command, run in CI with `LLM_PROVIDER=stub`, is:

```bash
python eval/compare_paths.py
```

The revised-wording comparison completed successfully:

| Path | Correct | Abstain OK | P50 (ms) | Max (ms) |
|---|---:|---:|---:|---:|
| deterministic | 9/25 | 7/7 | 0.0 | 1.1 |
| retrieval | 17/25 | 6/7 | 0.1 | 0.1 |
| llm (stub) | 17/25 | 6/7 | 0.1 | 0.3 |

**New cases E21–E25:** E21, E24 and E25 passed in retrieval/LLM. E22 and E23 failed in both retrieval and LLM: the evaluation did not find the expected source ID (`S26#1` for E22 and `S26#3` for E23) in the returned sources. The comparison script reports failing case IDs but does not print retrieved candidates or answer text, so this run establishes the missing expected-source result but does not establish whether the cause was query matching, ranking, or later answer handling. The deterministic path failed E21–E23 because it does not retrieve KB documents, and correctly abstained on E24–E25.

**Failures to investigate first:** E22 and E23 are the two new normal cases that retrieval/LLM still miss. E22 is the first priority because it tests a conditional rule (renewal is allowed only when no one else has reserved the book); E23 is next because it asks for both the replacement fee and the application location. The current evaluation output does not provide enough diagnostic detail to attribute either failure to a specific retrieval or generation component.

Other retrieval/LLM failures were E02, E12, E13, E14, E15 and E19. E19 is an ambiguous exam question that should abstain but does not.

CI run: [run #44514048519](https://github.com/vinhdu1233-tech/assistant-core-team05/actions/runs/44514048519), commit `1c4f9b18ed22c244d6c83b83b6c74beb1c65fff4`. It reported **173 passed, 1 warning**, with Ruff lint and Ruff format checks passing. The comparison completed successfully in stub mode. These latency values are specific to the GitHub Actions runner and local stub; they should not be generalized to a production LLM.

## Validation performed

- Confirmed that the dataset contains 25 non-empty JSONL records.
- Confirmed that all 25 IDs are unique and E21–E25 are the five additional cases.
- Confirmed that exactly three new cases use `expect_source` and exactly two use `expect_abstain: true`.
- Confirmed the three expected source IDs and targeted facts against the actual KB files.
- CI passed all 173 tests; Ruff lint and Ruff format passed.
