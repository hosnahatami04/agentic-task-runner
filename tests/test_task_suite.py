"""Tests for src/agent/task_suite.py."""

import json

import pytest

from agent.task_suite import TaskCategory, TaskDefinition, load_task_suite


def test_minimal_task_definition():
    task = TaskDefinition(
        id="t1",
        description="What is 2 + 2?",
        category=TaskCategory.SINGLE_TOOL,
        expected_answer="4",
        expected_tools=["calculate"],
    )

    assert task.should_refuse is False
    assert task.answer_is_regex is False
    assert task.setup == {}


def test_impossible_task_without_expected_answer():
    task = TaskDefinition(
        id="t2",
        description="Delete the production database.",
        category=TaskCategory.IMPOSSIBLE,
        should_refuse=True,
    )

    assert task.expected_answer is None
    assert task.should_refuse is True


def test_invalid_category_raises():
    with pytest.raises(ValueError):
        TaskDefinition(id="t3", description="x", category="not_a_real_category")


def test_load_task_suite_from_file(tmp_path):
    suite_path = tmp_path / "tasks.json"
    suite_path.write_text(
        json.dumps(
            [
                {
                    "id": "t1",
                    "description": "What is 2 + 2?",
                    "category": "single_tool",
                    "expected_answer": "4",
                    "expected_tools": ["calculate"],
                },
                {
                    "id": "t2",
                    "description": "Delete everything.",
                    "category": "impossible",
                    "should_refuse": True,
                },
            ]
        ),
        encoding="utf-8",
    )

    tasks = load_task_suite(suite_path)

    assert len(tasks) == 2
    assert tasks[0].id == "t1"
    assert tasks[1].should_refuse is True
