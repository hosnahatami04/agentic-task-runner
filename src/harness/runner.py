"""Runs the task suite under a given fault profile and saves a trace per task."""

from __future__ import annotations

import json
import random
import shutil
from contextlib import contextmanager
from pathlib import Path

from agent.loop import run_task
from agent.task_suite import TaskDefinition
from harness.fault_injector import FaultConfig, wrap_tool
from tools import registry
from tools.sandbox import WORKSPACE_ROOT

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tasks" / "fixtures"


@contextmanager
def apply_fault_profile(fault_configs: dict[str, FaultConfig], seed: int | None = None):
    """Temporarily wrap registered tools with fault injection, then restore them.

    fault_configs maps tool name -> FaultConfig. Tools not listed run unmodified.
    """
    rng = random.Random(seed)
    original_funcs = dict(registry._registry)

    try:
        for tool_name, fault_config in fault_configs.items():
            if tool_name in registry._registry:
                registry._registry[tool_name] = wrap_tool(
                    original_funcs[tool_name], fault_config, rng=rng
                )
        yield
    finally:
        registry._registry.clear()
        registry._registry.update(original_funcs)


def _setup_fixtures(task: TaskDefinition) -> None:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    for workspace_name, fixture_name in task.setup.items():
        source = FIXTURES_DIR / fixture_name
        destination = WORKSPACE_ROOT / workspace_name
        shutil.copyfile(source, destination)


def run_suite_with_faults(
    tasks: list[TaskDefinition],
    fault_configs: dict[str, FaultConfig],
    profile_name: str,
    traces_dir: str | Path = "traces",
    seed: int | None = None,
) -> list[dict]:
    """Run every task under the given fault profile, saving one trace JSON per task.

    Returns a list of {task_id, category, trace} summaries for quick inspection.
    """
    traces_path = Path(traces_dir) / profile_name
    traces_path.mkdir(parents=True, exist_ok=True)

    results = []
    with apply_fault_profile(fault_configs, seed=seed):
        for task in tasks:
            _setup_fixtures(task)

            try:
                trace = run_task(task.id, task.description)
            except Exception as exc:
                trace = None
                error = str(exc)
            else:
                error = None

            record = {
                "task_id": task.id,
                "category": task.category.value,
                "profile": profile_name,
                "trace": trace.model_dump() if trace else None,
                "unhandled_error": error,
            }
            (traces_path / f"{task.id}.json").write_text(
                json.dumps(record, indent=2), encoding="utf-8"
            )
            results.append(record)

    return results
