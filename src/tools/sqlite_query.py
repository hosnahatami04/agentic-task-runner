"""SQLite query tool: read-only SELECT access to a workspace database."""

from __future__ import annotations

import sqlite3

from agent.models import Observation

from .registry import tool
from .sandbox import resolve_in_sandbox

_ALLOWED_FIRST_WORD = "select"


@tool(
    name="query_db",
    description=(
        "Runs a read-only SELECT query against a SQLite database in the workspace. "
        "If you don't know the table or column names yet, first run "
        "\"SELECT sql FROM sqlite_master WHERE type='table'\" to see every table's "
        "exact structure before querying its data."
    ),
    parameters={
        "type": "object",
        "properties": {
            "sql": {"type": "string"},
            "db_path": {"type": "string"},
        },
        "required": ["sql", "db_path"],
    },
)
def query_db(sql: str, db_path: str) -> Observation:
    stripped = sql.strip()
    first_word = stripped.split(None, 1)[0].lower() if stripped else ""

    if first_word != _ALLOWED_FIRST_WORD:
        return Observation(
            success=False,
            error="Only SELECT statements are allowed",
        )

    try:
        full_path = resolve_in_sandbox(db_path)
    except ValueError as exc:
        return Observation(success=False, error=str(exc))

    if not full_path.is_file():
        return Observation(success=False, error=f"Database not found: {db_path}")

    try:
        # Open read-only so even a crafted multi-statement string can't write.
        uri = f"file:{full_path.as_posix()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        try:
            cursor = connection.execute(stripped)
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            connection.close()
    except sqlite3.Error as exc:
        return Observation(success=False, error=f"SQL error: {exc}")

    return Observation(success=True, data=rows)
