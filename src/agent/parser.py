"""Extracts a structured Action or final answer from the LLM's raw text response."""

from __future__ import annotations

import json
import re

from agent.models import Action

_CODE_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class ParseError(Exception):
    """Raised when the LLM's response cannot be parsed into a valid action."""


class ParsedResponse:
    """Either a tool call (action set) or a final answer (final_answer set)."""

    def __init__(self, thought: str, action: Action | None, final_answer: str | None):
        self.thought = thought
        self.action = action
        self.final_answer = final_answer

    @property
    def is_final(self) -> bool:
        return self.final_answer is not None


def _extract_json_text(raw: str) -> str:
    """Strip markdown code fences, if present, to isolate the JSON payload."""
    match = _CODE_FENCE_PATTERN.search(raw)
    if match:
        return match.group(1)
    return raw.strip()


def _try_repair_json(text: str) -> str:
    """Attempt a couple of cheap fixes for common LLM JSON mistakes."""
    repaired = text.strip()
    # Trailing commas before a closing brace/bracket are a frequent LLM slip-up.
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    return repaired


def parse_response(raw: str) -> ParsedResponse:
    """Parse the LLM's raw text response into a ParsedResponse.

    Raises ParseError if no valid JSON action or final answer can be extracted,
    even after attempting a repair.
    """
    json_text = _extract_json_text(raw)

    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError:
        try:
            payload = json.loads(_try_repair_json(json_text))
        except json.JSONDecodeError as exc:
            raise ParseError(f"Could not parse a JSON object from response: {raw!r}") from exc

    if not isinstance(payload, dict):
        raise ParseError(f"Expected a JSON object, got: {type(payload).__name__}")

    thought = payload.get("thought", "")

    if "final_answer" in payload:
        return ParsedResponse(thought=thought, action=None, final_answer=payload["final_answer"])

    if "action" in payload:
        action_payload = payload["action"]
        try:
            action = Action.model_validate(action_payload)
        except Exception as exc:
            raise ParseError(f"Invalid action payload: {action_payload!r}") from exc
        return ParsedResponse(thought=thought, action=action, final_answer=None)

    raise ParseError(f"Response has neither 'action' nor 'final_answer': {raw!r}")
