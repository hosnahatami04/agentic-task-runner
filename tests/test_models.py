"""Tests for the core Pydantic models in src/agent/models.py."""

from agent.models import Action, Observation, Step, ToolSchema, Trace


def test_tool_schema_round_trip():
    schema = ToolSchema(
        name="read_file",
        description="Reads a file from the workspace.",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
    )

    restored = ToolSchema.model_validate_json(schema.model_dump_json())

    assert restored == schema


def test_action_round_trip():
    action = Action(tool_name="calculate", arguments={"expression": "2 + 2"})

    restored = Action.model_validate_json(action.model_dump_json())

    assert restored == action


def test_action_default_arguments_is_empty_dict():
    action = Action(tool_name="noop")

    assert action.arguments == {}


def test_observation_success():
    observation = Observation(success=True, data={"content": "hello"})

    assert observation.success is True
    assert observation.error is None


def test_observation_failure():
    observation = Observation(success=False, error="file not found")

    assert observation.success is False
    assert observation.data is None


def test_step_without_action_or_observation():
    step = Step(thought="I already have the final answer.")

    assert step.action is None
    assert step.observation is None


def test_step_with_action_and_observation():
    action = Action(tool_name="calculate", arguments={"expression": "1 + 1"})
    observation = Observation(success=True, data=2)
    step = Step(thought="Let me compute this.", action=action, observation=observation)

    restored = Step.model_validate_json(step.model_dump_json())

    assert restored == step


def test_trace_round_trip():
    step = Step(
        thought="Compute 1+1",
        action=Action(tool_name="calculate", arguments={"expression": "1 + 1"}),
        observation=Observation(success=True, data=2),
    )
    trace = Trace(
        task_id="task-001",
        steps=[step],
        final_answer="2",
        success=True,
        metadata={"steps_taken": 1},
    )

    restored = Trace.model_validate_json(trace.model_dump_json())

    assert restored == trace


def test_trace_defaults():
    trace = Trace(task_id="task-002")

    assert trace.steps == []
    assert trace.final_answer is None
    assert trace.success is False
    assert trace.metadata == {}
