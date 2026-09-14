"""Runs the task suite against the agent under clean (no fault injection) conditions."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from agent.loop import run_task
from agent.task_suite import TaskDefinition
from tools.sandbox import WORKSPACE_ROOT

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tasks" / "fixtures"


class TaskResult:
    """Whether one task's agent run matched what the task expected."""

    def __init__(self, task: TaskDefinition, passed: bool, actual_answer: str | None, trace_success: bool):
        self.task = task
        self.passed = passed
        self.actual_answer = actual_answer
        self.trace_success = trace_success


def _setup_fixtures(task: TaskDefinition) -> None:
    """Copy any files this task needs into the workspace before running it."""
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    for workspace_name, fixture_name in task.setup.items():
        source = FIXTURES_DIR / fixture_name
        destination = WORKSPACE_ROOT / workspace_name
        shutil.copyfile(source, destination)


def _answer_matches(task: TaskDefinition, actual_answer: str | None) -> bool:
    if actual_answer is None:
        return False
    if task.answer_is_regex:
        return re.search(task.expected_answer, actual_answer, re.IGNORECASE) is not None
    return task.expected_answer.strip().lower() in actual_answer.strip().lower()


def run_single_task(task: TaskDefinition) -> TaskResult:
    """Run one task against the agent and grade the result."""
    _setup_fixtures(task)
    trace = run_task(task.id, task.description)

    if task.should_refuse:
        passed = trace.final_answer is not None and trace.metadata.get("steps_taken", 0) <= 2
        return TaskResult(task, passed, trace.final_answer, trace.success)

    passed = trace.success and _answer_matches(task, trace.final_answer)
    return TaskResult(task, passed, trace.final_answer, trace.success)


def run_suite(tasks: list[TaskDefinition]) -> list[TaskResult]:
    """Run every task in the suite and return one TaskResult per task."""
    return [run_single_task(task) for task in tasks]
