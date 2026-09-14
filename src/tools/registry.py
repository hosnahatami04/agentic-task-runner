"""Registry that tools sign up with via the @tool decorator."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agent.models import ToolSchema

_registry: dict[str, Callable[..., Any]] = {}
_schemas: dict[str, ToolSchema] = {}


def tool(name: str, description: str, parameters: dict[str, Any]) -> Callable:
    """Decorator that registers a function as an agent tool.

    Usage:
        @tool(
            name="calculate",
            description="Evaluates a math expression.",
            parameters={"type": "object", "properties": {"expression": {"type": "string"}}},
        )
        def calculate(expression: str) -> float:
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if name in _registry:
            raise ValueError(f"Tool '{name}' is already registered")

        _registry[name] = func
        _schemas[name] = ToolSchema(
            name=name,
            description=description,
            parameters=parameters,
        )
        return func

    return decorator


def get_tool(name: str) -> Callable[..., Any]:
    """Look up a registered tool's function by name."""
    if name not in _registry:
        raise KeyError(f"No tool registered with name '{name}'")
    return _registry[name]


def list_schemas() -> list[ToolSchema]:
    """Return the schemas of all registered tools, for building the system prompt."""
    return list(_schemas.values())


def clear() -> None:
    """Remove all registered tools. Intended for use in tests."""
    _registry.clear()
    _schemas.clear()
