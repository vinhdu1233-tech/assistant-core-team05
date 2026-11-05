"""Public service entry point for the assistant_core package."""

import logging
from time import perf_counter

from assistant_core.config import Settings
from assistant_core.errors import ConfigError, InvalidRequest, ProviderError
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.responder import Responder, TemplateResponder
from assistant_core.router import route
from assistant_core.tools import parse_credits, tuition

log = logging.getLogger("assistant_core")


class AssistantService:
    """Route a validated message to deterministic tools or a rule responder."""

    def __init__(
        self,
        settings: Settings,
        offices: OfficeDirectory,
        handbook: Handbook,
        responder: Responder,
    ) -> None:
        self.settings = settings
        self.offices = offices
        self.handbook = handbook
        self.responder = responder
        self.fallback = TemplateResponder()

    def handle(self, msg: Message) -> Response:
        """Single stable entry point used by the CLI and future HTTP/UI layers."""
        started = perf_counter()
        intent = route(msg.text, self.offices.names)

        if intent is Intent.GREETING:
            result = Response(
                answer="Hello! I can help with offices, fees and rules.",
                intent=intent,
            )
        elif intent is Intent.FEE:
            result = self._fee(msg.text)
        elif intent is Intent.OFFICE:
            office = self.offices.find(msg.text)
            if office is None:
                result = Response(answer="Sorry, I don't know that yet.", intent=Intent.UNKNOWN)
            else:
                result = Response(
                    answer=f"{office.name}: room {office.room}, open {office.hours}",
                    intent=Intent.OFFICE,
                )
        else:
            result = self._rule(msg.text)

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
    """Create the shared assistant service for the API."""
    from assistant_core.responder import StubLLMResponder

    if settings.llm_provider != "stub":
        raise ConfigError("Only the stub provider is currently supported.")

    offices = OfficeDirectory.from_csv(settings.data_dir / "offices.csv")

    handbook = Handbook.from_json(settings.data_dir / "handbook.json")

    return AssistantService(
        settings=settings,
        offices=offices,
        handbook=handbook,
        responder=StubLLMResponder(),
    )
