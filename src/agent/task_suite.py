"""Loads and validates the task suite: a fixed set of tasks with known-correct answers."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class TaskCategory(str, Enum):
    SINGLE_TOOL = "single_tool"
    MULTI_TOOL = "multi_tool"
    MULTI_STEP_REASONING = "multi_step_reasoning"
    ERROR_PRONE = "error_prone"
    IMPOSSIBLE = "impossible"


class TaskDefinition(BaseModel):
    """One task in the suite: a task description plus how to grade the agent's answer."""

    id: str
    description: str
    category: TaskCategory
    expected_answer: str | None = None
    answer_is_regex: bool = False
    expected_tools: list[str] = Field(default_factory=list)
    should_refuse: bool = False
    setup: dict[str, str] = Field(default_factory=dict)


def load_task_suite(path: str | Path) -> list[TaskDefinition]:
    """Load and validate the task suite JSON file."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [TaskDefinition.model_validate(item) for item in raw]
