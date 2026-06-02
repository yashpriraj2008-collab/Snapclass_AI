from __future__ import annotations

from typing import Any

import streamlit as st


def get_low_attendance_students(institute_id: str, threshold: float = 75) -> list[dict[str, Any]]:
    """Return students below threshold for an institute.

    Expected student-like dict keys (best-effort):
    - id
    - name
    - email
    - roll_no
    - attendance (number)
    - institute_id
    - class_name/subject_name (optional)
    """
    try:
        from src.database.client import get_supabase_client

        supabase = get_supabase_client()
    except Exception:
        return []

    if not supabase:
        return []

    # Best-effort query: prefer attendance summary table if present.
    # If schema differs, this should fail gracefully.
    try:
        resp = (
            supabase.table("students")
            .select("id,name,email,roll_no,institute_id,attendance")
            .eq("institute_id", institute_id)
            .lt("attendance", threshold)
            .eq("status", "active")
            .execute()
        )
        return resp.data or []
    except Exception:
        pass

    # Fallback: some versions store attendance in a separate table.
    try:
        resp = (
            supabase.table("attendance")
            .select("student_id,students(id,name,email,roll_no,institute_id),avg(attendance) as attendance")
            .eq("students.institute_id", institute_id)
            .group("student_id, students(id,name,email,roll_no,institute_id)")
            .lt("attendance", threshold)
            .execute()
        )
        rows = resp.data or []
        out: list[dict[str, Any]] = []
        for r in rows:
            s = r.get("students") or {}
            out.append(
                {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "email": s.get("email"),
                    "roll_no": s.get("roll_no"),
                    "institute_id": s.get("institute_id"),
                    "attendance": r.get("attendance"),
                }
            )
        return out
    except Exception:
        return []


def build_low_attendance_email(
    student_name: str,
    subject: str,
    attendance_pct: float,
) -> dict[str, str]:
    subject_line = "⚠️ Low Attendance Alert"
    if subject:
        subject_line += f" — {subject}"

    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;">
      <h2 style="color:#5B6CFF;">SnapClass AI</h2>
      <p>Dear <strong>{student_name}</strong>,</p>
      <p>Your attendance in <strong>{subject}</strong> has dropped to
         <strong style=\"color:#EF4444;\">{attendance_pct}%</strong>.</p>
      <p>The minimum required attendance is <strong>75%</strong>.</p>
      <p>Please attend classes regularly to avoid academic issues.</p>
      <br>
      <p style="color:#6B7280;font-size:12px;">This is an automated message from SnapClass AI.</p>
    </div>
    """

    return {"subject": subject_line, "html": html}


def send_low_attendance_alerts(
    institute_id: str,
    sender_user_id: str | None = None,
    threshold: float = 75,
) -> dict[str, Any]:
    """Fetch low-attendance students and send alert emails.

    Returns a summary dict.
    """
    try:
        from src.services.email_service import send_email
    except Exception:
        return {"ok": False, "error": "email_service unavailable"}

    students = get_low_attendance_students(institute_id, threshold=threshold)
    sent = 0
    failed = 0
    errors: list[str] = []

    for s in students:
        email = (s.get("email") or "").strip()
        if not email:
            failed += 1
            continue

        name = s.get("name") or "Student"
        attendance_pct = s.get("attendance") or 0
        subject = s.get("subject_name") or "your class"

        payload = build_low_attendance_email(
            student_name=str(name),
            subject=str(subject),
            attendance_pct=float(attendance_pct),
        )

        result = send_email(
            to_email=email,
            subject=payload["subject"],
            html=payload["html"],
            metadata={"institute_id": institute_id, "student_id": s.get("id")},
            template_key="low_attendance_alert",
            recipient_type="student",
            sender_user_id=sender_user_id,
        )

        if result.get("success"):
            sent += 1
        else:
            failed += 1
            err = result.get("error") or "Unknown error"
            errors.append(f"{email}: {err}")

    return {"ok": failed == 0, "sent": sent, "failed": failed, "errors": errors}

