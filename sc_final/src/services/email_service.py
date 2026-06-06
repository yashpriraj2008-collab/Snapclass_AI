from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

from src.database.client import get_supabase_client, read_app_secrets

DEFAULT_FROM_EMAIL = "SnapClass AI <hello@snapclass.ai>"


def get_secret(key: str, default: str | None = None) -> str | None:
    """Read a secret from Streamlit secrets or env vars."""
    try:
        v = st.secrets.get(key, default)
        return None if v is None else str(v)
    except Exception:
        v = os.getenv(key)
        return v if v is not None else default


def _from_email() -> str:
    # Branded sender in Resend must be "Name <hello@domain>".
    return (
        str(read_app_secrets().get("FROM_EMAIL") or get_secret("FROM_EMAIL") or DEFAULT_FROM_EMAIL).strip()
    )


def _support_email() -> str:
    # Use SUPPORT_EMAIL in secrets; fallback as instructed.
    return str(
        read_app_secrets().get("SUPPORT_EMAIL")
        or get_secret("SUPPORT_EMAIL")
        or "yourgmail@gmail.com"
    ).strip()


# Backward compatibility for existing callers.
# (Previously used CONTACT_NOTIFY_EMAIL / FOUNDER_EMAIL fallbacks.)
def _contact_support_email() -> str:
    return _support_email()



def is_email_configured() -> bool:
    api_key = str(read_app_secrets().get("RESEND_API_KEY") or get_secret("RESEND_API_KEY") or "").strip()
    from_email = _from_email()
    return bool(api_key and from_email)


def _resend_api_key() -> str:
    return str(
        read_app_secrets().get("RESEND_API_KEY")
        or get_secret("RESEND_API_KEY")
        or ""
    ).strip()


def send_email(to_email: str, subject: str, html: str) -> dict[str, Any]:
    api_key = _resend_api_key()
    from_email = _from_email()
    recipient = str(to_email or "").strip()
    subject_text = str(subject or "").strip()

    if not api_key or not from_email:
        return {"ok": False, "error": "Email service is not configured."}
    if not recipient:
        return {"ok": False, "error": "Recipient email is required."}
    if not subject_text:
        return {"ok": False, "error": "Email subject is required."}

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_email,
                "to": [recipient],
                "subject": subject_text,
                "html": str(html or ""),
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        return {"ok": False, "error": _friendly_email_error(exc)}

    if response.status_code in [200, 201]:
        try:
            data = response.json()
        except ValueError:
            data = {}
        return {"ok": True, "data": data}

    return {"ok": False, "error": _friendly_email_error(response.text)}


def _friendly_email_error(error: Exception | str) -> str:
    message = str(error or "")
    lowered = message.lower()
    if "domain" in lowered and ("verify" in lowered or "verified" in lowered):
        return "Email could not be sent because the Resend sender domain is not verified."
    if "api key" in lowered or "unauthorized" in lowered or "forbidden" in lowered:
        return "Email could not be sent because Resend credentials are not configured correctly."
    if "recipient" in lowered or "testing" in lowered:
        return "Email could not be sent because the recipient is not allowed by the current Resend account mode."
    return "Email could not be sent right now. Please check Resend configuration and try again."


def send_low_attendance_alert(
    student_email: str,
    student_name: str,
    subject: str,
    attendance_pct: float,
) -> dict[str, Any]:
    if not is_email_configured():
        return {"ok": False, "message": "Email service is not configured yet."}

    html = f"""
    <div style='font-family:sans-serif;max-width:600px;margin:auto;'>
      <h2 style='color:#5B6CFF;'>SnapClass AI</h2>
      <p>Dear <strong>{student_name}</strong>,</p>
      <p>Your attendance in <strong>{subject}</strong> has dropped to
         <strong style='color:#EF4444;'>{attendance_pct}%</strong>.</p>
      <p>The minimum required attendance is <strong>75%</strong>.</p>
      <p>Please attend classes regularly to avoid academic issues.</p>
      <br>
      <p style='color:#6B7280;font-size:12px;'>
        This is an automated message from SnapClass AI.
      </p>
    </div>
    """

    result = send_email(
        to_email=student_email,
        subject=f"⚠️ Low Attendance Alert — {subject}",
        html=html,
    )

    if result.get("ok"):
        return {"ok": True, "message": f"Alert sent to {student_email}"}
    return {"ok": False, "message": result.get("error") or "Email could not be sent."}


