"""Shared sandbox logic: confines file-based tools to a single workspace directory."""

from __future__ import annotations

from pathlib import Path

WORKSPACE_ROOT = Path("workspace").resolve()


def resolve_in_sandbox(path: str) -> Path:
    """Resolve a user-supplied path against the workspace root.

    Raises ValueError if the resolved path would escape the sandbox
    (e.g. via '..' segments or an absolute path).
    """
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    candidate = (WORKSPACE_ROOT / path).resolve()

    if not candidate.is_relative_to(WORKSPACE_ROOT):
        raise ValueError(f"Path '{path}' escapes the workspace sandbox")

    return candidate
