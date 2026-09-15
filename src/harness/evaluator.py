"""Reads saved traces and computes reliability metrics for a fault profile."""

from __future__ import annotations

import json
import re
from pathlib import Path

from agent.task_suite import TaskDefinition
from pydantic import BaseModel, Field


class ProfileMetrics(BaseModel):
    """Reliability metrics computed from one profile's traces."""

    profile: str
    total_tasks: int
    task_success_rate: float
    success_rate_by_category: dict[str, float] = Field(default_factory=dict)
    tool_error_recovery_rate: float | None
    hallucinated_result_rate: float
    average_steps_to_completion: float
    correct_refusal_rate: float | None


def load_trace_records(profile_dir: Path) -> list[dict]:
    records = []
    for trace_file in sorted(profile_dir.glob("*.json")):
        records.append(json.loads(trace_file.read_text(encoding="utf-8")))
    return records


def _answer_matches(task: TaskDefinition, actual_answer: str | None) -> bool:
    if actual_answer is None:
        return False
    if task.answer_is_regex:
        return re.search(task.expected_answer, actual_answer, re.IGNORECASE) is not None
    return task.expected_answer.strip().lower() in actual_answer.strip().lower()


def had_a_failed_observation(steps: list[dict]) -> bool:
    return any(
        step.get("observation") is not None and step["observation"]["success"] is False
        for step in steps
    )


def _last_observation_failed(steps: list[dict]) -> bool:
    observations = [s["observation"] for s in steps if s.get("observation") is not None]
    if not observations:
        return False
    return observations[-1]["success"] is False


def evaluate_profile(
    profile: str,
    tasks: list[TaskDefinition],
    traces_dir: str | Path = "traces",
) -> ProfileMetrics:
    """Compute reliability metrics for one fault profile from its saved traces."""
    tasks_by_id = {task.id: task for task in tasks}
    records = load_trace_records(Path(traces_dir) / profile)

    passed_count = 0
    passed_by_category: dict[str, int] = {}
    total_by_category: dict[str, int] = {}

    tasks_with_a_tool_failure = 0
    tasks_with_a_tool_failure_that_still_succeeded = 0

    hallucination_count = 0
    steps_taken_list: list[int] = []

    refusal_tasks_total = 0
    refusal_tasks_correct = 0

    for record in records:
        task = tasks_by_id[record["task_id"]]
        category = task.category.value
        total_by_category[category] = total_by_category.get(category, 0) + 1

        trace = record["trace"]
        if trace is None:
            # An unhandled exception (e.g. a simulated timeout that leaked through)
            # counts as a failure for every metric below.
            continue

        steps = trace["steps"]
        steps_taken_list.append(trace["metadata"].get("steps_taken", len(steps)))

        if task.should_refuse:
            refusal_tasks_total += 1
            refused_correctly = (
                trace["final_answer"] is not None
                and trace["metadata"].get("steps_taken", 0) <= 3
            )
            if refused_correctly:
                refusal_tasks_correct += 1
                passed_count += 1
                passed_by_category[category] = passed_by_category.get(category, 0) + 1
            continue

        task_passed = trace["success"] and _answer_matches(task, trace["final_answer"])
        if task_passed:
            passed_count += 1
            passed_by_category[category] = passed_by_category.get(category, 0) + 1

        if had_a_failed_observation(steps):
            tasks_with_a_tool_failure += 1
            if task_passed:
                tasks_with_a_tool_failure_that_still_succeeded += 1

        if trace["success"] and _last_observation_failed(steps):
            hallucination_count += 1

    total_tasks = len(records)
    success_rate_by_category = {
        category: passed_by_category.get(category, 0) / total_by_category[category]
        for category in total_by_category
    }

    recovery_rate = (
        tasks_with_a_tool_failure_that_still_succeeded / tasks_with_a_tool_failure
        if tasks_with_a_tool_failure > 0
        else None
    )
    refusal_rate = (
        refusal_tasks_correct / refusal_tasks_total if refusal_tasks_total > 0 else None
    )

    return ProfileMetrics(
        profile=profile,
        total_tasks=total_tasks,
        task_success_rate=passed_count / total_tasks if total_tasks else 0.0,
        success_rate_by_category=success_rate_by_category,
        tool_error_recovery_rate=recovery_rate,
        hallucinated_result_rate=hallucination_count / total_tasks if total_tasks else 0.0,
        average_steps_to_completion=(
            sum(steps_taken_list) / len(steps_taken_list) if steps_taken_list else 0.0
        ),
        correct_refusal_rate=refusal_rate,
    )
