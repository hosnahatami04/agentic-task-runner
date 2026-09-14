"""Tests for src/tools/search.py."""

from pathlib import Path

import pytest

from tools import sandbox
from tools.search import search_files


@pytest.fixture(autouse=True)
def _use_tmp_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "WORKSPACE_ROOT", tmp_path)


def test_finds_matching_line_in_single_file(tmp_path):
    (tmp_path / "notes.txt").write_text("hello\nfind me here\nbye")

    result = search_files("find me", ".")

    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0]["path"] == "notes.txt"
    assert result.data[0]["line_number"] == 2
    assert result.data[0]["line"] == "find me here"


def test_searches_recursively_in_subdirectories(tmp_path):
    subdir = tmp_path / "reports"
    subdir.mkdir()
    (subdir / "summary.txt").write_text("target value: 42")

    result = search_files("target value", ".")

    assert result.success is True
    assert len(result.data) == 1
    expected_path = str(Path("reports") / "summary.txt")
    assert result.data[0]["path"] == expected_path


def test_search_is_case_insensitive(tmp_path):
    (tmp_path / "notes.txt").write_text("Action items:\n- do the thing")

    result = search_files("action items", ".")

    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0]["line"] == "Action items:"


def test_no_matches_returns_empty_list(tmp_path):
    (tmp_path / "notes.txt").write_text("nothing relevant here")

    result = search_files("needle", ".")

    assert result.success is True
    assert result.data == []


def test_ignores_binary_files(tmp_path):
    (tmp_path / "notes.txt").write_text("find me")
    (tmp_path / "image.bin").write_bytes(b"\xff\xfe\x00\x01query")

    result = search_files("find me", ".")

    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0]["path"] == "notes.txt"


def test_rejects_directory_traversal():
    result = search_files("anything", "../../")

    assert result.success is False
    assert "sandbox" in result.error.lower()


def test_missing_directory_returns_error():
    result = search_files("anything", "does_not_exist")

    assert result.success is False
    assert "not found" in result.error.lower()
