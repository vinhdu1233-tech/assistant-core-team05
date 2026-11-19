# Lab 06 – Path Comparison

## 1. Objective

This comparison evaluates three assistant paths:

- **Deterministic:** uses routing and tools without retrieval-based document answers.
- **Retrieval:** uses routing, tools, and document retrieval without an LLM.
- **LLM:** uses routing, retrieval, and an LLM provider with structured output.

The purpose is to compare correctness, abstention behavior, and response latency, and to identify areas that need improvement.

## 2. Evaluation Method

The evaluation uses two datasets:

- **Original baseline:** 20 evaluation cases from the original `eval/cases.jsonl` at commit `3ed41c1`.
- **Extended evaluation:** 25 cases, including the five additional M5 H1 cases.

The 20-case baseline is reported separately to preserve comparability with the original evaluation. The 25-case results are included as supplemental results.

The benchmark measures:

- **Correctness:** number of responses satisfying the expected source, expected content, or abstention condition.
- **Abstention OK:** number of correctly handled abstention cases.
- **P50 latency:** median response time in milliseconds.
- **Maximum latency:** highest measured response time in milliseconds.

Command:

`python eval/compare_paths.py`

The benchmark was run locally using the `stub` LLM provider. Latency values represent one local benchmark run.

## 3. Results

### 3.1 Original 20-Case Baseline

| Path | Correct | Abstain OK | P50 (ms) | Max (ms) |
|---|---:|---:|---:|---:|
| Deterministic | 7/20 (35%) | 5/5 (100%) | 0.0 | 1.0 |
| Retrieval | 14/20 (70%) | 4/5 (80%) | 0.1 | 0.2 |
| LLM (stub) | 14/20 (70%) | 4/5 (80%) | 0.2 | 2.9 |

**Failed cases**

- Deterministic: E01, E02, E05, E06, E07, E08, E09, E10, E11, E12, E13, E14, E15.
- Retrieval: E02, E12, E13, E14, E15, E19.
- LLM (stub): E02, E12, E13, E14, E15, E19.

### 3.2 Extended 25-Case Evaluation

| Path | Correct | Abstain OK | P50 (ms) | Max (ms) |
|---|---:|---:|---:|---:|
| Deterministic | 9/25 (36%) | 7/7 (100%) | 0.1 | 1.7 |
| Retrieval | 18/25 (72%) | 6/7 (85.7%) | 0.1 | 0.3 |
| LLM (stub) | 18/25 (72%) | 6/7 (85.7%) | 0.1 | 13.6 |

**Failed cases**

- Deterministic: E01, E02, E05, E06, E07, E08, E09, E10, E11, E12, E13, E14, E15, E21, E22, E23.
- Retrieval: E02, E12, E13, E14, E15, E19, E22.
- LLM (stub): E02, E12, E13, E14, E15, E19, E22.

### 3.3 Results Comparison

The extended evaluation shows a small increase in correctness for all paths compared with the original baseline:

- Deterministic increased from 35% to 36%.
- Retrieval increased from 70% to 72%.
- LLM (stub) increased from 70% to 72%.

The additional cases do not change the overall ranking of the three paths. Retrieval and LLM (stub) remain ahead of the deterministic path.

The 25-case results are supplemental and do not replace the original 20-case baseline.

## 4. Comparison and Discussion

### 4.1 Deterministic Path

The deterministic path achieved 7/20 correct responses (35%) on the original baseline and 9/25 (36%) on the extended evaluation.

Its main strength is predictable behavior, low latency, and reliable abstention. It correctly handled all expected-abstention cases in both datasets.

However, without retrieval-based document answers, it cannot reliably handle many handbook, fee, and campus-service questions.

### 4.2 Retrieval Path

The retrieval path achieved 14/20 correct responses (70%) on the original baseline and 18/25 (72%) on the extended evaluation.

It provides document-based answers without requiring an LLM and substantially outperformed the deterministic path in correctness.

However, its failures show that retrieving a related document is not sufficient. The retrieved source must directly support the requested information. Relevance checks and abstention safeguards are particularly important when multiple handbook sections contain overlapping terms.

### 4.3 LLM Path

The LLM stub achieved the same correctness and abstention results as the retrieval path:

- 14/20 correct on the original baseline.
- 18/25 correct on the extended evaluation.

Its maximum latency was 2.9 ms on the baseline and 13.6 ms on the extended evaluation. These measurements reflect the local stub provider and must not be interpreted as production LLM performance.

The LLM path did not improve measured correctness over retrieval. In particular, it did not correct the wrong-source cases observed in the retrieval path.

Therefore, this benchmark does not demonstrate a measurable accuracy benefit from adding the LLM stub.

### 4.4 Recommendation for Handbook Questions

**The Retrieval path is the recommended default for handbook questions.**

It achieved 70% correctness on the original 20-case baseline, compared with 35% for the deterministic path. It can retrieve handbook sections and provide source references without depending on an LLM.

