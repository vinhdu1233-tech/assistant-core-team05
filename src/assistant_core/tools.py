"""Deterministic tools for parsing credits and calculating tuition."""

import json

from pydantic import BaseModel, Field, ValidationError

from assistant_core.errors import InvalidRequest


def parse_credits(text: str) -> tuple[int, int]:
    """Extract credit count and retake count from a tuition question."""
    words = text.lower()
    for char in "?,.;:!":
        words = words.replace(char, " ")
    words = words.split()

    credits = 0
    retake = 0

    for i, word in enumerate(words):
        if not word.isdigit():
            continue

        number = int(word)

        previous_is_retake = i > 0 and words[i - 1].startswith("retake")
        next_is_retake = i + 1 < len(words) and words[i + 1].startswith("retake")

        if previous_is_retake or next_is_retake:
            retake = number
        elif credits == 0:
            credits = number

    if credits <= 0:
        raise InvalidRequest("Credit count must be positive.")

    return credits, retake


def tuition(
    credits: int,
    retake: int,
    rate: int,
    retake_multiplier: float,
    max_credits: int,
) -> int:
    """Calculate tuition including retake fees."""
    if credits <= 0 or credits > max_credits:
        raise InvalidRequest("Invalid credit count.")

    if retake < 0:
        raise InvalidRequest("Retake count cannot be negative.")

    if rate < 0 or retake_multiplier < 0:
        raise InvalidRequest("Tuition rates cannot be negative.")

    total = credits * rate + retake * rate * retake_multiplier
    return int(total)


class FeeArgs(BaseModel):
    credits: int = Field(ge=1, le=30)
    retake: int = Field(default=0, ge=0, le=30)


TOOL_SPECS = {
    "calc_fee": {
        "description": "Compute deterministic tuition in VND.",
        "parameters": FeeArgs.model_json_schema(),
    },
}


def run_tool_call(raw: str, rate: int, retake_multiplier: float, max_credits: int) -> str | None:
    """Validate a requested tool call; do not trust LLM-provided arguments."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "tool" not in data:
        return None
    if data["tool"] != "calc_fee":
        raise InvalidRequest(f"unknown tool {data['tool']!r}")
    try:
        args = FeeArgs.model_validate(data.get("args", {}))
    except ValidationError as exc:
        raise InvalidRequest("invalid tool arguments") from exc
    total = tuition(args.credits, args.retake, rate, retake_multiplier, max_credits)
    return f"Your tuition is {total:,} VND."
