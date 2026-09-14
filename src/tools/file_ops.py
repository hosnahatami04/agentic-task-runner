"""File read/write tools, sandboxed to a single workspace directory."""

from __future__ import annotations

from agent.models import Observation

from .registry import tool
from .sandbox import resolve_in_sandbox


@tool(
    name="read_file",
    description="Reads the contents of a text file inside the workspace.",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
)
def read_file(path: str) -> Observation:
    try:
        full_path = resolve_in_sandbox(path)
    except ValueError as exc:
        return Observation(success=False, error=str(exc))

    if not full_path.is_file():
        return Observation(success=False, error=f"File not found: {path}")

    try:
        content = full_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Observation(success=False, error=f"File is not valid UTF-8 text: {path}")

    return Observation(success=True, data=content)


@tool(
    name="write_file",
    description="Writes text content to a file inside the workspace, creating it if needed.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
)
def write_file(path: str, content: str) -> Observation:
    try:
        full_path = resolve_in_sandbox(path)
    except ValueError as exc:
        return Observation(success=False, error=str(exc))

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

    return Observation(success=True, data=f"Wrote {len(content)} characters to {path}")
