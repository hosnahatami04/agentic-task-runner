"""Generates RELIABILITY_REPORT.md from previously saved traces.

Run run_harness.py for each profile first (clean, light, heavy, chaos)
so the traces/<profile>/ directories are populated.

Usage:
    python generate_report.py
"""

from agent.task_suite import load_task_suite
from harness.report import write_report

SUITE_PATH = "tasks/task_suite.json"
PROFILES = ["clean", "light", "heavy"]
OUTPUT_PATH = "RELIABILITY_REPORT.md"


def main() -> None:
    tasks = load_task_suite(SUITE_PATH)
    write_report(PROFILES, tasks, output_path=OUTPUT_PATH)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
