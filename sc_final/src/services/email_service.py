import streamlit as st
from typing import Any


def _get_resend():
    try:
        import resend  # type: ignore

        # API key can be blank in local/dev; caller handles failures.
        resend.api_key = st.secrets.get("RESEND_API_KEY", "")
        return resend
    except ImportError:
        return None


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
        return {"ok": False, "message": "Email service not configured."}

    sender = st.secrets.get("SENDER_EMAIL", "noreply@snapclass.ai")

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
        return {"ok": False, "message": str(e)}


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
        return {"ok": False, "message": "Email service not configured."}


    sender = st.secrets.get("SENDER_EMAIL", "noreply@snapclass.ai")
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
        return {"ok": False, "message": str(e)}


def send_welcome_email(user_email: str, user_name: str, role: str) -> dict[str, Any]:
    resend = _get_resend()
    if resend is None:
        return {"ok": False, "message": "resend not installed"}

    sender = st.secrets.get("SENDER_EMAIL", "noreply@snapclass.ai")
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
                  <a href="https://your-app.streamlit.app"
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
        return {"ok": False, "message": str(e)}