def send_weekly_report(
    teacher_email: str,
    teacher_name: str,
    class_name: str,
    stats: dict[str, Any],
) -> dict[str, Any]:
    if not is_email_configured():
        return {"ok": False, "message": "Email service is not configured yet."}

    html = f"""
    <div style='font-family:sans-serif;max-width:600px;margin:auto;'>
      <h2 style='color:#5B6CFF;'>SnapClass AI — Weekly Report</h2>
      <p>Dear <strong>{teacher_name}</strong>,</p>
      <p>Here is your weekly attendance summary for <strong>{class_name}</strong>:</p>
      <table style='width:100%;border-collapse:collapse;'>
        <tr style='background:#F5F7FF;'>
          <td style='padding:10px;border:1px solid #E5E7EB;'>Total Students</td>
          <td style='padding:10px;border:1px solid #E5E7EB;'><strong>{stats.get('total', 0)}</strong></td>
        </tr>
        <tr>
          <td style='padding:10px;border:1px solid #E5E7EB;'>Average Attendance</td>
          <td style='padding:10px;border:1px solid #E5E7EB;'><strong>{stats.get('avg', 0)}%</strong></td>
        </tr>
        <tr style='background:#F5F7FF;'>
          <td style='padding:10px;border:1px solid #E5E7EB;'>Students Below 75%</td>
          <td style='padding:10px;border:1px solid #E5E7EB;color:#EF4444;'><strong>{stats.get('low', 0)}</strong></td>
        </tr>
      </table>
      <br>
      <p style='color:#6B7280;font-size:12px;'>SnapClass AI — Automated Weekly Report</p>
    </div>
    """

    result = send_email(
        to_email=teacher_email,
        subject=f"📊 Weekly Attendance Report — {class_name}",
        html=html,
    )

    if result.get("ok"):
        return {"ok": True, "message": f"Report sent to {teacher_email}"}
    return {"ok": False, "message": result.get("error") or "Email could not be sent."}


def send_welcome_email(user_email: str, user_name: str, role: str) -> dict[str, Any]:
    if not is_email_configured():
        return {"ok": False, "message": "Email service is not configured yet."}

    app_public_url = read_app_secrets().get("APP_PUBLIC_URL") or "https://your-app.streamlit.app"

    html = f"""
    <div style='font-family:sans-serif;max-width:600px;margin:auto;'>
      <h2 style='color:#5B6CFF;'>Welcome to SnapClass AI! 🎓</h2>
      <p>Hi <strong>{user_name}</strong>,</p>
      <p>Your <strong>{role}</strong> account has been created successfully.</p>
      <p>You can now log in at your school's SnapClass AI portal.</p>
      <br>
      <a href='{app_public_url}'
         style='background:#5B6CFF;color:white;padding:12px 24px;'
               'border-radius:8px;text-decoration:none;'>
        Open SnapClass AI
      </a>
      <br><br>
      <p style='color:#6B7280;font-size:12px;'>SnapClass AI Team</p>
    </div>
    """

    return send_email(
        to_email=user_email,
        subject="Welcome to SnapClass AI 🎓",
        html=html,
    )


