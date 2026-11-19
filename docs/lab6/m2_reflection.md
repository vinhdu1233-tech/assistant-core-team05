# Lab 06 — H2 Reflection (M2)

1. RAG works like an open-book exam because the assistant searches reliable documents before answering a question.
2. The retrieval system finds relevant document chunks instead of relying entirely on the language model's memory.
3. The language model uses these retrieved chunks to produce a clear answer supported by the documents.
4. Our Python code checks whether the source IDs cited by the model actually belong to the retrieved chunks.
5. If no sufficiently relevant information is found, the assistant should say it does not know rather than invent an answer.