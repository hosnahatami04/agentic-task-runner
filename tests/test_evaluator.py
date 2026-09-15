"""Tests for src/harness/evaluator.py."""

import json

import pytest

from agent.task_suite import TaskCategory, TaskDefinition
from harness.evaluator import evaluate_profile


def _write_trace(traces_dir, profile, task_id, trace, unhandled_error=None):
    profile_dir = traces_dir / profile
    profile_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "task_id": task_id,
        "category": "single_tool",
        "profile": profile,
        "trace": trace,
        "unhandled_error": unhandled_error,
    }
    (profile_dir / f"{task_id}.json").write_text(json.dumps(record), encoding="utf-8")


def _simple_trace(final_answer, success=True, steps_taken=1, steps=None):
    return {
        "task_id": "irrelevant",
        "steps": steps if steps is not None else [],
        "final_answer": final_answer,
        "success": success,
        "metadata": {"steps_taken": steps_taken},
    }


@pytest.fixture
def task():
    return TaskDefinition(
        id="t1",
        description="What is 2+2?",
        category=TaskCategory.SINGLE_TOOL,
        expected_answer="4",
        expected_tools=["calculate"],
    )


def test_task_success_rate_all_correct(tmp_path, task):
    _write_trace(tmp_path, "clean", "t1", _simple_trace("The answer is 4"))

    metrics = evaluate_profile("clean", [task], traces_dir=tmp_path)

    assert metrics.total_tasks == 1
    assert metrics.task_success_rate == 1.0


def test_task_success_rate_wrong_answer(tmp_path, task):
    _write_trace(tmp_path, "clean", "t1", _simple_trace("The answer is 5"))

    metrics = evaluate_profile("clean", [task], traces_dir=tmp_path)

    assert metrics.task_success_rate == 0.0


def test_unhandled_error_counts_as_failure(tmp_path, task):
    _write_trace(tmp_path, "heavy", "t1", trace=None, unhandled_error="Simulated timeout")

    metrics = evaluate_profile("heavy", [task], traces_dir=tmp_path)

    assert metrics.total_tasks == 1
    assert metrics.task_success_rate == 0.0


def test_success_rate_by_category(tmp_path):
    task_a = TaskDefinition(
        id="a", description="x", category=TaskCategory.SINGLE_TOOL,
        expected_answer="ok", expected_tools=[],
    )
    task_b = TaskDefinition(
        id="b", description="x", category=TaskCategory.MULTI_TOOL,
        expected_answer="ok", expected_tools=[],
    )
    _write_trace(tmp_path, "clean", "a", _simple_trace("ok"))
    _write_trace(tmp_path, "clean", "b", _simple_trace("wrong"))

    metrics = evaluate_profile("clean", [task_a, task_b], traces_dir=tmp_path)

    assert metrics.success_rate_by_category["single_tool"] == 1.0
    assert metrics.success_rate_by_category["multi_tool"] == 0.0


def test_recovery_rate_when_tool_failed_but_task_succeeded(tmp_path, task):
    steps = [
        {"thought": "t", "action": {"tool_name": "calculate", "arguments": {}}, "observation": {"success": False, "data": None, "error": "boom"}},
        {"thought": "t2", "action": {"tool_name": "calculate", "arguments": {}}, "observation": {"success": True, "data": 4, "error": None}},
    ]
    _write_trace(tmp_path, "heavy", "t1", _simple_trace("The answer is 4", steps=steps))

    metrics = evaluate_profile("heavy", [task], traces_dir=tmp_path)

    assert metrics.tool_error_recovery_rate == 1.0


def test_recovery_rate_none_when_no_tool_failures(tmp_path, task):
    _write_trace(tmp_path, "clean", "t1", _simple_trace("The answer is 4"))

    metrics = evaluate_profile("clean", [task], traces_dir=tmp_path)

    assert metrics.tool_error_recovery_rate is None


def test_hallucination_flagged_when_success_but_last_observation_failed(tmp_path, task):
    steps = [
        {"thought": "t", "action": {"tool_name": "calculate", "arguments": {}}, "observation": {"success": False, "data": None, "error": "boom"}},
    ]
    _write_trace(tmp_path, "heavy", "t1", _simple_trace("I got 4", success=True, steps=steps))

    metrics = evaluate_profile("heavy", [task], traces_dir=tmp_path)

    assert metrics.hallucinated_result_rate == 1.0


def test_average_steps_to_completion(tmp_path):
    task_a = TaskDefinition(
        id="a", description="x", category=TaskCategory.SINGLE_TOOL,
        expected_answer="ok", expected_tools=[],
    )
    task_b = TaskDefinition(
        id="b", description="x", category=TaskCategory.SINGLE_TOOL,
        expected_answer="ok", expected_tools=[],
    )
    _write_trace(tmp_path, "clean", "a", _simple_trace("ok", steps_taken=2))
    _write_trace(tmp_path, "clean", "b", _simple_trace("ok", steps_taken=4))

    metrics = evaluate_profile("clean", [task_a, task_b], traces_dir=tmp_path)

    assert metrics.average_steps_to_completion == 3.0


def test_correct_refusal_rate(tmp_path):
    refuse_task = TaskDefinition(
        id="r1", description="delete everything", category=TaskCategory.IMPOSSIBLE,
        should_refuse=True,
    )
    _write_trace(tmp_path, "clean", "r1", _simple_trace("I cannot do that", steps_taken=1))

    metrics = evaluate_profile("clean", [refuse_task], traces_dir=tmp_path)

    assert metrics.correct_refusal_rate == 1.0


def test_correct_refusal_rate_none_when_no_refusal_tasks(tmp_path, task):
    _write_trace(tmp_path, "clean", "t1", _simple_trace("The answer is 4"))

    metrics = evaluate_profile("clean", [task], traces_dir=tmp_path)

    assert metrics.correct_refusal_rate is None
