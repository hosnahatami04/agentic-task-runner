"""Tests for src/harness/profiles.py."""

from harness.fault_injector import FaultType
from harness.profiles import PROFILES, targeted_profile


def test_clean_profile_has_no_faults():
    assert PROFILES["clean"].probabilities == {}


def test_light_profile_sums_to_ten_percent():
    total = sum(PROFILES["light"].probabilities.values())
    assert round(total, 4) == 0.10


def test_heavy_profile_sums_to_thirty_percent():
    total = sum(PROFILES["heavy"].probabilities.values())
    assert round(total, 4) == 0.30


def test_chaos_profile_sums_to_twenty_percent():
    total = sum(PROFILES["chaos"].probabilities.values())
    assert round(total, 4) == 0.20


def test_all_profiles_cover_every_fault_type():
    for name in ("light", "heavy", "chaos"):
        assert set(PROFILES[name].probabilities.keys()) == set(FaultType)


def test_targeted_profile_only_affects_named_tool():
    config = targeted_profile("query_db", probability=0.5)

    assert list(config.keys()) == ["query_db"]
    assert round(sum(config["query_db"].probabilities.values()), 4) == 0.5
