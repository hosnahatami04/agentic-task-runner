"""Mock web_fetch tool: serves canned responses so the agent can run fully offline."""

from __future__ import annotations

import json
from pathlib import Path

from agent.models import Observation

from .registry import tool

MOCK_RESPONSES_PATH = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "mock_web" / "responses.json"
)


def _load_mock_responses() -> dict[str, str]:
    if not MOCK_RESPONSES_PATH.is_file():
        return {}
    return json.loads(MOCK_RESPONSES_PATH.read_text(encoding="utf-8"))


@tool(
    name="web_fetch",
    description=(
        "Fetches the text content of a URL. Runs fully offline against a fixed "
        "set of known URLs; unknown URLs return an error."
    ),
    parameters={
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
)
def web_fetch(url: str) -> Observation:
    responses = _load_mock_responses()

    if url not in responses:
        return Observation(success=False, error=f"URL not reachable: {url}")

    return Observation(success=True, data=responses[url])
