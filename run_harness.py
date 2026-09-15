"""Runs the task suite under a chosen fault profile and prints a summary.

Usage:
    python run_harness.py clean
    python run_harness.py light
    python run_harness.py heavy
    python run_harness.py chaos
"""

import sys

from tools import calculator, document_reader, file_ops, search, sqlite_query  # noqa: F401

from agent.task_suite import load_task_suite
from harness.profiles import PROFILES
from harness.runner import run_suite_with_faults

SUITE_PATH = "tasks/task_suite.json"
SEED = 42


def main() -> None:
    profile_name = sys.argv[1] if len(sys.argv) > 1 else "clean"
    if profile_name not in PROFILES:
        print(f"Unknown profile '{profile_name}'. Choose from: {list(PROFILES)}")
        sys.exit(1)

    tasks = load_task_suite(SUITE_PATH)
    fault_config = PROFILES[profile_name]
    fault_configs = {schema_name: fault_config for schema_name in _tool_names()}

    print(f"Running {len(tasks)} tasks under profile '{profile_name}'...\n")
    results = run_suite_with_faults(
        tasks, fault_configs, profile_name, traces_dir="traces", seed=SEED
    )

    succeeded = sum(1 for r in results if r["trace"] and r["trace"]["success"])
    print(f"\n{'=' * 60}")
    print(f"PROFILE: {profile_name}")
    print(f"trace_success (agent reached a final answer): {succeeded}/{len(results)}")
    print(f"{'=' * 60}")

    for r in results:
        status = "OK" if r["trace"] and r["trace"]["success"] else "FAIL"
        reason = ""
        if r["unhandled_error"]:
            reason = f"unhandled: {r['unhandled_error']}"
        elif r["trace"] and not r["trace"]["success"]:
            reason = r["trace"]["metadata"].get("failure_reason", "")
        print(f"[{status}] {r['task_id']:15s} {reason}")


def _tool_names() -> list[str]:
    from tools.registry import list_schemas

    return [schema.name for schema in list_schemas()]


if __name__ == "__main__":
    main()
