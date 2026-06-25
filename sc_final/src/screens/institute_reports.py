"""Institute Admin reports from live Supabase data."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.services.admin_context import get_current_institute_id
from src.services.institute_service import _db, init_institute_state


def _rows_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in rows if row.get("id")}


def _safe_rows(table: str, institute_id: str) -> list[dict[str, Any]]:
    db = _db()
    if not db or not institute_id:
        return []
    try:
        return db.table(table).select("*").eq("institute_id", institute_id).execute().data or []
    except Exception:
        return []


def show_reports() -> None:
    init_institute_state()
    st.markdown("### Reports")

    from datetime import date, timedelta

    institute_id = get_current_institute_id()

    if not institute_id:
        st.warning("Please log in again with your institute admin account.")
        return

    db = _db()
    if not db:
        st.info("Reports need Supabase live data.")
        return

    PERIOD_OPTIONS = [
        "All Time",
        "Today",
        "This Week",
        "This Month",
        "Last Month",
        "Custom",
    ]
    selected_period = st.selectbox(
        "Select Period",
        PERIOD_OPTIONS,
        index=0,
        key="report_period_filter",
    )

    custom_start = custom_end = None
    if selected_period == "Custom":
        c1, c2 = st.columns(2)
        custom_start = c1.date_input("From", value=date.today() - timedelta(days=30), key="report_custom_from")
        custom_end = c2.date_input("To", value=date.today(), key="report_custom_to")

    teachers = _safe_rows("teachers", institute_id)
    students = _safe_rows("students", institute_id)
    classes = _safe_rows("classes", institute_id)
    subjects = _safe_rows("subjects", institute_id)
    sessions = _safe_rows("attendance_sessions", institute_id)
    session_ids = [row.get("id") for row in sessions if row.get("id")]

    records: list[dict[str, Any]] = []

    if session_ids:
        try:
            records = (
                db.table("attendance_records")
                .select("*")
                .in_("session_id", session_ids)
                .execute()
                .data
                or []
            )
        except Exception as e:
            records = []

    # Apply period filter
    today = date.today()
    if selected_period != "All Time":
        filtered_records = []
        for record in records:
            raw_date = str(record.get("attendance_date") or "")[:10]
            try:
                d = date.fromisoformat(raw_date) if raw_date else None
            except ValueError:
                d = None
            if d is None:
                continue
            if selected_period == "Today":
                if d == today:
                    filtered_records.append(record)
            elif selected_period == "This Week":
                week_start = today - timedelta(days=today.weekday())
                if week_start <= d <= today:
                    filtered_records.append(record)
            elif selected_period == "This Month":
                if d.month == today.month and d.year == today.year:
                    filtered_records.append(record)
            elif selected_period == "Last Month":
                if d.month == (today.month - 1) or (d.month == 12 and today.month == 1):
                    if d.year == today.year or (d.month == 12 and today.month == 1 and d.year == today.year - 1):
                        filtered_records.append(record)
            elif selected_period == "Custom" and custom_start and custom_end:
                if custom_start <= d <= (custom_end + timedelta(days=1)):
                    filtered_records.append(record)
        records = filtered_records


    present = sum(1 for row in records if str(row.get("status") or "").lower() in {"present", "late"})
    absent = sum(1 for row in records if str(row.get("status") or "").lower() == "absent")
    total = len(records)
    pct = round((present / total) * 100, 1) if total else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Students", len(students))
    c2.metric("Teachers", len(teachers))
    c3.metric("Classes", len(classes))
    c4.metric("Subjects", len(subjects))
    c5.metric("Attendance %", f"{pct}%")

    if not records:
        st.info("No attendance records yet. Reports will appear after attendance is marked.")
        return

    students_by_id = _rows_by_id(students)
    classes_by_id = _rows_by_id(classes)
    subjects_by_id = _rows_by_id(subjects)
    sessions_by_id = _rows_by_id(sessions)

    rows = []
    for record in records:
        session = sessions_by_id.get(str(record.get("session_id") or ""), {})
        student = students_by_id.get(str(record.get("student_id") or ""), {})
        class_row = classes_by_id.get(str(record.get("class_id") or session.get("class_id") or ""), {})
        subject = subjects_by_id.get(str(record.get("subject_id") or session.get("subject_id") or ""), {})
        rows.append(
            {
                "Date": str(record.get("attendance_date") or session.get("attendance_date") or session.get("date") or "")[:10],
                "Student": student.get("name") or record.get("student_id") or "-",
                "Roll No": student.get("roll_no") or "-",
                "Class": f"{class_row.get('class_name') or class_row.get('name') or ''}-{class_row.get('section') or ''}".strip("-"),
                "Subject": subject.get("subject_name") or subject.get("name") or record.get("subject_id") or "-",
                "Status": str(record.get("status") or "").title(),
                "Verification": record.get("attendance_verification") or record.get("verification_method") or "manual",
            }
        )

    df = pd.DataFrame(rows).sort_values("Date", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Report",
        df.to_csv(index=False).encode("utf-8"),
        "admin_attendance_report.csv",
        "text/csv",
        use_container_width=True,
    )
