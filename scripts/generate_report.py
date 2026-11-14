"""Generates RELIABILITY_REPORT.md and results/summary.json from saved traces.

Run scripts/run_harness.py for each profile first (clean, light, heavy)
so the traces/<profile>/ directories are populated.

Usage:
    python scripts/generate_report.py
"""

from agent.task_suite import load_task_suite
from harness.report import write_report, write_summary

SUITE_PATH = "tasks/task_suite.json"
PROFILES = ["clean", "light", "heavy"]
OUTPUT_PATH = "RELIABILITY_REPORT.md"
SUMMARY_PATH = "results/summary.json"


def main() -> None:
    tasks = load_task_suite(SUITE_PATH)
    write_report(PROFILES, tasks, output_path=OUTPUT_PATH)
    write_summary(PROFILES, tasks, output_path=SUMMARY_PATH)
    print(f"Wrote {OUTPUT_PATH} and {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
