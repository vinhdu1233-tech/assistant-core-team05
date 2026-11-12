import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MIGRATE_SCRIPT = ROOT / "scripts" / "migrate.py"

EXPECTED_TABLES = {
    "chat_session",
    "interaction",
    "feedback",
    "faq",
    "schema_version",
}


def run_migrations(db_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MIGRATE_SCRIPT), str(db_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def test_migrations_create_expected_schema(tmp_path):
    db_path = tmp_path / "test.db"

    run_migrations(db_path)

    with sqlite3.connect(db_path) as con:
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        versions = {row[0] for row in con.execute("SELECT name FROM schema_version")}

    assert EXPECTED_TABLES <= tables
    assert versions == {"001_init.sql", "002_add_faq.sql"}


def test_migrations_are_idempotent(tmp_path):
    db_path = tmp_path / "test.db"

    first_run = run_migrations(db_path)
    second_run = run_migrations(db_path)

    assert "apply 001_init.sql" in first_run.stdout
    assert "apply 002_add_faq.sql" in first_run.stdout
    assert "skip  001_init.sql" in second_run.stdout
    assert "skip  002_add_faq.sql" in second_run.stdout

    with sqlite3.connect(db_path) as con:
        versions = con.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]

    assert versions == 2


def test_migrations_define_expected_foreign_keys(tmp_path):
    db_path = tmp_path / "test.db"
    run_migrations(db_path)

    with sqlite3.connect(db_path) as con:
        interaction_fks = {(row[2], row[3], row[4]) for row in con.execute("PRAGMA foreign_key_list(interaction)")}
        feedback_fks = {(row[2], row[3], row[4]) for row in con.execute("PRAGMA foreign_key_list(feedback)")}

    assert ("chat_session", "session_id", "id") in interaction_fks
    assert ("interaction", "request_id", "request_id") in feedback_fks


def test_foreign_key_constraints_reject_invalid_rows(tmp_path):
    db_path = tmp_path / "test.db"
    run_migrations(db_path)

    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1

        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO interaction
                    (request_id, session_id, intent, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ("bad-request", "missing-session", "fee", "2026-11-12"),
            )
        con.rollback()

        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO feedback (request_id, rating, created_at)
                VALUES (?, ?, ?)
                """,
                ("missing-request", 1, "2026-11-12"),
            )
        con.rollback()


def test_data_persists_after_reconnecting(tmp_path):
    db_path = tmp_path / "test.db"
    run_migrations(db_path)

    # Open the first connection and insert data.
    with closing(sqlite3.connect(db_path)) as con:
        with con:
            con.execute(
                """
                INSERT INTO chat_session (id, channel, created_at)
                VALUES (?, ?, ?)
                """,
                ("m4-session", "web", "2026-11-12"),
            )
            con.execute(
                """
                INSERT INTO interaction
                    (request_id, session_id, intent, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ("m4-request", "m4-session", "fee", "2026-11-12"),
            )

    # The first connection is now closed.
    # Open a new connection to verify persistence.
    with closing(sqlite3.connect(db_path)) as con:
        session = con.execute(
            "SELECT id, channel FROM chat_session WHERE id = ?",
            ("m4-session",),
        ).fetchone()

        interaction = con.execute(
            """
            SELECT request_id, session_id, intent
            FROM interaction
            WHERE request_id = ?
            """,
            ("m4-request",),
        ).fetchone()

    assert session == ("m4-session", "web")
    assert interaction == ("m4-request", "m4-session", "fee")


def test_feedback_rating_constraint_rejects_invalid_value(tmp_path):
    db_path = tmp_path / "test.db"
    run_migrations(db_path)

    with closing(sqlite3.connect(db_path)) as con:
        con.execute("PRAGMA foreign_keys = ON")

        # Create valid parent records first.
        with con:
            con.execute(
                """
                INSERT INTO chat_session (id, channel, created_at)
                VALUES (?, ?, ?)
                """,
                ("session-1", "web", "2026-11-12"),
            )
            con.execute(
                """
                INSERT INTO interaction
                    (request_id, session_id, intent, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ("request-1", "session-1", "fee", "2026-11-12"),
            )

        # Rating 5 violates CHECK (rating IN (-1, 0, 1)).
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO feedback (request_id, rating, created_at)
                VALUES (?, ?, ?)
                """,
                ("request-1", 5, "2026-11-12"),
            )
