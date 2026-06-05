"""Storage helpers for tracking processed emails in Neon PostgreSQL."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def _database_url() -> str:
    """Return the Neon connection string from environment variables."""
    database_url = os.getenv("NEON_DATABASE_URL", "").strip()
    if not database_url:
        raise ValueError("NEON_DATABASE_URL is not set.")
    return database_url


def init_db() -> None:
    """Create the processed_emails table if it does not already exist."""
    try:
        with psycopg2.connect(_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS processed_emails (
                        id TEXT PRIMARY KEY,
                        processed_at TEXT
                    )
                    """
                )
                conn.commit()
        print("[DB] Connected to Neon. Table ready.")
    except Exception as exc:
        print(f"[DB] Error in init_db: {exc}")
        raise


def is_processed(email_id: str) -> bool:
    """Return True when an email id exists in processed_emails."""
    try:
        with psycopg2.connect(_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM processed_emails WHERE id = %s LIMIT 1",
                    (email_id,),
                )
                return cur.fetchone() is not None
    except Exception as exc:
        print(f"[DB] Error in is_processed: {exc}")
        raise


def mark_processed(email_id: str) -> None:
    """Insert an email id into processed_emails and ignore duplicates."""
    processed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        with psycopg2.connect(_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO processed_emails (id, processed_at)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (email_id, processed_at),
                )
                conn.commit()
    except Exception as exc:
        print(f"[DB] Error in mark_processed: {exc}")
        raise


def get_all_processed_ids() -> list[str]:
    """Return all processed email ids from the database."""
    try:
        with psycopg2.connect(_database_url()) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM processed_emails ORDER BY id")
                return [row[0] for row in cur.fetchall()]
    except Exception as exc:
        print(f"[DB] Error in get_all_processed_ids: {exc}")
        raise


if __name__ == "__main__":
    test_email_id = f"email_test_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    tests = [
        ("init_db", lambda: (init_db(), True)[1]),
        ("is_processed (before mark)", lambda: is_processed(test_email_id) is False),
        ("mark_processed", lambda: (mark_processed(test_email_id), True)[1]),
        ("is_processed (after mark)", lambda: is_processed(test_email_id) is True),
        (
            "get_all_processed_ids",
            lambda: test_email_id in get_all_processed_ids(),
        ),
    ]

    for name, test_fn in tests:
        try:
            result = test_fn()
            print(f"[TEST] {name}: {'PASS' if result else 'FAIL'}")
        except Exception as exc:
            print(f"[TEST] {name}: FAIL ({exc})")
