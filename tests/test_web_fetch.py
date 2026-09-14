"""Tests for src/tools/web_fetch.py."""

from tools.web_fetch import web_fetch


def test_fetches_known_url():
    result = web_fetch("https://example.com/company-handbook")

    assert result.success is True
    assert "timesheets" in result.data


def test_fetches_second_known_url():
    result = web_fetch("https://example.com/holiday-schedule")

    assert result.success is True
    assert "New Year" in result.data


def test_unknown_url_returns_error():
    result = web_fetch("https://example.com/does-not-exist")

    assert result.success is False
    assert "not reachable" in result.error.lower()
