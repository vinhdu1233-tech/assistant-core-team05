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

The required command is:

```bash
python eval/compare_paths.py
```

The integration run on the *previous wording* completed in stub mode on all 25 cases:

| Path | Correct | Abstain OK | P50 (ms) | Max (ms) |
|---|---:|---:|---:|---:|
| deterministic | 9/25 | 7/7 | 0.0 | 0.6 |
| retrieval | 18/25 | 6/7 | 0.0 | 0.1 |
| llm (stub) | 18/25 | 6/7 | 0.0 | 0.2 |

In that run, E21, E23, E24 and E25 passed in retrieval/LLM; E22 failed both because its original multi-part question did not produce the expected `S26#1` source. The deterministic path failed E21–E23, as expected for a path that does not retrieve KB documents, and correctly abstained on E24–E25. The other retrieval/LLM failures were E02, E12, E13, E14, E15 and E19; E19 is an ambiguous exam question that should abstain but did not.

That earlier run was recorded by integration CI [run #44493281044](https://github.com/vinhdu1233-tech/assistant-core-team05/actions/runs/44493281044), commit `001e361e97069c7636930d58a3f3ac234eca751b`. These figures are retained as historical results only: E21–E23 have since been made more specific, so they are not the final results for the revised wording.

**Revised-wording comparison:** pending the CI run for this follow-up branch. The table and failure analysis above will be updated with that run's actual output before this follow-up is considered complete.

## Validation performed

- Confirmed that the dataset contains 25 non-empty JSONL records.
- Confirmed that all 25 IDs are unique and E21–E25 are the five additional cases.
- Confirmed that exactly three new cases use `expect_source` and exactly two use `expect_abstain: true`.
- Confirmed the three expected source IDs and targeted facts against the actual KB files.
- The integration CI run above reported 173 tests passed, Ruff lint passed, and Ruff format passed. The revised-wording CI validation is pending.
