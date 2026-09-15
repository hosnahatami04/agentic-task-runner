"""Interactive chat loop: type a task, see the agent think and act, repeat.

Usage:
    python chat.py

Type 'exit' or 'quit' to stop.
"""

from tools import calculator, file_ops, search, sqlite_query, web_fetch  # noqa: F401

from agent.loop import run_task

EXIT_COMMANDS = {"exit", "quit"}


def _print_trace(trace) -> None:
    for i, step in enumerate(trace.steps, start=1):
        print(f"  [{i}] {step.thought}")
        if step.action:
            print(f"      -> {step.action.tool_name}({step.action.arguments})")
        if step.observation:
            obs = step.observation
            if obs.success:
                print(f"      <- {obs.data!r}")
            else:
                print(f"      <- ERROR: {obs.error}")

    print()
    if trace.success:
        print(f"Agent: {trace.final_answer}")
    else:
        print(f"Agent: (did not finish — {trace.metadata.get('failure_reason')})")


def main() -> None:
    print("Chat with the agent. Type 'exit' or 'quit' to stop.\n")
    turn = 0

    while True:
        try:
            task = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not task:
            continue
        if task.lower() in EXIT_COMMANDS:
            break

        turn += 1
        trace = run_task(f"chat-{turn}", task)
        _print_trace(trace)
        print()


if __name__ == "__main__":
    main()
