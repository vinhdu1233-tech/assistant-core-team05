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

## Comparison run

The requested command is:

```bash
python eval/compare_paths.py
```

**Run status: blocked on integration of A1 and A2.** At the time this change was prepared, the feature branch is based on `setup/lab06-rag`, where `RagAnswerer.answer()` still contains the A1 `NotImplementedError` for empty results and `parse_draft()` still contains the A2 grounding TODO. The corresponding implementation PRs are #49 (M1/A1) and #50 (M4/A2); neither change is part of this M5 branch. Running the comparison against this branch before those changes are integrated cannot produce a valid final comparison table. I have not inserted guessed accuracy or latency figures.

After #49 and #50 are merged into `setup/lab06-rag`, update this feature branch from the integration branch, run the command above from the repository root with `LLM_PROVIDER=stub`, and replace this note with the actual output table. The explanation must identify any failed E21–E25 cases and the reason. The original E01–E20 data must remain unchanged.

## Validation performed

- Confirmed that the dataset contains 25 non-empty JSONL records.
- Confirmed that all 25 IDs are unique and the five appended records use E21–E25.
- Confirmed that exactly three new cases use `expect_source` and exactly two use `expect_abstain: true`.
- Confirmed the three expected source IDs against the actual KB files.

Full evaluation and repository test/Ruff commands remain pending the A1/A2 integration noted above.
