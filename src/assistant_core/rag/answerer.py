"""Answer policy questions with retrieval + LLM, safely.

Order of defences:
  1. retrieve; if the best score is too low -> ABSTAIN and escalate (no LLM call)
  2. ask the LLM for structured JSON; validate schema + grounding; retry once
  3. on provider failure or invalid output -> quote the best source (retrieval-only fallback)
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable

from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.llm import LLM, AnswerDraft, build_prompt, parse_draft
from assistant_core.models import Intent, Response, Source
from assistant_core.rag.index import DEFAULT_MIN_SCORES, HybridIndex, Index, TfidfIndex

log = logging.getLogger("assistant_core.rag")
ESCALATE_MSG = (
    "I'm not confident I can answer that from the official documents. "
    "Please contact the Training Office (room I.101) or ask your academic advisor."
)


class RagAnswerer:
    def __init__(
        self,
        index: Index,
        llm: LLM | None,
        min_score: float | None = None,
        k: int = 3,
        prompt_version: str = "answer_v1",
        retries: int = 1,
        tool_runner: Callable[[str], str | None] | None = None,
    ):
        cosine_scale = isinstance(index, (TfidfIndex, HybridIndex))
        if min_score is None:
            min_score = DEFAULT_MIN_SCORES["tfidf" if cosine_scale else "bm25"]
        if not math.isfinite(min_score) or min_score < 0 or (cosine_scale and min_score > 1.0):
            raise ValueError("Invalid minimum score for retrieval index")
        self.index, self.llm, self.min_score, self.k = index, llm, min_score, k
        self.prompt_version, self.retries, self.tool_runner = prompt_version, retries, tool_runner

    def answer(self, question: str) -> Response:
        hits = self.index.search(question, self.k)
        # A1: refuse unsupported questions before creating a prompt or calling the model.
        if not hits or not math.isfinite(hits[0].score) or hits[0].score < self.min_score:
            return Response(answer=ESCALATE_MSG, intent=Intent.UNKNOWN, path="abstain", escalate=True, confidence=0.0)
        sources = {h.chunk.id: Source(id=h.chunk.id, title=h.chunk.title) for h in hits}
        top = hits[0].chunk
        if self.llm is None:  # retrieval-only baseline
            return Response(
                answer=f"{top.title}: {top.text}",
                intent=Intent.RULE,
                sources=[sources[top.id]],
                path="retrieval",
                confidence=None,
            )
        prompt = build_prompt(question, hits, self.prompt_version)
        for attempt in range(self.retries + 1):
            try:
                raw = self.llm.complete(prompt)
                if self.tool_runner is not None:
                    try:
                        result = self.tool_runner(raw)
                    except InvalidRequest as exc:
                        return Response(answer=str(exc), intent=Intent.FEE, path="tool", degraded=True)
                    if result is not None:
                        return Response(answer=result, intent=Intent.FEE, path="tool")
                draft: AnswerDraft = parse_draft(raw, set(sources))
                if draft.abstain:
                    return Response(
                        answer=ESCALATE_MSG,
                        intent=Intent.UNKNOWN,
                        path="abstain",
                        escalate=True,
                        confidence=draft.confidence,
                    )
                return Response(
                    answer=draft.answer,
                    intent=Intent.RULE,
                    path="llm",
                    confidence=draft.confidence,
                    sources=[sources[i] for i in draft.source_ids],
                )
            except ProviderError as exc:
                log.warning("llm attempt %d failed: %s", attempt + 1, exc)
        return Response(
            answer=f"{top.title}: {top.text}",
            intent=Intent.RULE,
            sources=[sources[top.id]],
            path="retrieval",
            degraded=True,
        )