The LLM stub achieved the same 70% correctness but did not improve the measured results. Its maximum latency was also higher in this benchmark run.

However, retrieval should be used with stronger relevance checks and abstention safeguards before being relied on for unsupported or ambiguous questions. A response should only be generated when the retrieved evidence directly supports the requested information.

The deterministic path remains useful for predictable tool-based operations and cases where reliable abstention is more important than answering a broad handbook question.

## 5. Analysis of Selected Failed Cases

The following cases were examined using diagnostic output from all three paths.

### E13 – Tuition Due Date

**Question:** `when is tuition due`

**Expected source:** `F26#3`

All three paths routed the question to the deterministic fee intent and returned:

`Credit count must be positive.`

No handbook source was retrieved.

This indicates a routing error: the system interpreted a tuition due-date question as a fee calculation, which requires a positive credit count. The retrieval and LLM paths did not reach document retrieval because the question was handled by the fee route.

**Suggested improvement:** distinguish tuition due-date or payment-status questions from fee amount and credit-based calculation questions. Due-date questions should be routed to the relevant handbook or fee-policy source.

### E14 – Credit Limit

**Question:** `can I take 32 credits`

**Expected source:** `H26#6.1`

The deterministic path abstained.

The retrieval and LLM paths both selected `H26#7.2`, a section about medical absence from a final exam, instead of the expected credit-limit section. The LLM path therefore propagated the same incorrect source selected by retrieval.

This is a retrieval relevance and source-selection error. The returned section does not support the requested credit-limit information.

**Suggested improvement:** improve retrieval ranking for credit-limit questions and verify that the selected source directly addresses the requested credit quantity and policy.

### E15 – Library Borrowing Duration

**Question:** `how long can I keep a library book`

**Expected source:** `S26#1`

All three paths routed the question to the deterministic office intent and returned:

`Library: room B.201, open Mon-Sat 07:00-20:00`

No library borrowing-policy source was retrieved.

This indicates a routing error: the system interpreted a question about borrowing duration as a request for library location or opening hours.

**Suggested improvement:** distinguish library service-policy questions, such as borrowing duration and renewal rules, from library location and opening-hour questions. Borrowing-policy questions should retrieve `S26#1`.

### E19 – Unsupported Open-Book Exam Question

**Question:** `is the final exam open-book`

**Expected behavior:** abstain because the knowledge base does not specify whether the final exam is open-book.

The deterministic path abstained correctly.

However, retrieval and LLM selected `H26#7.2`, which describes medical absence from a final exam and the required medical certificate procedure. Although the source contains the phrase "final exam", it does not answer whether the exam is open-book.

Both paths therefore returned information that was related to the question's wording but did not support the requested claim.

This is an evidence-relevance and abstention failure. Lexical overlap with a handbook section should not be treated as sufficient evidence for an answer.

**Suggested improvement:** require direct evidence that supports the specific question before generating an answer. If no relevant source establishes the open-book policy, the system should abstain rather than return an unrelated exam regulation.

## 6. Priority for Further Improvement

**E19 should be fixed first.**

The reason is the risk of providing unsupported academic-policy information. E13 and E15 are routing errors, while E14 is a wrong-source retrieval error. E19 is especially concerning because the system produces an answer even though the knowledge base does not contain evidence for the requested policy.

A wrong answer about exam conditions could mislead students. Improving abstention and evidence validation for E19 would therefore be a higher priority than improving answer coverage alone.

The recommended first improvement is to verify that retrieved evidence directly answers the user's question. When the evidence is merely related or does not establish the requested fact, the assistant should abstain.

## 7. Limitations

- The benchmark was conducted locally, and latency may vary across environments.
- The LLM provider was `stub`, not a live production model.
- Latency values represent one benchmark run and should not be treated as statistically stable performance estimates.
- The original 20-case baseline and extended 25-case evaluation are reported separately to preserve comparability.
- The selected failed cases were investigated using diagnostic outputs; the proposed improvements are recommendations and have not yet been validated by a new benchmark run.

## 8. Conclusion

The original 20-case baseline shows that retrieval and LLM (stub) both achieved 70% correctness, compared with 35% for the deterministic path. The extended 25-case evaluation shows a similar result: 72% for retrieval and LLM (stub), compared with 36% for deterministic.

The deterministic path achieved the strongest abstention performance, correctly handling all expected-abstention cases. Retrieval and LLM (stub) each failed one abstention case in both evaluations.

Retrieval is the recommended default for handbook questions because it improves correctness and provides source-based answers without requiring an LLM. The LLM stub did not demonstrate an accuracy improvement in this benchmark.

The main remaining challenge is ensuring that retrieved evidence directly supports the user's question. E13 and E15 require better routing, E14 requires improved source relevance, and E19 requires stronger evidence validation and abstention.

The first priority should be fixing E19 to prevent unsupported academic-policy answers. Overall, retrieval provides a substantial improvement over deterministic routing, but reliable source selection and abstention remain essential for a trustworthy assistant.
