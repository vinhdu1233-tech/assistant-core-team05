# Lab 06 – Path Comparison

## 1. Objective

This comparison evaluates three assistant paths:

- Deterministic: uses routing and tools without retrieval-based document answers.
- Retrieval: uses routing, tools, and document retrieval without an LLM.
- LLM: uses routing, retrieval, and an LLM provider with structured output.

The purpose is to compare correctness, abstention behavior, and response latency.

## 2. Evaluation Method

The evaluation uses 25 cases from `eval/cases.jsonl`, including normal questions, paraphrases, and ambiguous or out-of-scope questions.

The benchmark measures:

- Correctness: number of responses satisfying the expected source, expected content, or abstention condition.
- Abstention OK: number of correctly handled abstention cases.
- P50 latency: median response time in milliseconds.
- Maximum latency: highest measured response time in milliseconds.

Command:

`python eval/compare_paths.py`

The benchmark was run locally using the `stub` LLM provider.

## 3. Results

| Path | Correct | Abstain OK | P50 (ms) | Max (ms) |
|---|---:|---:|---:|---:|
| Deterministic | 9/25 (36%) | 7/7 (100%) | 0.1 | 1.7 |
| Retrieval | 18/25 (72%) | 6/7 (85.7%) | 0.1 | 0.3 |
| LLM (stub) | 18/25 (72%) | 6/7 (85.7%) | 0.1 | 13.6 |

### Failed cases

- Deterministic: E01, E02, E05, E06, E07, E08, E09, E10, E11, E12, E13, E14, E15, E21, E22, E23.
- Retrieval: E02, E12, E13, E14, E15, E19, E22.
- LLM (stub): E02, E12, E13, E14, E15, E19, E22.

## 4. Comparison and Discussion

### Deterministic Path

The deterministic path achieved 9/25 correct responses (36%) and correctly handled all 7 abstention cases.

Its main strength is predictable behavior and low latency. However, without retrieval-based document answers, it cannot handle many handbook, fee, and campus-service questions.

### Retrieval Path

The retrieval path achieved 18/25 correct responses (72%), an improvement of 36 percentage points over the deterministic path.

It provides document-based answers without requiring an LLM. However, it failed seven cases, including several paraphrased or multi-part questions.

The knowledge base contains the expected information for these cases. For example, F26#2 contains the retake fee, H26#4.2 contains the final-year retake deadline, and S26#1 contains library borrowing rules. These failures therefore require further investigation of retrieval relevance, source selection, and answer evaluation.

### LLM Path

The LLM stub achieved the same correctness and abstention results as the retrieval path: 18/25 and 6/7, respectively.

Its maximum latency was 13.6 ms, compared with 0.3 ms for retrieval. This result reflects the local stub provider and must not be interpreted as the performance of a production LLM.

The LLM path did not improve the measured correctness in this benchmark.

### Abstention Analysis

The deterministic path correctly handled all seven expected-abstention cases.

Both retrieval and LLM (stub) handled six out of seven correctly. E19 asks whether the final exam is open-book, but the knowledge base does not specify this information. This case should be investigated to determine why the system did not abstain as expected.

## 5. Limitations

- The benchmark was conducted locally and latency may vary across environments.
- The LLM provider was `stub`, not a live production model.
- The current results represent one benchmark run.
- Failed cases have not yet been individually diagnosed at the retrieval and response-generation levels.

## 6. Conclusion

Retrieval and LLM (stub) achieved higher correctness than the deterministic path, with both reaching 72% compared with 36%.

The deterministic path achieved the strongest abstention result at 100%, while retrieval and LLM (stub) reached 85.7%.

The LLM stub did not improve correctness over retrieval and showed a higher maximum latency in this run. Further investigation is needed to improve retrieval performance and ensure correct abstention when the knowledge base does not contain sufficient evidence.

Overall, retrieval provides a substantial improvement for document-based questions, while reliable abstention and source selection remain important areas for improvement.
