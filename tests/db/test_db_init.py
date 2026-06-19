from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from linkup.db.repositories import get_connection, init_db

if TYPE_CHECKING:
    from pathlib import Path


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def test_get_connection_applies_sqlite_settings(initialized_db: Path) -> None:
    with get_connection(initialized_db) as conn:
        row = conn.execute("SELECT 1 AS value").fetchone()
        foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]

    assert isinstance(row, sqlite3.Row)
    assert row["value"] == 1
    assert foreign_keys == 1
    assert journal_mode == "wal"


def test_init_db_applies_v2_schema_and_is_idempotent(initialized_db: Path) -> None:
    init_db(initialized_db)

    with get_connection(initialized_db) as conn:
        user_columns = _columns(conn, "User_Profile")
        log_columns = _columns(conn, "Daily_Log")
        history_columns = _columns(conn, "Workout_History")
        session_columns = _columns(conn, "Workout_Session")
        db_version = conn.execute("SELECT value FROM App_Settings WHERE key = 'db_version'").fetchone()["value"]
        trigger_names = {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'").fetchall()
        }

    assert {"gender", "goals", "pushup_max", "plank_max_sec", "squat_max"} <= user_columns
    assert {"mental_condition_score", "outdoor_hours", "fatigue_by_part"} <= log_columns
    assert "status" in history_columns
    assert "memo" in session_columns
    assert db_version == "2"
    assert {
        "trg_user_profile_updated_at",
        "trg_session_calc_duration",
        "trg_session_require_daily_log",
    } <= trigger_names
