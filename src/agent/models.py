"""Core data types shared by the agent loop, tools, and harness."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolSchema(BaseModel):
    """Describes a tool to the LLM: its name, purpose, and expected arguments."""

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class Action(BaseModel):
    """A tool call the LLM has decided to make."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class Observation(BaseModel):
    """The result of executing an Action."""

    success: bool
    data: Any = None
    error: str | None = None


class Step(BaseModel):
    """One iteration of the ReAct loop: what the agent thought, did, and saw."""

    thought: str
    action: Action | None = None
    observation: Observation | None = None


class Trace(BaseModel):
    """The full record of an agent run on a single task."""

    task_id: str
    steps: list[Step] = Field(default_factory=list)
    final_answer: str | None = None
    success: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
