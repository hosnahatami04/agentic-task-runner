"""Tests for src/agent/loop.py."""

from unittest.mock import patch

import pytest

from agent.loop import run_task
from tools import registry


@pytest.fixture(autouse=True)
def _clear_registry():
    registry.clear()
    yield
    registry.clear()


@pytest.fixture
def add_tool():
    @registry.tool(
        name="add",
        description="Adds two numbers.",
        parameters={
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"],
        },
    )
    def add(a, b):
        return a + b

    return add


def test_final_answer_on_first_response(add_tool):
    responses = ['{"thought": "I already know this", "final_answer": "42"}']

    with patch("agent.loop.generate", side_effect=responses):
        trace = run_task("t1", "What is the answer?")

    assert trace.success is True
    assert trace.final_answer == "42"
    assert len(trace.steps) == 1
    assert trace.steps[0].action is None


def test_tool_call_then_final_answer(add_tool):
    responses = [
        '{"thought": "I need to add", "action": {"tool_name": "add", "arguments": {"a": 2, "b": 3}}}',
        '{"thought": "Got the result", "final_answer": "5"}',
    ]

    with patch("agent.loop.generate", side_effect=responses):
        trace = run_task("t2", "What is 2 + 3?")

    assert trace.success is True
    assert trace.final_answer == "5"
    assert len(trace.steps) == 2
    assert trace.steps[0].action.tool_name == "add"
    assert trace.steps[0].observation.success is True
    assert trace.steps[0].observation.data == 5


def test_unknown_tool_produces_error_observation(add_tool):
    responses = [
        '{"thought": "calling a bad tool", "action": {"tool_name": "nonexistent", "arguments": {}}}',
        '{"thought": "giving up", "final_answer": "cannot do this"}',
    ]

    with patch("agent.loop.generate", side_effect=responses):
        trace = run_task("t3", "Do something impossible")

    assert trace.steps[0].observation.success is False
    assert "nonexistent" in trace.steps[0].observation.error


def test_wrong_arguments_produce_error_observation(add_tool):
    responses = [
        '{"thought": "calling with bad args", "action": {"tool_name": "add", "arguments": {"x": 1}}}',
        '{"thought": "giving up", "final_answer": "failed"}',
    ]

    with patch("agent.loop.generate", side_effect=responses):
        trace = run_task("t4", "Add something")

    assert trace.steps[0].observation.success is False


def test_unparseable_response_recorded_and_loop_continues(add_tool):
    responses = [
        "this is not json",
        '{"thought": "ok now", "final_answer": "done"}',
    ]

    with patch("agent.loop.generate", side_effect=responses):
        trace = run_task("t5", "Try again after a bad response")

    assert trace.success is True
    assert trace.final_answer == "done"
    assert len(trace.steps) == 2
    assert "Failed to parse" in trace.steps[0].thought


def test_max_steps_exceeded_returns_failed_trace(add_tool):
    response = '{"thought": "still working", "action": {"tool_name": "add", "arguments": {"a": 1, "b": 1}}}'

    with patch("agent.loop.generate", return_value=response):
        trace = run_task("t6", "Never finishes", max_steps=3)

    assert trace.success is False
    assert trace.final_answer is None
    assert len(trace.steps) == 3
    assert trace.metadata["failure_reason"] == "max steps exceeded"
