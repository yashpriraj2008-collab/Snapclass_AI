"""Contact/lead capture helpers for the public Contact page and Founder HQ."""
from __future__ import annotations

import os
import re
from typing import Any

from postgrest.types import ReturnMethod

from src.database.client import get_supabase_client, read_app_secrets

try:
    import streamlit as st  # used only for APP_ENV hiding of debug
except Exception:  # pragma: no cover
    st = None

from src.services.email_service import send_contact_autoreply, send_contact_notification

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")

INQUIRY_TYPES = [
    "Book a Demo",
    "Pricing",
    "Technical Support",
    "Partnership",
    "General Question",
]

STUDENT_COUNTS = [
    "Under 50",
    "50-200",
    "200-1000",
    "1000+",
]

CONTACT_STATUSES = ["new", "contacted", "closed", "spam"]


def _debug_enabled() -> bool:
    try:
        if st is not None and bool(st.session_state.get("debug_mode")):
            return True
    except Exception:
        pass
    try:
        env = str(os.getenv("APP_ENV") or read_app_secrets().get("APP_ENV") or "production").strip().lower()
    except Exception:
        env = "production"
    return env == "development"


def _text(value: Any) -> str:
    return str(value or "").strip()


def validate_contact_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _text(payload.get("name")):
        errors.append("Full name is required.")
    if not EMAIL_RE.match(_text(payload.get("email")).lower()):
        errors.append("Enter a valid email address.")
    phone = _text(payload.get("phone"))
    if not phone:
        errors.append("Phone or WhatsApp number is required.")
    elif not PHONE_RE.match(phone):
        errors.append("Enter a valid phone or WhatsApp number.")
    if _text(payload.get("inquiry_type")) not in INQUIRY_TYPES:
        errors.append("Select an inquiry type.")
    if not _text(payload.get("subject")):
        errors.append("Subject is required.")
    message = _text(payload.get("message"))
    if not message:
        errors.append("Message is required.")
    elif len(message) < 10:
        errors.append("Message should be at least 10 characters.")
    if _text(payload.get("website")):
        errors.append("Message could not be submitted.")
    return errors


def submit_contact_message(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate, save, and optionally email a public contact message."""

    # Map UI payload into DB schema columns.
    normalized: dict[str, Any] = {
        "name": _text(payload.get("full_name") or payload.get("name")),
        "institute_name": _text(payload.get("institute_name")),
        "email": _text(payload.get("email")).lower(),
        "phone": _text(payload.get("phone")),
        "inquiry_type": _text(payload.get("inquiry_type")),
        "student_count": _text(payload.get("student_count")),
        "subject": _text(payload.get("subject")),
        "message": _text(payload.get("message")),
        "status": _text(payload.get("status")) or "new",
        "source": _text(payload.get("source")) or "landing_contact_form",
    }

    # Store extra metadata inside `message` because schema only has `message`.
    extra_bits: list[str] = []
    role = _text(payload.get("role"))
    preferred_contact = _text(payload.get("preferred_contact"))
    if role:
        extra_bits.append(f"Role: {role}")
    if preferred_contact:
        extra_bits.append(f"Preferred contact: {preferred_contact}")

    if extra_bits:
        normalized["message"] = f"{normalized['message']}\n\n" + "\n".join(extra_bits)

    errors = validate_contact_payload({**normalized, "website": payload.get("website")})
    if errors:
        return {"ok": False, "message": " ".join(errors), "validation": True}

    db = get_supabase_client()
    if not db:
        return {
            "ok": False,
            "message": "Message could not be saved. Please email hello@snapclass.ai.",
            "supabase_unavailable": True,
        }

    try:
        db.table("contact_messages").insert(normalized, returning=ReturnMethod.minimal).execute()
        row = normalized
    except Exception as exc:
        result: dict[str, Any] = {
            "ok": False,
            "message": "Message could not be saved. Please email hello@snapclass.ai.",
        }
        if _debug_enabled():
            result["debug"] = str(exc)
        return result

    notification = send_contact_notification(row)
    autoreply = send_contact_autoreply(row)

    return {
        "ok": True,
        "message": "Message sent! We'll get back to you within 24 hours.",
        "data": row,
        "email_notification": notification,
        "email_autoreply": autoreply,
    }

def list_contact_messages() -> dict[str, Any]:
    db = get_supabase_client()
    if not db:
        return {"ok": False, "message": "Unable to load data. Please retry.", "data": []}

    try:
        rows = (
            db.table("contact_messages")
            .select("*")
            .order("created_at", desc=True)
            .limit(200)
            .execute()
            .data
            or []
        )
        return {"ok": True, "data": rows}
    except Exception as exc:
        return {"ok": False, "message": "Unable to load data. Please retry.", "data": [], "debug": str(exc)}


def update_contact_status(message_id: str, status: str) -> dict[str, Any]:
    db = get_supabase_client()
    if not db:
        return {"ok": False, "message": "Unable to update status. Please retry."}
    if status not in CONTACT_STATUSES:
        return {"ok": False, "message": "Invalid status."}
    if not _text(message_id):
        return {"ok": False, "message": "Missing message id."}

    try:
        db.table("contact_messages").update({"status": status}).eq("id", message_id).execute()
        return {"ok": True, "message": f"Lead marked {status}."}
    except Exception as exc:
        return {"ok": False, "message": "Unable to update status. Please retry.", "debug": str(exc)}


def resend_configured() -> bool:
    key = str(read_app_secrets().get("RESEND_API_KEY", "") or "").strip()
    return bool(key and key != "re_your_key_here")
