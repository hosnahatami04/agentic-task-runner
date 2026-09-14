"""Builds a small, realistic company SQLite database used as a task fixture.

Run directly to (re)generate tests/fixtures/company.db:
    python tests/fixtures/build_company_db.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "company.db"

DEPARTMENTS = [
    (1, "Engineering"),
    (2, "Sales"),
    (3, "Marketing"),
    (4, "Human Resources"),
]

EMPLOYEES = [
    (1, "Alice Chen", 1, 95000),
    (2, "Bruno Silva", 1, 88000),
    (3, "Carla Nguyen", 1, 102000),
    (4, "David Kim", 2, 72000),
    (5, "Elena Rossi", 2, 76000),
    (6, "Farid Hosseini", 3, 65000),
    (7, "Grace Okafor", 3, 68000),
    (8, "Hana Sato", 4, 60000),
]


def build() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute(
            """
            CREATE TABLE departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department_id INTEGER NOT NULL REFERENCES departments(id),
                salary INTEGER NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO departments (id, name) VALUES (?, ?)", DEPARTMENTS
        )
        connection.executemany(
            "INSERT INTO employees (id, name, department_id, salary) VALUES (?, ?, ?, ?)",
            EMPLOYEES,
        )
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    build()
    print(f"Built {DB_PATH}")
