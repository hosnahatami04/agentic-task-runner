"""Tests for src/agent/prompt.py."""

import pytest

from agent.models import ToolSchema
from agent.prompt import build_system_prompt
from tools import registry


@pytest.fixture(autouse=True)
def _clear_registry():
    registry.clear()
    yield
    registry.clear()


def test_includes_tool_name_and_description():
    schemas = [
        ToolSchema(
            name="calculate",
            description="Evaluates a math expression.",
            parameters={"type": "object"},
        )
    ]

    prompt = build_system_prompt(schemas)

    assert "calculate" in prompt
    assert "Evaluates a math expression." in prompt


def test_includes_multiple_tools():
    schemas = [
        ToolSchema(name="tool_a", description="Does A.", parameters={}),
        ToolSchema(name="tool_b", description="Does B.", parameters={}),
    ]

    prompt = build_system_prompt(schemas)

    assert "tool_a" in prompt
    assert "tool_b" in prompt


def test_includes_output_format_instructions():
    prompt = build_system_prompt([])

    assert "final_answer" in prompt
    assert "tool_name" in prompt


def test_handles_empty_tool_list():
    prompt = build_system_prompt([])

    assert "Available tools:" in prompt
