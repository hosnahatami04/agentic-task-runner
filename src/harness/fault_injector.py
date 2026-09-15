"""Wraps tool functions with configurable, random failure modes.

The agent loop is never aware this exists: it always calls tools.registry.get_tool()
as usual. The harness temporarily swaps a tool's registered function for a wrapped
version before a run, and restores the original afterward.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from enum import Enum
from typing import Any

from agent.models import Observation
from pydantic import BaseModel, Field


class FaultType(str, Enum):
    TIMEOUT = "timeout"
    CORRUPT_OUTPUT = "corrupt_output"
    PERMISSION_ERROR = "permission_error"
    IRRELEVANT_OUTPUT = "irrelevant_output"
    PARTIAL_FAILURE = "partial_failure"


class FaultConfig(BaseModel):
    """How likely each fault type is to trigger on a single tool call."""

    probabilities: dict[FaultType, float] = Field(default_factory=dict)

    def pick_fault(self, rng: random.Random) -> FaultType | None:
        """Roll the dice once per fault type; return the first one that triggers."""
        for fault_type, probability in self.probabilities.items():
            if rng.random() < probability:
                return fault_type
        return None


class TimeoutError_(Exception):
    """Raised to simulate a tool that took too long to respond."""


def _apply_fault(fault_type: FaultType, real_result: Any) -> Observation:
    if fault_type == FaultType.TIMEOUT:
        raise TimeoutError_("Simulated timeout: tool did not respond in time")

    if fault_type == FaultType.PERMISSION_ERROR:
        return Observation(success=False, error="Permission denied: access to this resource is restricted")

    if fault_type == FaultType.CORRUPT_OUTPUT:
        return Observation(success=True, data="{{{not-valid-json::garbled output###}}}")

    if fault_type == FaultType.IRRELEVANT_OUTPUT:
        return Observation(success=True, data="The weather in Reykjavik is currently 4 degrees Celsius.")

    if fault_type == FaultType.PARTIAL_FAILURE:
        if isinstance(real_result, Observation) and isinstance(real_result.data, str):
            truncated = real_result.data[: max(1, len(real_result.data) // 2)]
            return Observation(success=True, data=truncated)
        return Observation(success=True, data=None)

    raise ValueError(f"Unknown fault type: {fault_type}")


def wrap_tool(
    tool_func: Callable[..., Any],
    fault_config: FaultConfig,
    rng: random.Random | None = None,
) -> Callable[..., Any]:
    """Return a version of tool_func that may misbehave according to fault_config."""
    rng = rng or random.Random()

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        fault_type = fault_config.pick_fault(rng)
        if fault_type is None:
            return tool_func(*args, **kwargs)

        real_result = tool_func(*args, **kwargs)
        return _apply_fault(fault_type, real_result)

    return wrapped
