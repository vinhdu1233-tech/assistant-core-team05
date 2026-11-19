# Lab 06 — Part C: Knowledge Base and BM25 Retrieval

**Member:** M2 — TuanTu2205  
**Issue:** #42

## 1. Knowledge Base and Metadata

The Lab 06 knowledge base is stored in `data/kb/` and contains three sample Markdown documents about student regulations, tuition fees, and campus services.

Each document contains metadata such as `doc_id`, `title`, `version`, and `owner`, which helps identify the source of information.

For example, the student handbook contains sections identified by `H26`, version `2026.1`, and owned by the Training Office. Campus service sections use `S26` and are owned by Student Affairs.

## 2. Document Chunking

The `load_folder()` function reads the Markdown documents and splits them into smaller sections called *chunks*.

The actual execution returned **14 chunks**.

Examples:

- `H26#5.3` — Thesis registration
- `H26#5.4` — Late thesis registration
- `S26#1` — Library borrowing
- `S26#2` — IT account password reset

Each chunk preserves its source ID, title, version, owner, and content.

Searching chunks instead of entire documents helps the assistant identify the specific section supporting an answer.

## 3. BM25 Retrieval

The retrieval index was created using:

`make_index("bm25", chunks)`

BM25 ranks chunks according to their relevance to the user's query. Its scoring considers keyword frequency, term rarity, and document length.

The tutorial uses `RETRIEVAL_MIN_SCORE=2.0` as the minimum relevance threshold.

### Tutorial Query

**Query:** `can I register my thesis with 118 credits`

| Rank | Chunk ID | Score |
|---|---|---:|
| 1 | H26#5.3 | 4.914 |
| 2 | H26#5.4 | 2.449 |

The first result is appropriate because section 5.3 explains thesis registration requirements.

### Three Original Queries

| Question | Top Chunk | BM25 Score | Relevance |
|---|---|---:|---|
| How can I reset my IT account password? | S26#2 | 10.311 | Relevant |
| How long may I borrow library books? | S26#1 | 8.719 | Relevant |
| What happens if I register my thesis late? | H26#5.4 | 4.899 | Relevant |

The three highest-ranked chunks match the intended topics.

However, some lower-ranked results are less relevant. For example, the library question also retrieved `F26#3` (Payment deadline) with score `0.852`. This shows that keyword-based retrieval can return unrelated chunks when some terms overlap.

A minimum-score threshold helps prevent weak matches from being used as evidence.

## 4. Out-of-Scope Question

**Query:** `what is the capital of France`

**Actual result:** `[]`

The knowledge base does not contain information about this question. The search returned no matching chunks.

In this situation, the assistant should abstain rather than invent an answer.

## 5. Observations and Conclusion

The BM25 retrieval successfully ranked the relevant section first in all three original queries.

Compared with the simple keyword-overlap approach in Part B, BM25 additionally considers term rarity and document length when ranking results.

Nevertheless, BM25 is primarily lexical retrieval. It may miss related meanings expressed with different words and may return weak matches.

Combining retrieval with a minimum-score threshold and answer validation makes the assistant more reliable.

## 6. Reproduction

All experiments were run from the repository root using:

- `load_folder(Path("data/kb"))`
- `make_index("bm25", chunks)`
- `idx.search(query, k=3)`

The scores reported above were obtained from actual Python execution on the Lab 06 integration starter.