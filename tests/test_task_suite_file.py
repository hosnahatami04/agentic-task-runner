"""Validates the real tasks/task_suite.json file against the TaskDefinition schema."""

from collections import Counter
from pathlib import Path

from agent.task_suite import TaskCategory, load_task_suite

SUITE_PATH = Path(__file__).parent.parent / "tasks" / "task_suite.json"


def test_suite_file_loads_and_validates():
    tasks = load_task_suite(SUITE_PATH)

    assert len(tasks) == 37


def test_all_task_ids_are_unique():
    tasks = load_task_suite(SUITE_PATH)

    ids = [t.id for t in tasks]
    assert len(ids) == len(set(ids))


def test_category_distribution_matches_plan():
    tasks = load_task_suite(SUITE_PATH)

    counts = Counter(t.category for t in tasks)

    assert counts[TaskCategory.SINGLE_TOOL] == 7
    assert counts[TaskCategory.MULTI_TOOL] == 11
    assert counts[TaskCategory.MULTI_STEP_REASONING] == 6
    assert counts[TaskCategory.ERROR_PRONE] == 5
    assert counts[TaskCategory.IMPOSSIBLE] == 8


def test_impossible_tasks_all_marked_should_refuse():
    tasks = load_task_suite(SUITE_PATH)

    for task in tasks:
        if task.category == TaskCategory.IMPOSSIBLE:
            assert task.should_refuse is True, f"{task.id} should have should_refuse=True"


def test_non_impossible_tasks_have_expected_answer():
    tasks = load_task_suite(SUITE_PATH)

    for task in tasks:
        if task.category != TaskCategory.IMPOSSIBLE:
            assert task.expected_answer is not None, f"{task.id} is missing an expected_answer"


def test_referenced_fixtures_exist():
    fixtures_dir = Path(__file__).parent.parent / "tasks" / "fixtures"
    known_fixtures = {"company.db"} | {p.name for p in fixtures_dir.glob("*.txt")}

    tasks = load_task_suite(SUITE_PATH)

    for task in tasks:
        for fixture_name in task.setup.values():
            assert fixture_name in known_fixtures, (
                f"{task.id} references unknown fixture '{fixture_name}'"
            )
