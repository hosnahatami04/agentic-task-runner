"""Generates a Markdown reliability report from evaluated fault profiles."""

from __future__ import annotations

import json
from pathlib import Path

from agent.task_suite import TaskDefinition
from harness.evaluator import (
    ProfileMetrics,
    evaluate_profile,
    had_a_failed_observation,
    load_trace_records,
)


def _format_rate(value: float | None) -> str:
    return f"{value:.0%}" if value is not None else "n/a"


def _summary_table(all_metrics: list[ProfileMetrics]) -> str:
    header = "| Profile | Success Rate | Tool-Error Recovery | Hallucination Rate | Avg Steps | Refusal Rate |"
    separator = "|---|---|---|---|---|---|"
    rows = [header, separator]
    for m in all_metrics:
        rows.append(
            f"| {m.profile} | {_format_rate(m.task_success_rate)} "
            f"| {_format_rate(m.tool_error_recovery_rate)} "
            f"| {_format_rate(m.hallucinated_result_rate)} "
            f"| {m.average_steps_to_completion:.1f} "
            f"| {_format_rate(m.correct_refusal_rate)} |"
        )
    return "\n".join(rows)


def _category_breakdown(m: ProfileMetrics) -> str:
    lines = [f"### {m.profile}", ""]
    for category, rate in sorted(m.success_rate_by_category.items()):
        lines.append(f"- **{category}**: {_format_rate(rate)}")
    return "\n".join(lines)


def _find_recovery_case_studies(
    profile: str, traces_dir: Path, limit: int = 3
) -> list[dict]:
    """Find tasks that hit a tool failure but still ended in success."""
    studies = []
    for record in load_trace_records(traces_dir / profile):
        trace = record["trace"]
        if trace is None or not trace["success"]:
            continue
        if had_a_failed_observation(trace["steps"]):
            studies.append(record)
        if len(studies) >= limit:
            break
    return studies


def _render_case_study(record: dict) -> str:
    trace = record["trace"]
    lines = [f"#### {record['task_id']} ({record['category']})", ""]
    for i, step in enumerate(trace["steps"], start=1):
        lines.append(f"**Step {i}** — {step['thought']}")
        if step.get("action"):
            lines.append(f"- Action: `{step['action']['tool_name']}({step['action']['arguments']})`")
        if step.get("observation"):
            obs = step["observation"]
            lines.append(f"- Observation: success={obs['success']}, data={obs['data']!r}, error={obs['error']!r}")
        lines.append("")
    lines.append(f"**Final answer:** {trace['final_answer']}")
    return "\n".join(lines)


def generate_report(
    profiles: list[str],
    tasks: list[TaskDefinition],
    traces_dir: str | Path = "traces",
) -> str:
    """Build the full Markdown reliability report across the given profiles."""
    traces_path = Path(traces_dir)

    all_metrics = [evaluate_profile(p, tasks, traces_dir) for p in profiles]

    sections = [
        "# Reliability Report",
        "",
        "## Summary",
        "",
        _summary_table(all_metrics),
        "",
        "## Per-Category Breakdown",
        "",
    ]
    for m in all_metrics:
        sections.append(_category_breakdown(m))
        sections.append("")

    sections.append("## Case Studies: Recovering From a Tool Failure")
    sections.append("")
    found_any = False
    for profile in profiles:
        studies = _find_recovery_case_studies(profile, traces_path)
        for study in studies:
            found_any = True
            sections.append(_render_case_study(study))
            sections.append("")
    if not found_any:
        sections.append("_No recovery case studies found in these traces._")
        sections.append("")

    return "\n".join(sections)


def write_report(
    profiles: list[str],
    tasks: list[TaskDefinition],
    output_path: str | Path = "RELIABILITY_REPORT.md",
    traces_dir: str | Path = "traces",
) -> None:
    """Generate the report and write it to output_path."""
    report = generate_report(profiles, tasks, traces_dir)
    Path(output_path).write_text(report, encoding="utf-8")
