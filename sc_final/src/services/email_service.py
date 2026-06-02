import streamlit as st
from typing import Any

from src.database.client import get_supabase_client, read_app_secrets


DEFAULT_SENDER_EMAIL = "noreply@snapclass.ai"


def _sender_email() -> str:
    return str(read_app_secrets().get("SENDER_EMAIL") or DEFAULT_SENDER_EMAIL).strip()


def _get_resend():
    try:
        import resend  # type: ignore

        # API key can be blank in local/dev; caller handles failures.
        resend.api_key = read_app_secrets().get("RESEND_API_KEY", "")
        return resend
    except ImportError:
        return None


def _friendly_email_error(error: Exception) -> str:
    """Return a user-safe Resend failure message."""
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
    """
    Sends an email alert to a student when their attendance is below threshold.
    Returns: {"ok": bool, "message": str}
    """
    resend = _get_resend()
    if resend is None:
        return {"ok": False, "message": "Email service is not configured yet."}

    sender = _sender_email()

    try:
        resend.Emails.send(
            {
                "from": sender,
                "to": student_email,
                "subject": f"⚠️ Low Attendance Alert — {subject}",
                "html": f"""
                <div style="font-family:sans-serif;max-width:600px;margin:auto;">
                  <h2 style="color:#5B6CFF;">SnapClass AI</h2>
                  <p>Dear <strong>{student_name}</strong>,</p>
                  <p>Your attendance in <strong>{subject}</strong> has dropped to
                     <strong style="color:#EF4444;">{attendance_pct}%</strong>.</p>
                  <p>The minimum required attendance is <strong>75%</strong>.</p>
                  <p>Please attend classes regularly to avoid academic issues.</p>
                  <br>
                  <p style="color:#6B7280;font-size:12px;">
                    This is an automated message from SnapClass AI.
                  </p>
                </div>
                """,
            }
        )
        return {"ok": True, "message": f"Alert sent to {student_email}"}
    except Exception as e:
        return {"ok": False, "message": _friendly_email_error(e)}


def send_weekly_report(
    teacher_email: str,
    teacher_name: str,
    class_name: str,
    stats: dict[str, Any],
) -> dict[str, Any]:
    """
    Sends a weekly attendance report to a teacher.
    `stats` expects keys: total, avg, low (but tolerates missing keys).
    """
    resend = _get_resend()
    if resend is None:
        return {"ok": False, "message": "Email service is not configured yet."}


    sender = _sender_email()
    try:
        resend.Emails.send(
            {
                "from": sender,
                "to": teacher_email,
                "subject": f"📊 Weekly Attendance Report — {class_name}",
                "html": f"""
                <div style="font-family:sans-serif;max-width:600px;margin:auto;">
                  <h2 style="color:#5B6CFF;">SnapClass AI — Weekly Report</h2>
                  <p>Dear <strong>{teacher_name}</strong>,</p>
                  <p>Here is your weekly attendance summary for <strong>{class_name}</strong>:</p>
                  <table style="width:100%;border-collapse:collapse;">
                    <tr style="background:#F5F7FF;">
                      <td style="padding:10px;border:1px solid #E5E7EB;">Total Students</td>
                      <td style="padding:10px;border:1px solid #E5E7EB;"><strong>{stats.get("total", 0)}</strong></td>
                    </tr>
                    <tr>
                      <td style="padding:10px;border:1px solid #E5E7EB;">Average Attendance</td>
                      <td style="padding:10px;border:1px solid #E5E7EB;"><strong>{stats.get("avg", 0)}%</strong></td>
                    </tr>
                    <tr style="background:#F5F7FF;">
                      <td style="padding:10px;border:1px solid #E5E7EB;">Students Below 75%</td>
                      <td style="padding:10px;border:1px solid #E5E7EB;color:#EF4444;"><strong>{stats.get("low", 0)}</strong></td>
                    </tr>
                  </table>
                  <br>
                  <p style="color:#6B7280;font-size:12px;">SnapClass AI — Automated Weekly Report</p>
                </div>
                """,
            }
        )
        return {"ok": True, "message": f"Report sent to {teacher_email}"}
    except Exception as e:
        return {"ok": False, "message": _friendly_email_error(e)}


def send_welcome_email(user_email: str, user_name: str, role: str) -> dict[str, Any]:
    resend = _get_resend()
    if resend is None:
        return {"ok": False, "message": "resend not installed"}

    sender = _sender_email()
    try:
        resend.Emails.send(
            {
                "from": sender,
                "to": user_email,
                "subject": "Welcome to SnapClass AI 🎓",
                "html": f"""
                <div style="font-family:sans-serif;max-width:600px;margin:auto;">
                  <h2 style="color:#5B6CFF;">Welcome to SnapClass AI! 🎓</h2>
                  <p>Hi <strong>{user_name}</strong>,</p>
                  <p>Your <strong>{role}</strong> account has been created successfully.</p>
                  <p>You can now log in at your school's SnapClass AI portal.</p>
                  <br>
                  <a href="{read_app_secrets().get("APP_PUBLIC_URL", "https://your-app.streamlit.app")}"
                     style="background:#5B6CFF;color:white;padding:12px 24px;
                            border-radius:8px;text-decoration:none;">
                    Open SnapClass AI
                  </a>
                  <br><br>
                  <p style="color:#6B7280;font-size:12px;">SnapClass AI Team</p>
                </div>
                """,
            }
        )
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "message": _friendly_email_error(e)}


