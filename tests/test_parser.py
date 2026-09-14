"""Tests for src/agent/parser.py."""

import pytest

from agent.parser import ParseError, parse_response


def test_parses_clean_json_action():
    raw = '{"thought": "I should calculate", "action": {"tool_name": "calculate", "arguments": {"expression": "2+2"}}}'

    result = parse_response(raw)

    assert result.is_final is False
    assert result.thought == "I should calculate"
    assert result.action.tool_name == "calculate"
    assert result.action.arguments == {"expression": "2+2"}


def test_parses_final_answer():
    raw = '{"thought": "I have the answer", "final_answer": "42"}'

    result = parse_response(raw)

    assert result.is_final is True
    assert result.final_answer == "42"
    assert result.action is None


def test_parses_json_wrapped_in_markdown_fence():
    raw = '```json\n{"thought": "ok", "final_answer": "done"}\n```'

    result = parse_response(raw)

    assert result.is_final is True
    assert result.final_answer == "done"


def test_parses_json_wrapped_in_plain_fence():
    raw = '```\n{"thought": "ok", "final_answer": "done"}\n```'

    result = parse_response(raw)

    assert result.final_answer == "done"


def test_repairs_trailing_comma():
    raw = '{"thought": "ok", "final_answer": "done",}'

    result = parse_response(raw)

    assert result.final_answer == "done"


def test_missing_action_and_final_answer_raises():
    raw = '{"thought": "just thinking"}'

    with pytest.raises(ParseError):
        parse_response(raw)


def test_completely_invalid_json_raises():
    raw = "this is not json at all"

    with pytest.raises(ParseError):
        parse_response(raw)


def test_action_missing_tool_name_raises():
    raw = '{"thought": "ok", "action": {"arguments": {}}}'

    with pytest.raises(ParseError):
        parse_response(raw)


def test_non_object_json_raises():
    raw = "[1, 2, 3]"

    with pytest.raises(ParseError):
        parse_response(raw)
