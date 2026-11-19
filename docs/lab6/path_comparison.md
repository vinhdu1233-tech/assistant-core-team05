# Lab 06 – Path Comparison

## 1. Objective

This comparison evaluates three assistant paths:

- Deterministic: uses routing and tools without retrieval-based document answers.
- Retrieval: uses routing, tools, and document retrieval without an LLM.
- LLM: uses routing, retrieval, and an LLM provider with structured output.

The purpose is to compare correctness, abstention behavior, and response latency.

## 2. Evaluation Method

The original baseline uses E01–E20, and the expanded H1 benchmark uses E01–E25 from `eval/cases.jsonl`, including normal questions, paraphrases, and ambiguous or out-of-scope questions. Both are now run separately in CI.

The benchmark measures:

- Correctness: number of responses satisfying the expected source, expected content, or abstention condition.
- Abstention OK: number of correctly handled abstention cases.
- P50 latency: median response time in milliseconds.
- Maximum latency: highest measured response time in milliseconds.

Command:

`python eval/compare_paths.py --first 20` (baseline) and `python eval/compare_paths.py --first 25` (expanded)

Both runs below used the local `stub` LLM provider. The two result sets are kept separate because E21–E23 were revised to test distinct facts; the scores are not interchangeable.

## 3. Results by benchmark version

### Run A — Earlier 25-case wording

This is the earlier comparison recorded before the E21–E23 wording revision.

### Original E01–E20 baseline

Measured independently in GitHub Actions CI [run #44541714180](https://github.com/vinhdu1233-tech/assistant-core-team05/actions/runs/44541714180) using `LLM_PROVIDER=stub` and `python eval/compare_paths.py --first 20`:

| Path | Correct (E01–E20) | Abstain OK | P50 (ms) | Max (ms) |
|---|---:|---:|---:|---:|
| Deterministic | 7/20 (35%) | 5/5 (100%) | 0.0 | 1.0 |
| Retrieval | 14/20 (70%) | 4/5 (80%) | 0.1 | 0.1 |
| LLM (stub) | 14/20 (70%) | 4/5 (80%) | 0.1 | 0.4 |

### Expanded E01–E25 benchmark

| Path | Correct | Abstain OK | P50 (ms) | Max (ms) |
|---|---:|---:|---:|---:|
| Deterministic | 9/25 (36%) | 7/7 (100%) | 0.1 | 1.7 |
| Retrieval | 18/25 (72%) | 6/7 (85.7%) | 0.1 | 0.3 |
| LLM (stub) | 18/25 (72%) | 6/7 (85.7%) | 0.1 | 13.6 |

### Run B — Revised E21–E23 wording (current M5 benchmark)

E21–E23 were revised to test the thesis-registration window, the library-renewal restriction when another student has reserved a book, and the student-card replacement fee/location. E01–E20 remain unchanged. The current dataset still contains 25 cases.

| Path | Correct | Abstain OK | P50 (ms) | Max (ms) |
|---|---:|---:|---:|---:|
| Deterministic | 9/25 (36%) | 7/7 (100%) | 0.0 | 1.1 |
| Retrieval | 17/25 (68%) | 6/7 (85.7%) | 0.1 | 0.1 |
| LLM (stub) | 17/25 (68%) | 6/7 (85.7%) | 0.1 | 0.3 |

Run B is the result to use when reporting the current revised `eval/cases.jsonl`. The one-case decrease from Run A (18/25 to 17/25 for retrieval and LLM) must not be hidden or presented as a like-for-like rerun: the wording and fact coverage of E21–E23 changed between benchmark versions. The latency figures are run-specific and should not be treated as a controlled performance comparison across environments.

## 4. Failed cases and discussion

### Deterministic Path

The deterministic path achieved 9/25 correct responses (36%) and correctly handled all 7 abstention cases in both recorded runs.

Its main strength is predictable behavior and low latency. However, without retrieval-based document answers, it cannot handle many handbook, fee, and campus-service questions. In the revised run, it also does not retrieve the KB facts tested by E21–E23.

### Retrieval Path

The earlier run failed E02, E12, E13, E14, E15, E19 and E22. In the revised run, the failed cases are E02, E12, E13, E14, E15, E19, E22 and E23.

The revised run therefore retains the six earlier retrieval/LLM failures and additionally misses E23. E22 expects source `S26#1` (library renewal); E23 expects `S26#3` (student-card replacement). The evaluation output establishes that the expected source IDs were not returned, but it does not expose enough retrieval candidates or answer detail to determine whether the cause is query matching, ranking, or later answer handling.

### LLM Path

The LLM stub matched retrieval correctness and abstention in both recorded runs: 18/25 in Run A and 17/25 in Run B.

Its maximum latency was higher than retrieval in both runs, but these measurements use the local stub provider. They must not be interpreted as production LLM latency or quality.

### Abstention Analysis

The deterministic path correctly handled all seven expected-abstention cases.

Both retrieval and LLM (stub) handled six out of seven correctly in the revised run. E19 asks whether the final exam is open-book, but the knowledge base does not specify this information. This case should be investigated to determine why the system did not abstain as expected.

### Required case-by-case analysis

- **E13 (tuition due vs paid):** The question asks about a deadline (`F26#3`), not a fee calculation. Lexical routing/retrieval can conflate tuition payment dates with tuition amounts; the expected source is not returned.
- **E14 (credit vs credits):** The question asks whether 32 credits are allowed (`H26#6.1`). The singular/plural wording and the number can trigger an inappropriate fee/tool route or miss the relevant enrollment policy. The expected source is not returned.
- **E15 (library loan duration):** The question is about borrowing policy (`S26#1`), not the physical location of the library. Office routing can intercept it before RAG retrieval.
- **E19 (open-book exam):** The KB discusses exams but does not establish whether this particular exam is open-book. A lexically related source is not sufficient evidence, so retrieval/LLM should abstain rather than cite it.
- **E22 (multi-part library request):** The question combines borrowing limit, duration, and renewal; office/library location routing or a nonmatching top chunk prevents the expected `S26#1` citation. It is part of the 25-case expansion only.

**Recommended path for handbook questions:** Use retrieval with grounded citations as the practical baseline: it reaches 14/20 on the original cases and 18/25 on the expanded cases, while avoiding an external LLM dependency. The local LLM stub adds no measured accuracy in this experiment. Keep deterministic tools for actual fee calculations and privacy refusals.

**First failure to fix:** E15, because a library-policy query is easily confused with a library-location request by the intent router; correcting this distinction should also help the expanded E22. This recommendation is based on the documented failures and code routing, not a claim that a fix has already been verified.

## 5. Limitations

- The benchmark was conducted in CI/local environments; latency varies across environments and runs.
- The LLM provider was `stub`, not a live production model.
- The results represent two benchmark versions, not a controlled experiment changing only one implementation variable.
- Failed cases have not yet been individually diagnosed at the retrieval and response-generation levels.
- The comparison script reports failed case IDs and aggregate metrics, but does not currently print retrieved candidates or answer text for each failure.

## 6. Conclusion

For the current revised 25-case benchmark (Run B), retrieval and LLM (stub) each achieved 17/25 correct responses (68%), while the deterministic path achieved 9/25 (36%). The deterministic path handled all seven abstention cases; retrieval and LLM (stub) handled six.

The earlier 18/25 result belongs to Run A, before E21–E23 were revised, and should be retained only as historical context. Final reporting should use Run B for the current dataset and explicitly identify the benchmark version.

The LLM stub did not improve correctness over retrieval. E22 and E23 remain unresolved source-selection failures, and reliable abstention for E19 remains an area for improvement.
