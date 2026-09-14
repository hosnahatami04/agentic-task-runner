"""Local text search tool: finds a query string across files in the workspace."""

from __future__ import annotations

from agent.models import Observation

from .registry import tool
from .sandbox import resolve_in_sandbox


@tool(
    name="search_files",
    description=(
        "Searches for a text query across files in a workspace directory "
        "(case-insensitive). Returns matching file paths with their matching lines."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "directory": {"type": "string"},
        },
        "required": ["query", "directory"],
    },
)
def search_files(query: str, directory: str = ".") -> Observation:
    try:
        search_root = resolve_in_sandbox(directory)
    except ValueError as exc:
        return Observation(success=False, error=str(exc))

    if not search_root.is_dir():
        return Observation(success=False, error=f"Directory not found: {directory}")

    matches: list[dict[str, object]] = []
    query_lower = query.lower()

    for file_path in sorted(search_root.rglob("*")):
        if not file_path.is_file():
            continue

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(lines, start=1):
            if query_lower in line.lower():
                matches.append(
                    {
                        "path": str(file_path.relative_to(search_root)),
                        "line_number": line_number,
                        "line": line,
                    }
                )

    return Observation(success=True, data=matches)
