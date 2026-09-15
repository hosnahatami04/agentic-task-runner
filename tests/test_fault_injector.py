"""Tests for src/harness/fault_injector.py."""

import random

import pytest

from agent.models import Observation
from harness.fault_injector import (
    FaultConfig,
    FaultType,
    TimeoutError_,
    wrap_tool,
)


def _always_seed(value: float) -> random.Random:
    """A fake RNG whose .random() always returns the given value."""

    class _FixedRandom(random.Random):
        def random(self) -> float:
            return value

    return _FixedRandom()


def test_no_faults_configured_calls_real_tool():
    def real_tool(x):
        return x * 2

    wrapped = wrap_tool(real_tool, FaultConfig(probabilities={}), rng=_always_seed(0.0))

    assert wrapped(5) == 10


def test_fault_never_triggers_below_threshold():
    def real_tool(x):
        return x * 2

    config = FaultConfig(probabilities={FaultType.CORRUPT_OUTPUT: 0.1})
    wrapped = wrap_tool(real_tool, config, rng=_always_seed(0.5))

    assert wrapped(5) == 10


def test_permission_error_fault():
    def real_tool():
        return Observation(success=True, data="secret")

    config = FaultConfig(probabilities={FaultType.PERMISSION_ERROR: 1.0})
    wrapped = wrap_tool(real_tool, config, rng=_always_seed(0.0))

    result = wrapped()

    assert result.success is False
    assert "permission" in result.error.lower()


def test_corrupt_output_fault():
    def real_tool():
        return Observation(success=True, data="clean data")

    config = FaultConfig(probabilities={FaultType.CORRUPT_OUTPUT: 1.0})
    wrapped = wrap_tool(real_tool, config, rng=_always_seed(0.0))

    result = wrapped()

    assert result.success is True
    assert result.data != "clean data"


def test_irrelevant_output_fault():
    def real_tool():
        return Observation(success=True, data="42")

    config = FaultConfig(probabilities={FaultType.IRRELEVANT_OUTPUT: 1.0})
    wrapped = wrap_tool(real_tool, config, rng=_always_seed(0.0))

    result = wrapped()

    assert result.success is True
    assert result.data != "42"


def test_partial_failure_truncates_string_data():
    def real_tool():
        return Observation(success=True, data="0123456789")

    config = FaultConfig(probabilities={FaultType.PARTIAL_FAILURE: 1.0})
    wrapped = wrap_tool(real_tool, config, rng=_always_seed(0.0))

    result = wrapped()

    assert result.success is True
    assert result.data == "01234"


def test_timeout_fault_raises():
    def real_tool():
        return Observation(success=True, data="fine")

    config = FaultConfig(probabilities={FaultType.TIMEOUT: 1.0})
    wrapped = wrap_tool(real_tool, config, rng=_always_seed(0.0))

    with pytest.raises(TimeoutError_):
        wrapped()


def test_first_matching_fault_type_wins():
    def real_tool():
        return Observation(success=True, data="fine")

    config = FaultConfig(
        probabilities={
            FaultType.PERMISSION_ERROR: 1.0,
            FaultType.CORRUPT_OUTPUT: 1.0,
        }
    )
    wrapped = wrap_tool(real_tool, config, rng=_always_seed(0.0))

    result = wrapped()

    assert "permission" in result.error.lower()
