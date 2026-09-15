"""Standard fault profiles: pre-defined FaultConfig presets for harness runs."""

from __future__ import annotations

from harness.fault_injector import FaultConfig, FaultType

_ALL_FAULT_TYPES = list(FaultType)


def _even_split(total_probability: float) -> dict[FaultType, float]:
    """Split a total failure rate evenly across every fault type."""
    per_type = total_probability / len(_ALL_FAULT_TYPES)
    return {fault_type: per_type for fault_type in _ALL_FAULT_TYPES}


PROFILES: dict[str, FaultConfig] = {
    "clean": FaultConfig(probabilities={}),
    "light": FaultConfig(probabilities=_even_split(0.10)),
    "heavy": FaultConfig(probabilities=_even_split(0.30)),
    "chaos": FaultConfig(probabilities=_even_split(0.20)),
}


def targeted_profile(tool_name: str, probability: float = 0.50) -> dict[str, FaultConfig]:
    """A profile that only injects faults into one specific tool.

    Returns a per-tool config mapping rather than a single FaultConfig, since
    "targeted" only makes sense in relation to which tool is being wrapped.
    """
    return {tool_name: FaultConfig(probabilities=_even_split(probability))}
