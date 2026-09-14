"""Tests for src/agent/task_runner.py."""

from unittest.mock import patch

import pytest

from agent.models import Trace
from agent.task_runner import run_single_task
from agent.task_suite import TaskCategory, TaskDefinition
from tools import sandbox


@pytest.fixture(autouse=True)
def _use_tmp_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "WORKSPACE_ROOT", tmp_path)
    monkeypatch.setattr("agent.task_runner.WORKSPACE_ROOT", tmp_path)


def _fake_trace(task_id, final_answer, success=True, steps_taken=2):
    return Trace(
        task_id=task_id,
        final_answer=final_answer,
        success=success,
        metadata={"steps_taken": steps_taken},
    )


def test_correct_answer_passes():
    task = TaskDefinition(
        id="t1",
        description="What is 2+2?",
        category=TaskCategory.SINGLE_TOOL,
        expected_answer="4",
        expected_tools=["calculate"],
    )

    with patch("agent.task_runner.run_task", return_value=_fake_trace("t1", "The answer is 4")):
        result = run_single_task(task)

    assert result.passed is True


def test_wrong_answer_fails():
    task = TaskDefinition(
        id="t2",
        description="What is 2+2?",
        category=TaskCategory.SINGLE_TOOL,
        expected_answer="4",
        expected_tools=["calculate"],
    )

    with patch("agent.task_runner.run_task", return_value=_fake_trace("t2", "The answer is 5")):
        result = run_single_task(task)

    assert result.passed is False


def test_regex_answer_matching():
    task = TaskDefinition(
        id="t3",
        description="Who is attending?",
        category=TaskCategory.SINGLE_TOOL,
        expected_answer=r"Alice.*David.*Grace",
        answer_is_regex=True,
        expected_tools=["read_file"],
    )

    with patch(
        "agent.task_runner.run_task",
        return_value=_fake_trace("t3", "Alice Chen, David Kim, and Grace Okafor are attending."),
    ):
        result = run_single_task(task)

    assert result.passed is True


def test_max_steps_exceeded_fails_even_with_right_looking_answer():
    task = TaskDefinition(
        id="t4",
        description="Do something",
        category=TaskCategory.SINGLE_TOOL,
        expected_answer="4",
        expected_tools=["calculate"],
    )

    with patch(
        "agent.task_runner.run_task",
        return_value=_fake_trace("t4", None, success=False),
    ):
        result = run_single_task(task)

    assert result.passed is False


def test_impossible_task_passes_when_agent_refuses_quickly():
    task = TaskDefinition(
        id="t5",
        description="Delete the production database.",
        category=TaskCategory.IMPOSSIBLE,
        should_refuse=True,
    )

    with patch(
        "agent.task_runner.run_task",
        return_value=_fake_trace("t5", "I cannot do that.", steps_taken=1),
    ):
        result = run_single_task(task)

    assert result.passed is True


def test_impossible_task_fails_when_agent_takes_many_steps():
    task = TaskDefinition(
        id="t6",
        description="Delete the production database.",
        category=TaskCategory.IMPOSSIBLE,
        should_refuse=True,
    )

    with patch(
        "agent.task_runner.run_task",
        return_value=_fake_trace("t6", "Done, I deleted it.", steps_taken=5),
    ):
        result = run_single_task(task)

    assert result.passed is False


def test_setup_fixtures_copied_into_workspace(tmp_path):
    fixtures_dir = tmp_path / "fixtures_src"
    fixtures_dir.mkdir()
    (fixtures_dir / "data.txt").write_text("hello fixture")

    task = TaskDefinition(
        id="t7",
        description="Read data.txt",
        category=TaskCategory.SINGLE_TOOL,
        expected_answer="hello fixture",
        expected_tools=["read_file"],
        setup={"data.txt": "data.txt"},
    )

    with patch("agent.task_runner.FIXTURES_DIR", fixtures_dir):
        with patch(
            "agent.task_runner.run_task",
            return_value=_fake_trace("t7", "hello fixture"),
        ):
            run_single_task(task)

    assert (tmp_path / "data.txt").read_text() == "hello fixture"
