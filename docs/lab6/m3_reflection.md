# Lab 06 — H2 Reflection (M3)

1. RAG is like an open-book exam: before answering, the assistant searches the approved documents for relevant evidence.
2. It finds matching sections using a retrieval index instead of relying on a language model's memory.
3. The language model can phrase a readable answer using those retrieved sections, but it must not invent deadlines or rules.
4. Our code checks that every cited source ID was actually retrieved; it also rejects malformed answers.
5. When no sufficiently relevant source exists, our code should abstain and refer the student to a human rather than guess.
