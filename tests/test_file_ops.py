"""Tests for src/tools/file_ops.py."""

import pytest

from tools import file_ops, sandbox


@pytest.fixture(autouse=True)
def _use_tmp_workspace(tmp_path, monkeypatch):
    """Point WORKSPACE_ROOT at a throwaway directory for every test."""
    monkeypatch.setattr(sandbox, "WORKSPACE_ROOT", tmp_path)


def test_write_then_read_file():
    write_result = file_ops.write_file("notes.txt", "hello world")
    assert write_result.success is True

    read_result = file_ops.read_file("notes.txt")
    assert read_result.success is True
    assert read_result.data == "hello world"


def test_write_creates_parent_directories():
    result = file_ops.write_file("reports/summary.txt", "data")

    assert result.success is True
    read_result = file_ops.read_file("reports/summary.txt")
    assert read_result.data == "data"


def test_read_missing_file_returns_error():
    result = file_ops.read_file("does_not_exist.txt")

    assert result.success is False
    assert "not found" in result.error.lower()


def test_read_rejects_path_traversal():
    result = file_ops.read_file("../../some_secret.txt")

    assert result.success is False
    assert "sandbox" in result.error.lower()


def test_write_rejects_path_traversal():
    result = file_ops.write_file("../escape.txt", "malicious")

    assert result.success is False
    assert "sandbox" in result.error.lower()


def test_read_rejects_absolute_path_outside_sandbox(tmp_path):
    outside_file = tmp_path.parent / "outside.txt"
    outside_file.write_text("secret")

    result = file_ops.read_file(str(outside_file))

    assert result.success is False
    assert "sandbox" in result.error.lower()
