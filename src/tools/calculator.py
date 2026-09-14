"""A safe calculator tool: evaluates arithmetic without using eval()."""

from __future__ import annotations

import ast
import operator

from agent.models import Observation

from .registry import tool

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")

    if isinstance(node, ast.BinOp):
        op_func = _OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(_eval_node(node.left), _eval_node(node.right))

    if isinstance(node, ast.UnaryOp):
        op_func = _OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(_eval_node(node.operand))

    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


@tool(
    name="calculate",
    description="Evaluates a math expression (+, -, *, /, %, **) and returns the numeric result.",
    parameters={
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"],
    },
)
def calculate(expression: str) -> Observation:
    """Safely evaluate an arithmetic expression like '2 + 3 * 4'."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        return Observation(success=True, data=result)
    except ZeroDivisionError:
        return Observation(success=False, error="Division by zero")
    except (ValueError, SyntaxError, TypeError) as exc:
        return Observation(success=False, error=f"Invalid expression: {exc}")
