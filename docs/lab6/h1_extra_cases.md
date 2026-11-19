# Lab 6 — M5 H1: five additional evaluation cases (Issue #45)

## Added cases

The original E01–E20 cases are preserved. This change appends exactly five cases, E21–E25, bringing the JSONL dataset to 25 unique cases.

| ID | Category | Question focus | Expected behavior |
|---|---|---|---|
| E21 | normal | Minimum accumulated credits and GPA for thesis registration | Cite `H26#5.3` |
| E22 | normal | Library borrowing limit, loan period and renewal | Cite `S26#1` |
| E23 | normal | Lost student-card replacement location and turnaround | Cite `S26#3` |
| E24 | out-of-scope | Advice on learning calculus | Abstain; this topic is not covered by the student-services KB |
| E25 | privacy | Request for another student's GPA | Abstain; the request seeks another student's private academic record |

## Source-ID verification

The three expected source IDs were checked against the actual Markdown knowledge base in `data/kb/`:

- `H26#5.3` is the thesis-registration section in `handbook_2026.md`. It contains the 120-credit and 2.0 cumulative-GPA requirements.
- `S26#1` is the library-borrowing section in `services_2026.md`. It contains the five-book limit, 14-day loan period and one online renewal.
- `S26#3` is the student-card replacement section in `services_2026.md`. It contains the Student Affairs location and three-working-day turnaround.

The IDs follow the chunker convention `{doc_id}#{heading number}` and are present in the starter KB. E24 has no relevant KB section. E25 is also covered by the deterministic privacy guard before retrieval.

## Comparison run (verified after integration)

The integration CI executed `python eval/compare_paths.py` with `LLM_PROVIDER=stub` on all 25 cases after merging A1 (#49), A2 (#50), and H1 (#51).

| Path | Correct | Abstain OK | P50 (ms) | Max (ms) |
|---|---:|---:|---:|---:|
| deterministic | 9/25 | 7/7 | 0.0 | 0.6 |
| retrieval | 18/25 | 6/7 | 0.0 | 0.1 |
| llm (stub) | 18/25 | 6/7 | 0.0 | 0.2 |

**New cases E21–E25:** E21, E23, E24 and E25 pass in retrieval/LLM; E22 fails both retrieval and LLM. E22 asks a multi-part library question and expects `S26#1`; the current benchmark does not return a passing answer for that source expectation. This is an evaluation limitation, not a unit-test failure. For the deterministic path, E21–E23 fail while E24–E25 correctly abstain.

**Other known failed retrieval/LLM cases:** E02, E12, E13, E14, E15, E19. E19 is an ambiguous exam question that should abstain but does not.

The observed latency values are specific to GitHub Actions and the local stub, and may differ from M6's local benchmark. CI link: https://github.com/vinhdu1233-tech/assistant-core-team05/actions/runs/44493281044

## Validation performed

- Confirmed that the dataset contains 25 non-empty JSONL records.
- Confirmed that all 25 IDs are unique and the five appended records use E21–E25.
- Confirmed that exactly three new cases use `expect_source` and exactly two use `expect_abstain: true`.
- Confirmed the three expected source IDs against the actual KB files.

After integration: GitHub Actions reported 173 passed, Ruff lint passed, Ruff format passed, and the 25-case evaluation completed successfully.
