"""Load and filter mock email data from a JSON file."""

from __future__ import annotations

import json
import os
from pathlib import Path

REQUIRED_FIELDS = {"id", "from", "subject", "body", "received_at"}


def _mock_file_path() -> Path:
    """Resolve the mock email JSON path from environment or default value."""
    raw_path = os.getenv("MOCK_EMAIL_PATH", "mock_data/emails.json")
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parents[1] / path


def load_mock_emails() -> list[dict]:
    """Load emails from JSON and return only entries with required fields."""
    path = _mock_file_path()
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    valid_emails: list[dict] = []
    for index, email in enumerate(data):
        if not isinstance(email, dict):
            print(f"[WARN] Skipping email at index {index}: expected object.")
            continue

        missing = REQUIRED_FIELDS - set(email.keys())
        if missing:
            print(
                f"[WARN] Skipping email at index {index}: missing fields {sorted(missing)}."
            )
            continue

        valid_emails.append(email)

    return valid_emails


def get_unprocessed_emails(processed_ids: list[str]) -> list[dict]:
    """Return only emails whose ids are not in processed_ids."""
    processed_set = set(processed_ids)
    return [email for email in load_mock_emails() if email.get("id") not in processed_set]


def get_email_by_id(email_id: str) -> dict | None:
    """Return a single email matching email_id, or None when not found."""
    for email in load_mock_emails():
        if email.get("id") == email_id:
            return email
    return None


if __name__ == "__main__":
    emails = load_mock_emails()
    print(f"Loaded {len(emails)} emails.")
    for email in emails:
        print(email["subject"])
