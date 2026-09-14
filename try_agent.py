"""Manual smoke-test script: run a task against the agent and see the full trace.

Usage:
    python try_agent.py "What is 12 * 8?"
    python try_agent.py "Write 'hello' to greeting.txt, then read it back."
"""

import sys

from tools import calculator, file_ops, search, sqlite_query, web_fetch  # noqa: F401

from agent.loop import run_task


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python try_agent.py "<task description>"')
        sys.exit(1)

    task = sys.argv[1]
    trace = run_task("manual-run", task)

    print(f"\n{'=' * 60}")
    print(f"TASK: {task}")
    print(f"{'=' * 60}\n")

    for i, step in enumerate(trace.steps, start=1):
        print(f"--- Step {i} ---")
        print(f"Thought: {step.thought}")
        if step.action:
            print(f"Action:  {step.action.tool_name}({step.action.arguments})")
        if step.observation:
            obs = step.observation
            print(f"Result:  success={obs.success} data={obs.data!r} error={obs.error!r}")
        print()

    print(f"{'=' * 60}")
    print(f"SUCCESS: {trace.success}")
    print(f"FINAL ANSWER: {trace.final_answer}")
    print(f"STEPS TAKEN: {trace.metadata.get('steps_taken')}")
    if not trace.success:
        print(f"FAILURE REASON: {trace.metadata.get('failure_reason')}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
