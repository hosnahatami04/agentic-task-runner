"""The ReAct loop: Thought -> Action -> Observation, repeated until done."""

from __future__ import annotations

from agent.models import Observation, Step, Trace
from agent.parser import ParseError, parse_response
from agent.prompt import build_system_prompt
from harness.fault_injector import TimeoutError_
from llm.ollama_client import generate
from tools.registry import get_tool, list_schemas

MAX_STEPS = 10


def _build_conversation(system_prompt: str, task: str, steps: list[Step]) -> str:
    """Render the system prompt, task, and step history into one prompt string."""
    parts = [system_prompt, f"\nTask: {task}\n"]

    for step in steps:
        parts.append(f"Thought: {step.thought}")
        if step.action is not None:
            parts.append(f"Action: {step.action.tool_name}({step.action.arguments})")
        if step.observation is not None:
            parts.append(f"Observation: {step.observation.model_dump()}")

    return "\n".join(parts)


def _execute_action(action) -> Observation:
    try:
        tool_func = get_tool(action.tool_name)
    except KeyError as exc:
        return Observation(success=False, error=str(exc))

    try:
        result = tool_func(**action.arguments)
    except TypeError as exc:
        return Observation(success=False, error=f"Invalid arguments for {action.tool_name}: {exc}")
    except TimeoutError_ as exc:
        return Observation(success=False, error=str(exc))

    if isinstance(result, Observation):
        return result
    return Observation(success=True, data=result)


def run_task(task_id: str, task: str, max_steps: int = MAX_STEPS) -> Trace:
    """Run the ReAct loop for a single task and return the full trace."""
    system_prompt = build_system_prompt(list_schemas())
    steps: list[Step] = []

    for _ in range(max_steps):
        prompt = _build_conversation(system_prompt, task, steps)
        raw_response = generate(prompt)

        try:
            parsed = parse_response(raw_response)
        except ParseError as exc:
            steps.append(Step(thought=f"Failed to parse response: {exc}"))
            continue

        if parsed.is_final:
            steps.append(Step(thought=parsed.thought))
            return Trace(
                task_id=task_id,
                steps=steps,
                final_answer=str(parsed.final_answer),
                success=True,
                metadata={"steps_taken": len(steps)},
            )

        observation = _execute_action(parsed.action)
        steps.append(Step(thought=parsed.thought, action=parsed.action, observation=observation))

    return Trace(
        task_id=task_id,
        steps=steps,
        final_answer=None,
        success=False,
        metadata={"steps_taken": len(steps), "failure_reason": "max steps exceeded"},
    )
