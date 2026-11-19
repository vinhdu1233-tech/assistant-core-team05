"""Public service entry point for the assistant_core package."""

import logging
from time import perf_counter

from assistant_core.config import Settings
from assistant_core.errors import ConfigError, InvalidRequest, ProviderError
from assistant_core.guard import PRIVATE_REPLY, is_private_request
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.llm import make_llm
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.rag.answerer import RagAnswerer
from assistant_core.rag.chunker import load_folder
from assistant_core.rag.index import make_index
from assistant_core.responder import Responder, TemplateResponder
from assistant_core.router import route
from assistant_core.tools import parse_credits, run_tool_call, tuition

log = logging.getLogger("assistant_core")


class AssistantService:
    """Route a validated message to deterministic tools or a rule responder."""

    def __init__(
        self,
        settings: Settings,
        offices: OfficeDirectory,
        handbook: Handbook,
        responder: Responder,
        rag: RagAnswerer | None = None,
    ) -> None:
        self.settings = settings
        self.offices = offices
        self.handbook = handbook
        self.responder = responder
        self.fallback = TemplateResponder()
        self.rag = rag

    def handle(self, msg: Message) -> Response:
        """Single stable entry point used by the CLI and future HTTP/UI layers."""
        started = perf_counter()
        # Protect private student data before any deterministic or RAG routing.
        if self.rag is not None and is_private_request(msg.text):
            result = Response(answer=PRIVATE_REPLY, intent=Intent.UNKNOWN, path="abstain")
        else:
            intent = route(msg.text, self.offices.names)
            result = self._dispatch(intent, msg.text)

        log.info(
            "handled",
            extra={
                "intent": result.intent.value,
                "latency_ms": round((perf_counter() - started) * 1000, 3),
                "session": msg.session_id,
                "degraded": result.degraded,
            },
        )
        return result

    def _dispatch(self, intent: Intent, text: str) -> Response:
        if intent is Intent.GREETING:
            result = Response(
                answer="Hello! I can help with offices, fees and rules.",
                intent=intent,
            )
        elif intent is Intent.FEE:
            result = self._fee(text)
        elif intent is Intent.OFFICE:
            office = self.offices.find(text)
            if office is None:
                result = Response(answer="Sorry, I don't know that yet.", intent=Intent.UNKNOWN)
            else:
                result = Response(
                    answer=f"{office.name}: room {office.room}, open {office.hours}",
                    intent=Intent.OFFICE,
                )
        else:
            result = self._rule(text)

        return result

    def _fee(self, text: str) -> Response:
        try:
            credits, retake_credits = parse_credits(text)
            amount = tuition(
                credits=credits,
                retake=retake_credits,
                rate=self.settings.credit_rate_vnd,
                retake_multiplier=self.settings.retake_multiplier,
                max_credits=self.settings.max_credits,
            )
        except InvalidRequest as exc:
            return Response(answer=str(exc), intent=Intent.FEE)

        return Response(answer=f"Your tuition is {amount:,} VND.", intent=Intent.FEE)

    def _rule(self, question: str) -> Response:
        if self.rag is not None:
            if is_private_request(question):
                return Response(answer=PRIVATE_REPLY, intent=Intent.UNKNOWN, path="abstain")
            return self.rag.answer(question)
        rule = self.handbook.search(question)
        if rule is None:
            return Response(answer="Sorry, I don't know that yet.", intent=Intent.UNKNOWN)

        sources = [Source(id=rule.id, title=rule.title)]
        try:
            answer = self.responder.explain(question, rule)
        except ProviderError:
            log.warning("provider failed; using template fallback")
            return Response(
                answer=self.fallback.explain(question, rule),
                intent=Intent.RULE,
                sources=sources,
                degraded=True,
            )

        return Response(
            answer=answer,
            intent=Intent.RULE,
            sources=sources,
        )


def build_service(settings: Settings) -> AssistantService:
    """Build a Lab 6-capable service without replacing the team's Lab 5 API."""
    from assistant_core.responder import StubLLMResponder

    if settings.llm_provider not in {"stub", "template", "ollama", "openai"}:
        raise ConfigError("Unsupported LLM provider")

    offices = OfficeDirectory.from_csv(settings.data_dir / "offices.csv")
    handbook = Handbook.from_json(settings.data_dir / "handbook.json")
    rag = None
    if settings.kb_dir.exists():
        chunks = load_folder(settings.kb_dir)
        index = make_index(settings.retrieval_kind, chunks)
        llm = None
        if settings.llm_provider != "template":
            llm = make_llm(
                settings.llm_provider,
                settings.llm_model,
                settings.llm_base_url,
                settings.llm_api_key,
                settings.llm_timeout_s,
            )

        def tool_runner(raw: str) -> str | None:
            return run_tool_call(raw, settings.credit_rate_vnd, settings.retake_multiplier, settings.max_credits)

        rag = RagAnswerer(
            index,
            llm,
            settings.retrieval_min_score,
            prompt_version=settings.prompt_version,
            tool_runner=tool_runner,
        )

    return AssistantService(
        settings=settings,
        offices=offices,
        handbook=handbook,
        responder=StubLLMResponder() if settings.llm_provider == "stub" else TemplateResponder(),
        rag=rag,
    )
