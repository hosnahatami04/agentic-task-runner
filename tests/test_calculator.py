"""Tests for src/tools/calculator.py."""

from tools.calculator import calculate


def test_addition():
    result = calculate("2 + 3")

    assert result.success is True
    assert result.data == 5


def test_operator_precedence():
    result = calculate("2 + 3 * 4")

    assert result.success is True
    assert result.data == 14


def test_negative_numbers():
    result = calculate("-5 + 10")

    assert result.success is True
    assert result.data == 5


def test_power_and_modulo():
    result = calculate("2 ** 10 % 100")

    assert result.success is True
    assert result.data == 24


def test_division():
    result = calculate("10 / 4")

    assert result.success is True
    assert result.data == 2.5


def test_division_by_zero_is_handled():
    result = calculate("1 / 0")

    assert result.success is False
    assert "zero" in result.error.lower()


def test_invalid_syntax_is_handled():
    result = calculate("2 + * 3")

    assert result.success is False
    assert result.error is not None


def test_rejects_function_calls():
    result = calculate("__import__('os').system('echo hi')")

    assert result.success is False
    assert result.error is not None


def test_rejects_arbitrary_names():
    result = calculate("x + 1")

    assert result.success is False
    assert result.error is not None
