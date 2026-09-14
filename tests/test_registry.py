"""Tests for src/tools/registry.py."""

import pytest

from tools import registry


@pytest.fixture(autouse=True)
def _clear_registry():
    """Each test starts with an empty registry, and cleans up after itself."""
    registry.clear()
    yield
    registry.clear()


def test_tool_decorator_registers_function():
    @registry.tool(
        name="add",
        description="Adds two numbers.",
        parameters={"type": "object", "properties": {"a": {}, "b": {}}},
    )
    def add(a, b):
        return a + b

    assert registry.get_tool("add") is add


def test_registered_function_still_callable_directly():
    @registry.tool(name="add", description="Adds two numbers.", parameters={})
    def add(a, b):
        return a + b

    assert add(2, 3) == 5


def test_get_tool_executes_correctly_through_registry():
    @registry.tool(name="add", description="Adds two numbers.", parameters={})
    def add(a, b):
        return a + b

    func = registry.get_tool("add")

    assert func(2, 3) == 5


def test_get_tool_raises_for_unknown_name():
    with pytest.raises(KeyError):
        registry.get_tool("does_not_exist")


def test_duplicate_registration_raises():
    @registry.tool(name="add", description="Adds two numbers.", parameters={})
    def add(a, b):
        return a + b

    with pytest.raises(ValueError):

        @registry.tool(name="add", description="Another one.", parameters={})
        def add_again(a, b):
            return a + b


def test_list_schemas_returns_registered_tool_schema():
    @registry.tool(
        name="add",
        description="Adds two numbers.",
        parameters={"type": "object", "properties": {"a": {}, "b": {}}},
    )
    def add(a, b):
        return a + b

    schemas = registry.list_schemas()

    assert len(schemas) == 1
    assert schemas[0].name == "add"
    assert schemas[0].description == "Adds two numbers."


def test_list_schemas_empty_when_no_tools_registered():
    assert registry.list_schemas() == []