def send_contact_notification(message: dict[str, Any]) -> dict[str, Any]:
    if not is_email_configured():
        return {"ok": False, "message": "Email service is not configured yet."}

    inquiry_type = str(message.get("inquiry_type") or "General Question")
    to_email = _support_email()

    html = f"""
    <div style='font-family:sans-serif;max-width:640px;margin:auto;'>
      <h2 style='color:#5B6CFF;'>New SnapClass AI inquiry</h2>
      <p><strong>Type:</strong> {inquiry_type}</p>
      <p><strong>Name:</strong> {message.get('name', '')}</p>
      <p><strong>Institute:</strong> {message.get('institute_name', '') or '-'}</p>
      <p><strong>Email:</strong> {message.get('email', '')}</p>
      <p><strong>Phone/WhatsApp:</strong> {message.get('phone', '') or '-'}</p>
      <p><strong>Student count:</strong> {message.get('student_count', '') or '-'}</p>
      <p><strong>Subject:</strong> {message.get('subject', '')}</p>
      <div style='background:#F5F7FF;border-radius:12px;padding:14px;margin-top:12px;'>
        {message.get('message', '')}
      </div>
    </div>
    """

    try:
        res = send_email(
            to_email=to_email,
            subject=f"New SnapClass AI inquiry: {inquiry_type}",
            html=html,
        )
        if res.get("ok"):
            return {"ok": True, "message": "Founder notification sent."}
        return {"ok": False, "message": res.get("error") or "Email could not be sent."}
    except Exception as exc:
        return {"ok": False, "message": _friendly_email_error(exc)}


def send_contact_autoreply(message: dict[str, Any]) -> dict[str, Any]:
    if not is_email_configured():
        return {"ok": False, "message": "Email service is not configured yet."}

    recipient = str(message.get("email") or "").strip()
    if not recipient:
        return {"ok": False, "message": "Recipient email missing."}

    html = f"""
    <div style='font-family:sans-serif;max-width:600px;margin:auto;'>
      <h2 style='color:#5B6CFF;'>Thanks for contacting SnapClass AI</h2>
      <p>Hi <strong>{message.get('name', 'there')}</strong>,</p>
      <p>We received your message and will reply within 24 hours.</p>
      <p style='color:#6B7280;font-size:12px;'>SnapClass AI Team</p>
    </div>
    """

    res = send_email(
        to_email=recipient,
        subject="We received your SnapClass AI message",
        html=html,
    )
    if res.get("ok"):
        return {"ok": True, "message": "Auto-reply sent."}
    return {"ok": False, "message": res.get("error") or "Email could not be sent."}


def send_test_email(recipient_email: str, sender_user_id: str | None = None) -> dict[str, Any]:
    if not is_email_configured():
        return {"ok": False, "message": "Email service is not configured yet."}

    subject = "SnapClass AI test email"
    html = "<p>SnapClass AI email delivery is configured.</p>"

    log_id: str | None = None
    db = get_supabase_client()

    if db is not None:
        try:
            inserted = (
                db.table("email_logs")
                .insert(
                    {
                        "sender_user_id": sender_user_id,
                        "recipient_email": recipient_email,
                        "recipient_type": "founder_test",
                        "subject": subject,
                        "template_key": "founder_test",
                        "status": "queued",
                        "metadata": {"source": "founder_settings"},
                    }
                )
                .execute()
            )
            rows = inserted.data or []
            log_id = rows[0].get("id") if rows else None
        except Exception:
            log_id = None

    try:
        result = send_email(to_email=recipient_email, subject=subject, html=html)
        data = result.get("data") or {}
        resend_email_id = data.get("id") if isinstance(data, dict) else None

        if db is not None and log_id:
            db.table("email_logs").update(
                {
                    "status": "sent" if result.get("ok") else "failed",
                    "resend_email_id": resend_email_id,
                    "sent_at": __import__("datetime").datetime.utcnow().isoformat(),
                    "error_message": None if result.get("ok") else result.get("error"),
                }
            ).eq("id", log_id).execute()

        if result.get("ok"):
            return {"ok": True, "message": "Test email sent."}
        return {"ok": False, "message": result.get("error") or "Test email failed."}

    except Exception as exc:
        safe_message = _friendly_email_error(exc)
        if db is not None and log_id:
            try:
                db.table("email_logs").update({"status": "failed", "error_message": safe_message}).eq(
                    "id", log_id
                ).execute()
            except Exception:
                pass
        return {"ok": False, "message": safe_message}