def _contact_support_email() -> str:
    secrets = read_app_secrets()
    return str(
        secrets.get("CONTACT_NOTIFY_EMAIL")
        or secrets.get("SUPPORT_EMAIL")
        or secrets.get("FOUNDER_EMAIL")
        or "hello@snapclass.ai"
    ).strip()


def _resend_ready() -> bool:
    key = str(read_app_secrets().get("RESEND_API_KEY", "") or "").strip()
    return bool(key and key != "re_your_key_here")


def send_contact_notification(message: dict[str, Any]) -> dict[str, Any]:
    """Notify founder/support about a new public inquiry."""
    if not _resend_ready():
        return {"ok": False, "message": "Email service is not configured yet."}
    resend = _get_resend()
    if resend is None:
        return {"ok": False, "message": "Email service is not configured yet."}

    inquiry_type = str(message.get("inquiry_type") or "General Question")
    sender = _sender_email()
    to_email = _contact_support_email()
    try:
        resend.Emails.send(
            {
                "from": sender,
                "to": to_email,
                "subject": f"New SnapClass AI inquiry: {inquiry_type}",
                "html": f"""
                <div style="font-family:sans-serif;max-width:640px;margin:auto;">
                  <h2 style="color:#5B6CFF;">New SnapClass AI inquiry</h2>
                  <p><strong>Type:</strong> {inquiry_type}</p>
                  <p><strong>Name:</strong> {message.get("name", "")}</p>
                  <p><strong>Institute:</strong> {message.get("institute_name", "") or "-"}</p>
                  <p><strong>Email:</strong> {message.get("email", "")}</p>
                  <p><strong>Phone/WhatsApp:</strong> {message.get("phone", "") or "-"}</p>
                  <p><strong>Student count:</strong> {message.get("student_count", "") or "-"}</p>
                  <p><strong>Subject:</strong> {message.get("subject", "")}</p>
                  <div style="background:#F5F7FF;border-radius:12px;padding:14px;margin-top:12px;">
                    {message.get("message", "")}
                  </div>
                </div>
                """,
            }
        )
        return {"ok": True, "message": "Founder notification sent."}
    except Exception as exc:
        return {"ok": False, "message": _friendly_email_error(exc)}


def send_contact_autoreply(message: dict[str, Any]) -> dict[str, Any]:
    """Send a polite auto-reply to the visitor."""
    if not _resend_ready():
        return {"ok": False, "message": "Email service is not configured yet."}
    resend = _get_resend()
    if resend is None:
        return {"ok": False, "message": "Email service is not configured yet."}

    recipient = str(message.get("email") or "").strip()
    if not recipient:
        return {"ok": False, "message": "Recipient email missing."}

    sender = _sender_email()
    try:
        resend.Emails.send(
            {
                "from": sender,
                "to": recipient,
                "subject": "We received your SnapClass AI message",
                "html": f"""
                <div style="font-family:sans-serif;max-width:600px;margin:auto;">
                  <h2 style="color:#5B6CFF;">Thanks for contacting SnapClass AI</h2>
                  <p>Hi <strong>{message.get("name", "there")}</strong>,</p>
                  <p>We received your message and will reply within 24 hours.</p>
                  <p style="color:#6B7280;font-size:12px;">SnapClass AI Team</p>
                </div>
                """,
            }
        )
        return {"ok": True, "message": "Auto-reply sent."}
    except Exception as exc:
        return {"ok": False, "message": _friendly_email_error(exc)}


def send_test_email(recipient_email: str, sender_user_id: str | None = None) -> dict[str, Any]:
    """Send a founder test email and persist an email_logs row."""
    secrets = read_app_secrets()
    api_key = str(secrets.get("RESEND_API_KEY", "") or "").strip()
    if not api_key or api_key == "re_your_key_here":
        return {"ok": False, "message": "Email service is not configured yet."}

    resend = _get_resend()
    if resend is None:
        return {"ok": False, "message": "Email service is not configured yet."}

    sender = _sender_email()
    subject = "SnapClass AI test email"
    log_id = None
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
        response = resend.Emails.send(
            {
                "from": sender,
                "to": recipient_email,
                "subject": subject,
                "html": "<p>SnapClass AI email delivery is configured.</p>",
            }
        )
        resend_email_id = response.get("id") if isinstance(response, dict) else None
        if db is not None and log_id:
            db.table("email_logs").update(
                {
                    "status": "sent",
                    "resend_email_id": resend_email_id,
                    "sent_at": __import__("datetime").datetime.utcnow().isoformat(),
                }
            ).eq("id", log_id).execute()
        return {"ok": True, "message": "Test email sent."}
    except Exception as exc:
        safe_message = _friendly_email_error(exc)
        if db is not None and log_id:
            try:
                db.table("email_logs").update(
                    {"status": "failed", "error_message": safe_message}
                ).eq("id", log_id).execute()
            except Exception:
                pass
        return {"ok": False, "message": safe_message}
