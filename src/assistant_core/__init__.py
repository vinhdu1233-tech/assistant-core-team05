"""Maintainable study assistant core package."""

from assistant_core.models import Message, Response
from assistant_core.service import AssistantService, build_service

__version__ = "0.3.0"

__all__ = [
    "AssistantService",
    "Message",
    "Response",
    "build_service",
]
