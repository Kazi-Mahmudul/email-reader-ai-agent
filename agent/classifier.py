"""Classify emails for importance and priority using OpenAI."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_NAME = "gpt-4o-mini"
ALLOWED_PRIORITIES = {"HIGH", "MEDIUM", "LOW"}
HIGH_URGENCY_CATEGORIES = {
    "PAYMENT_ISSUE",
    "SERVER_DOWN",
    "CLIENT_COMPLAINT",
    "URGENT_REQUEST",
}

SYSTEM_PROMPT = """You classify inbound emails for a B2B SaaS business.

Rules:
- Mark important=true for payment issues, client complaints, server alerts, and urgent requests.
- Mark important=false for spam, newsletters, and generic marketing.
- Always return valid JSON with exactly these fields:
  important (boolean),
  priority ("HIGH" | "MEDIUM" | "LOW"),
  category (string),
  reason (one clear sentence).
- Priority rule:
  HIGH if important and urgent/financial/technical
  MEDIUM if important but not urgent
  LOW if not important
- Do not include any extra keys.
"""


def _build_user_prompt(email: dict[str, Any]) -> str:
    """Create a robust user prompt from email data."""
    return (
        "Classify this email.\n"
        f"id: {email['id']}\n"
        f"from: {email['from']}\n"
        f"subject: {email['subject']}\n"
        f"body: {email['body']}\n"
    )


def _client() -> OpenAI:
    """Return an OpenAI client initialized with OPENAI_API_KEY."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def _normalize_result(data: dict[str, Any]) -> dict:
    """Normalize and validate model output to exact required schema."""
    important = bool(data.get("important", False))
    category = _normalize_category(str(data.get("category", "GENERAL_INQUIRY")))

    priority = str(data.get("priority", "")).upper()
    if not important:
        priority = "LOW"
    elif priority not in ALLOWED_PRIORITIES or priority == "LOW":
        priority = "HIGH" if category in HIGH_URGENCY_CATEGORIES else "MEDIUM"

    reason = str(data.get("reason", "Classified based on subject and body content.")).strip()
    if not reason:
        reason = "Classified based on subject and body content."
    reason = reason.replace("\n", " ").strip()
    if "." in reason:
        reason = reason.split(".", 1)[0].strip() + "."
    elif not reason.endswith("."):
        reason = reason + "."

    return {
        "important": important,
        "priority": priority,
        "category": category,
        "reason": reason,
    }


def _normalize_category(raw_category: str) -> str:
    """Map free-text categories to canonical enum-like labels."""
    normalized = raw_category.strip().upper().replace("-", "_").replace(" ", "_")
    if not normalized:
        return "GENERAL_INQUIRY"

    category_aliases = {
        "PAYMENT_ISSUE": "PAYMENT_ISSUE",
        "PAYMENT_ISSUES": "PAYMENT_ISSUE",
        "BILLING_ISSUE": "PAYMENT_ISSUE",
        "BILLING": "PAYMENT_ISSUE",
        "SERVER_DOWN": "SERVER_DOWN",
        "SERVER_ALERT": "SERVER_DOWN",
        "SERVER_ALERTS": "SERVER_DOWN",
        "TECHNICAL_ALERT": "SERVER_DOWN",
        "TECH_ALERT": "SERVER_DOWN",
        "CLIENT_COMPLAINT": "CLIENT_COMPLAINT",
        "CLIENT_COMPLAINTS": "CLIENT_COMPLAINT",
        "URGENT_REQUEST": "URGENT_REQUEST",
        "URGENT": "URGENT_REQUEST",
        "SPAM": "SPAM",
        "NEWSLETTER": "NEWSLETTER",
        "MEETING_REQUEST": "MEETING_REQUEST",
        "CALENDAR_INVITE": "MEETING_REQUEST",
        "GENERAL_INQUIRY": "GENERAL_INQUIRY",
        "GENERAL_BUSINESS_INQUIRY": "GENERAL_INQUIRY",
        "MARKETING": "SPAM",
        "GENERIC_MARKETING": "SPAM",
    }
    return category_aliases.get(normalized, normalized)


def classify_email(email: dict) -> dict:
    """Classify one email and return importance, priority, category, and reason."""
    required = {"id", "from", "subject", "body"}
    missing = sorted(required - set(email.keys()))
    email_id = email.get("id", "<missing-id>")
    print(f"[CLASSIFIER] Processing email_id: {email_id}")

    if missing:
        error_message = f"Email missing required fields: {missing}"
        print(f"[CLASSIFIER] ERROR: {error_message}")
        raise ValueError(error_message)

    for attempt in range(2):
        try:
            response = _client().chat.completions.create(
                model=MODEL_NAME,
                response_format={"type": "json_object"},
                temperature=0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(email)},
                ],
            )

            raw_content = response.choices[0].message.content or "{}"
            parsed = json.loads(raw_content)
            if not isinstance(parsed, dict):
                raise ValueError("Model response was not a JSON object.")

            result = _normalize_result(parsed)
            print(
                "[CLASSIFIER] Result: "
                f"important={result['important']}, "
                f"priority={result['priority']}, "
                f"category={result['category']}"
            )
            return result
        except Exception as exc:
            print(f"[CLASSIFIER] ERROR: {exc}")
            if attempt == 0:
                time.sleep(2)
                continue

            fallback = {
                "important": False,
                "priority": "LOW",
                "category": "CLASSIFICATION_ERROR",
                "reason": f"AI classification failed: {exc}",
            }
            print(
                "[CLASSIFIER] Result: "
                f"important={fallback['important']}, "
                f"priority={fallback['priority']}, "
                f"category={fallback['category']}"
            )
            return fallback

    # This line is unreachable but keeps static checkers happy.
    return {
        "important": False,
        "priority": "LOW",
        "category": "CLASSIFICATION_ERROR",
        "reason": "AI classification failed: unknown error",
    }


def classify_batch(emails: list[dict]) -> list[dict]:
    """Classify a batch of emails and merge each result with original fields."""
    results: list[dict] = []
    for email in emails:
        try:
            classification = classify_email(email)
            results.append({**email, **classification})
        except Exception as exc:
            email_id = email.get("id", "<missing-id>") if isinstance(email, dict) else "<non-dict>"
            print(f"[ERROR] Failed to classify email {email_id}: {exc}")
            continue
    return results


if __name__ == "__main__":
    test_emails = [
        {
            "id": "test_001",
            "from": "Billing Team <billing@vendor.com>",
            "subject": "Payment failed for your account",
            "body": "We could not process your payment today. Please update your payment method immediately to avoid account interruption.",
        },
        {
            "id": "test_002",
            "from": "Tech Alerts <alerts@monitoring.io>",
            "subject": "Production API latency is critical",
            "body": "Average response time has exceeded 4 seconds for the past 15 minutes. Customer requests are timing out and error rates are rising.",
        },
        {
            "id": "test_003",
            "from": "Marketing Digest <news@adtrends.com>",
            "subject": "Top growth campaigns this week",
            "body": "Here is your weekly marketing digest with campaign benchmarks and ad performance tips. Unsubscribe at any time.",
        },
    ]

    results = classify_batch(test_emails)
    print(json.dumps(results, indent=2))
