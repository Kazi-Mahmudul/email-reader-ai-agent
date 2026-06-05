"""FastAPI app for polling, classifying, and managing email notifications."""

from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .classifier import classify_email
    from .email_loader import get_unprocessed_emails, load_mock_emails
    from .storage import get_all_processed_ids, init_db, mark_processed
except ImportError:
    from classifier import classify_email
    from email_loader import get_unprocessed_emails, load_mock_emails
    from storage import get_all_processed_ids, init_db, mark_processed

load_dotenv(find_dotenv())

app = FastAPI(title="AI Email Reading Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

notifications: list[dict] = []
db_ready = False


@app.on_event("startup")
def startup_event() -> None:
    """Initialize database table on app startup."""
    global db_ready
    if not os.getenv("OPENAI_API_KEY", "").strip():
        print("[AGENT] WARNING: OPENAI_API_KEY not set. Classification will fail.")
    init_db()
    db_ready = True
    print("[AGENT] Started. DB ready.")


@app.post("/api/trigger-poll")
def trigger_poll() -> dict:
    """Poll mock emails, classify unprocessed entries, and update notifications."""
    print("[POLL] Starting poll cycle...")
    all_emails = load_mock_emails()
    processed_ids = get_all_processed_ids()
    unprocessed = get_unprocessed_emails(processed_ids)

    processed_count = 0
    new_notifications = 0

    # Safety check to avoid acting on stale IDs if source changed unexpectedly.
    all_ids = {email.get("id") for email in all_emails}
    unprocessed = [email for email in unprocessed if email.get("id") in all_ids]
    print(f"[POLL] Found {len(unprocessed)} unprocessed emails")

    for email in unprocessed:
        email_id = email["id"]
        classification = classify_email(email)
        merged = {**email, **classification}

        if classification["important"]:
            if not any(item.get("id") == email_id for item in notifications):
                notifications.append(merged)
                new_notifications += 1

        mark_processed(email_id)
        processed_count += 1

    print(f"[POLL] New notifications added: {new_notifications}")
    print("[POLL] Poll cycle complete.")
    return {"processed": processed_count, "new_notifications": new_notifications}


@app.get("/api/notifications")
def get_notifications() -> list[dict]:
    """Return current in-memory notifications sorted by newest received_at first."""
    return sorted(
        notifications,
        key=lambda item: item.get("received_at", ""),
        reverse=True,
    )


@app.get("/api/notifications/stats")
def get_notification_stats() -> dict:
    """Return summary counts for in-memory notifications."""
    by_priority = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    by_category: dict[str, int] = {}

    for item in notifications:
        priority = str(item.get("priority", "LOW")).upper()
        if priority not in by_priority:
            by_priority[priority] = 0
        by_priority[priority] += 1

        category = str(item.get("category", "UNKNOWN")).upper()
        by_category[category] = by_category.get(category, 0) + 1

    return {
        "total": len(notifications),
        "by_priority": by_priority,
        "by_category": by_category,
    }


@app.delete("/api/notifications/{email_id}")
def delete_notification(email_id: str) -> dict:
    """Delete one notification by id from in-memory storage."""
    for index, item in enumerate(notifications):
        if item.get("id") == email_id:
            notifications.pop(index)
            return {"deleted": True}
    return {"deleted": False}


@app.get("/api/health")
def health() -> dict:
    """Return service and DB readiness status."""
    return {"status": "ok", "notification_count": len(notifications), "db_ready": db_ready}
