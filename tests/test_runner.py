"""Tests for src/harness/runner.py."""

from unittest.mock import patch

import pytest

from agent.models import Trace
from agent.task_suite import TaskCategory, TaskDefinition
from harness.fault_injector import FaultConfig, FaultType
from harness.runner import apply_fault_profile, run_suite_with_faults
from tools import registry


@pytest.fixture(autouse=True)
def _clear_registry():
    registry.clear()
    yield
    registry.clear()


@pytest.fixture
def echo_tool():
    @registry.tool(name="echo", description="Returns its input.", parameters={})
    def echo(value):
        return value

    return echo


def test_apply_fault_profile_restores_original_after_success(echo_tool):
    original = registry.get_tool("echo")

    with apply_fault_profile({"echo": FaultConfig(probabilities={FaultType.PERMISSION_ERROR: 1.0})}):
        wrapped = registry.get_tool("echo")
        assert wrapped is not original

    assert registry.get_tool("echo") is original


def test_apply_fault_profile_restores_original_after_exception(echo_tool):
    original = registry.get_tool("echo")

    with pytest.raises(ValueError):
        with apply_fault_profile({"echo": FaultConfig(probabilities={})}):
            raise ValueError("something went wrong inside the with block")

    assert registry.get_tool("echo") is original


def test_apply_fault_profile_actually_injects_fault(echo_tool):
    with apply_fault_profile(
        {"echo": FaultConfig(probabilities={FaultType.PERMISSION_ERROR: 1.0})}, seed=1
    ):
        result = registry.get_tool("echo")("hello")

    assert result.success is False
    assert "permission" in result.error.lower()


def test_unlisted_tools_are_not_wrapped(echo_tool):
    original = registry.get_tool("echo")

    with apply_fault_profile({}):
        assert registry.get_tool("echo") is original


def test_run_suite_with_faults_writes_trace_files(tmp_path, echo_tool):
    task = TaskDefinition(
        id="t1",
        description="Echo hello",
        category=TaskCategory.SINGLE_TOOL,
        expected_answer="hello",
        expected_tools=["echo"],
    )

    fake_trace = Trace(task_id="t1", final_answer="hello", success=True, metadata={"steps_taken": 1})

    with patch("harness.runner.run_task", return_value=fake_trace):
        results = run_suite_with_faults(
            [task], fault_configs={}, profile_name="clean", traces_dir=tmp_path
        )

    assert len(results) == 1
    assert results[0]["task_id"] == "t1"
    assert results[0]["trace"]["final_answer"] == "hello"

    saved_file = tmp_path / "clean" / "t1.json"
    assert saved_file.is_file()


def test_run_suite_with_faults_records_unhandled_errors(tmp_path, echo_tool):
    task = TaskDefinition(
        id="t2",
        description="This will crash",
        category=TaskCategory.SINGLE_TOOL,
        expected_answer="anything",
        expected_tools=["echo"],
    )

    with patch("harness.runner.run_task", side_effect=RuntimeError("boom")):
        results = run_suite_with_faults(
            [task], fault_configs={}, profile_name="clean", traces_dir=tmp_path
        )

    assert results[0]["trace"] is None
    assert "boom" in results[0]["unhandled_error"]
