"""Tests for src/tools/sqlite_query.py."""

import sqlite3
from pathlib import Path

import pytest

from tools import sandbox
from tools.sqlite_query import query_db

FIXTURE_DB = Path(__file__).parent / "fixtures" / "company.db"


@pytest.fixture(autouse=True)
def _use_tmp_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "WORKSPACE_ROOT", tmp_path)


@pytest.fixture
def db_in_workspace(tmp_path):
    """Copy the fixture database into the fake workspace for this test."""
    target = tmp_path / "company.db"
    target.write_bytes(FIXTURE_DB.read_bytes())
    return "company.db"


def test_select_returns_rows(db_in_workspace):
    result = query_db("SELECT name, salary FROM employees WHERE department_id = 1", db_in_workspace)

    assert result.success is True
    names = {row["name"] for row in result.data}
    assert names == {"Alice Chen", "Bruno Silva", "Carla Nguyen"}


def test_select_with_join(db_in_workspace):
    result = query_db(
        """
        SELECT employees.name, departments.name AS department
        FROM employees
        JOIN departments ON employees.department_id = departments.id
        WHERE departments.name = 'Marketing'
        """,
        db_in_workspace,
    )

    assert result.success is True
    assert len(result.data) == 2


def test_rejects_non_select_statements(db_in_workspace):
    result = query_db("DELETE FROM employees", db_in_workspace)

    assert result.success is False
    assert "select" in result.error.lower()


def test_rejects_smuggled_write_after_select(db_in_workspace):
    result = query_db("SELECT 1; DROP TABLE employees;", db_in_workspace)

    assert result.success is False

    # Confirm the table really is untouched, regardless of how it failed.
    connection = sqlite3.connect(FIXTURE_DB)
    try:
        count = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    finally:
        connection.close()
    assert count == 8


def test_missing_database_returns_error():
    result = query_db("SELECT 1", "does_not_exist.db")

    assert result.success is False
    assert "not found" in result.error.lower()


def test_rejects_path_traversal():
    result = query_db("SELECT 1", "../../company.db")

    assert result.success is False
    assert "sandbox" in result.error.lower()


def test_invalid_sql_returns_error(db_in_workspace):
    result = query_db("SELECT * FROM not_a_real_table", db_in_workspace)

    assert result.success is False
    assert result.error is not None
