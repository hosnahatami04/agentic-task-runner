"""Tests for src/harness/report.py."""

import json

from agent.task_suite import TaskCategory, TaskDefinition
from harness.report import generate_report


def _write_trace(traces_dir, profile, task_id, category, trace):
    profile_dir = traces_dir / profile
    profile_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "task_id": task_id,
        "category": category,
        "profile": profile,
        "trace": trace,
        "unhandled_error": None,
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


def test_report_includes_summary_table(tmp_path):
    task = TaskDefinition(
        id="t1", description="x", category=TaskCategory.SINGLE_TOOL,
        expected_answer="4", expected_tools=[],
    )
    _write_trace(tmp_path, "clean", "t1", "single_tool", _simple_trace("The answer is 4"))

    report = generate_report(["clean"], [task], traces_dir=tmp_path)

    assert "# Reliability Report" in report
    assert "| clean |" in report


def test_report_includes_category_breakdown(tmp_path):
    task = TaskDefinition(
        id="t1", description="x", category=TaskCategory.SINGLE_TOOL,
        expected_answer="4", expected_tools=[],
    )
    _write_trace(tmp_path, "clean", "t1", "single_tool", _simple_trace("The answer is 4"))

    report = generate_report(["clean"], [task], traces_dir=tmp_path)

    assert "single_tool" in report


def test_report_includes_recovery_case_study(tmp_path):
    task = TaskDefinition(
        id="t1", description="x", category=TaskCategory.SINGLE_TOOL,
        expected_answer="4", expected_tools=[],
    )
    steps = [
        {
            "thought": "trying the tool",
            "action": {"tool_name": "calculate", "arguments": {"expression": "2+2"}},
            "observation": {"success": False, "data": None, "error": "boom"},
        },
        {
            "thought": "retrying",
            "action": {"tool_name": "calculate", "arguments": {"expression": "2+2"}},
            "observation": {"success": True, "data": 4, "error": None},
        },
    ]
    _write_trace(
        tmp_path, "heavy", "t1", "single_tool",
        _simple_trace("The answer is 4", steps=steps),
    )

    report = generate_report(["heavy"], [task], traces_dir=tmp_path)

    assert "Case Studies" in report
    assert "t1" in report
    assert "boom" in report


def test_report_handles_no_case_studies_gracefully(tmp_path):
    task = TaskDefinition(
        id="t1", description="x", category=TaskCategory.SINGLE_TOOL,
        expected_answer="4", expected_tools=[],
    )
    _write_trace(tmp_path, "clean", "t1", "single_tool", _simple_trace("The answer is 4"))

    report = generate_report(["clean"], [task], traces_dir=tmp_path)

    assert "No recovery case studies found" in report
