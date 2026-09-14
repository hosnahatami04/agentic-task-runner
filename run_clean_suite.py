"""Runs the full 40-task suite against the real agent (no fault injection).

Usage:
    python run_clean_suite.py
"""

from tools import calculator, file_ops, search, sqlite_query, web_fetch  # noqa: F401

from agent.task_runner import run_suite
from agent.task_suite import load_task_suite

SUITE_PATH = "tasks/task_suite.json"


def main() -> None:
    tasks = load_task_suite(SUITE_PATH)
    print(f"Running {len(tasks)} tasks...\n")

    results = run_suite(tasks)

    passed = sum(1 for r in results if r.passed)
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed}/{len(results)} passed ({passed / len(results):.0%})")
    print(f"{'=' * 60}\n")

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.task.id} ({r.task.category.value})")
        if not r.passed:
            print(f"       expected: {r.task.expected_answer!r}")
            print(f"       actual:   {r.actual_answer!r}")
            print(f"       trace_success: {r.trace_success}")


if __name__ == "__main__":
    main()
