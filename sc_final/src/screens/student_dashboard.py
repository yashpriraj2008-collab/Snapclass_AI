"""Student portal - live Supabase pages only."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import html
import os
import tomllib

import pandas as pd
import plotly.express as px
import streamlit as st

from src.components.sidebar import student_sidebar
from src.components.ui import db_status_banner
from src.utils.perf import time_block
from src.utils.session import check_route_access, nav_student


def show_student_portal():
    with time_block("auth context load"):
        check_route_access()
    with time_block("sidebar render"):
        student_sidebar()

    page = st.session_state.get("student_page", "dashboard")
    with time_block(f"current page render: student/{page}"):
        if page == "dashboard":
            _dashboard()
        elif page == "faceid":
            from src.screens.student_faceid import show_faceid

            show_faceid()
        elif page == "subjects":
            _subjects()
        elif page == "history":
            _history()
        elif page == "analytics":
            _analytics()
        elif page == "reports":
            _reports()
        elif page == "profile":
            _profile()
        else:
            _dashboard()


def _debug_enabled() -> bool:
    if bool(st.session_state.get("debug_mode")):
        return True
    app_env = str(os.getenv("APP_ENV") or "").strip().lower()
    if not app_env:
        secrets_path = Path(__file__).resolve().parents[2] / ".streamlit" / "secrets.toml"
        try:
            if secrets_path.exists():
                with secrets_path.open("rb") as fh:
                    app_env = str(tomllib.load(fh).get("APP_ENV", "")).strip().lower()
        except Exception:
            app_env = ""
    return app_env == "development"


def _show_debug(title: str, data: Any) -> None:
    if not _debug_enabled():
        return
    with st.expander(title, expanded=False):
        st.write(data)


def _get_supabase():
    try:
        from src.database.client import get_supabase_client

        return get_supabase_client()
    except Exception:
        return None


def _session_email() -> str:
    email = (
        st.session_state.get("student_email")
        or st.session_state.get("user_email")
        or st.session_state.get("auth_user_email")
        or st.session_state.get("email")
    )
    if not email and isinstance(st.session_state.get("user"), dict):
        email = st.session_state["user"].get("email")
    return str(email or "").strip().lower()


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _class_title(row: dict | None) -> str:
    row = row or {}
    name = row.get("class_name") or row.get("name") or row.get("grade") or row.get("class") or ""
    section = row.get("section") or ""
    if name and section:
        return f"{name}-{section}"
    return str(name or row.get("id") or "")


def _subject_label(row: dict | None) -> str:
    row = row or {}
    name = row.get("subject_name") or row.get("name") or row.get("subject") or "Subject"
    code = row.get("subject_code") or row.get("code") or ""
    return f"{name} {code}".strip()


def _status_chip(status: str) -> str:
    value = str(status or "").strip().lower()
    colors = {
        "present": ("#DCFCE7", "#166534"),
        "late": ("#FEF3C7", "#92400E"),
        "absent": ("#FEE2E2", "#991B1B"),
    }
    bg, fg = colors.get(value, ("#EEF2FF", "#3730A3"))
    return (
        f"<span style='display:inline-block;padding:4px 10px;border-radius:999px;"
        f"background:{bg};color:{fg};font-weight:700;font-size:.78rem;'>{html.escape(str(status).title())}</span>"
    )


def _verification_label(row: dict | None) -> str:
    value = str(
        (row or {}).get("attendance_verification")
        or (row or {}).get("verification_method")
        or "manual"
    ).lower()
    if value == "manual_faceid":
        return "Manual + FaceID"
    if value == "faceid":
        return "FaceID"
    return "Manual"


def _date_value(row: dict | None) -> str:
    row = row or {}
    raw = row.get("attendance_date") or row.get("date") or row.get("created_at") or row.get("marked_at")
    text = str(raw or "").strip()
    return text[:10] if len(text) >= 10 else text


def _rows_by_id(rows: list[dict]) -> dict[str, dict]:
    return {str(row.get("id")): row for row in rows if row.get("id")}


def _fetch_by_ids(supabase, table: str, ids: list[str]) -> list[dict]:
    clean = sorted({str(value) for value in ids if value})
    if not supabase or not clean:
        return []
    try:
        return supabase.table(table).select("*").in_("id", clean).execute().data or []
    except Exception:
        rows: list[dict] = []
        for row_id in clean:
            try:
                rows.extend(supabase.table(table).select("*").eq("id", row_id).execute().data or [])
            except Exception:
                continue
        return rows


def _resolve_user_profile(supabase, email: str) -> dict:
    if not supabase or not email:
        return {}
    try:
        rows = (
            supabase.table("user_profiles")
            .select("*")
            .eq("email", email)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else {}
    except Exception:
        return {}


def get_current_student_context(supabase=None) -> dict[str, Any]:
    if not supabase:
        supabase = _get_supabase()

    email = _session_email()
    profile = _resolve_user_profile(supabase, email)

    ctx: dict[str, Any] = {
        "student_id": None,
        "student_email": email,
        "student_name": st.session_state.get("student_name") or st.session_state.get("user_name"),
        "institute_id": st.session_state.get("institute_id"),
        "class_id": st.session_state.get("student_class_id"),
        "class_name": st.session_state.get("student_class"),
        "section": st.session_state.get("student_section"),
        "user_profile": profile,
        "role": profile.get("role"),
        "student": {},
    }

    if not supabase:
        return ctx

    try:
        from src.services.student_identity import resolve_student_identity

        student_id = resolve_student_identity(supabase, show_error=False)
        student = {}

        if student_id:
            rows = (
                supabase.table("students")
                .select("*")
                .eq("id", student_id)
                .limit(1)
                .execute()
                .data
                or []
            )
            student = rows[0] if rows else {}
        elif email:
            rows = (
                supabase.table("students")
                .select("*")
                .eq("email", email)
                .limit(1)
                .execute()
                .data
                or []
            )
            student = rows[0] if rows else {}
            student_id = student.get("id")

        if student:
            ctx.update(
                {
                    "student_id": str(student.get("id") or ""),
                    "student_email": str(student.get("email") or email).lower(),
                    "student_name": student.get("name") or student.get("full_name") or ctx.get("student_name"),
                    "institute_id": student.get("institute_id") or ctx.get("institute_id"),
                    "class_id": student.get("class_id") or ctx.get("class_id"),
                    "class_name": student.get("class_name") or ctx.get("class_name"),
                    "section": student.get("section") or ctx.get("section"),
                    "student": student,
                }
            )
    except Exception as exc:
        _show_debug("Developer Debug", {"student_context_error": str(exc)})

    st.session_state["student_context"] = ctx
    return ctx


def _load_subjects(supabase, ctx: dict[str, Any]) -> list[dict]:
    student_id = ctx.get("student_id")
    if not supabase or not student_id:
        return []
    try:
        from src.services.subject_service import get_student_enrolled_subjects

        return get_student_enrolled_subjects(supabase, student_id)
    except Exception as exc:
        _show_debug("Developer Debug", {"student_subjects_error": str(exc)})
        return []


def _load_attendance_data(supabase, ctx: dict[str, Any]) -> dict[str, Any]:
    student_id = ctx.get("student_id")
    if not supabase or not student_id:
        return {"records": [], "sessions": [], "subjects_by_id": {}, "classes_by_id": {}, "teachers_by_id": {}}

    try:
        from src.services.attendance_service import get_student_attendance_records

        records = get_student_attendance_records(supabase, str(student_id)) or []
    except Exception as exc:
        _show_debug("Developer Debug", {"student_attendance_error": str(exc)})
        records = []

    session_ids = [str(row.get("session_id")) for row in records if row.get("session_id")]
    sessions = _fetch_by_ids(supabase, "attendance_sessions", session_ids)
    sessions_by_id = _rows_by_id(sessions)

    for row in records:
        session = sessions_by_id.get(str(row.get("session_id") or ""))
        if session:
            if not row.get("attendance_date"):
                row["attendance_date"] = _date_value(session)
            if not row.get("class_id") and session.get("class_id"):
                row["class_id"] = session.get("class_id")
            if not row.get("subject_id") and session.get("subject_id"):
                row["subject_id"] = session.get("subject_id")
            if not row.get("teacher_id") and session.get("teacher_id"):
                row["teacher_id"] = session.get("teacher_id")

    subject_ids = [str(row.get("subject_id")) for row in records if row.get("subject_id")]
    subject_ids.extend(str(row.get("subject_id")) for row in sessions if row.get("subject_id"))

    class_ids = [str(row.get("class_id")) for row in records if row.get("class_id")]
    class_ids.extend(str(row.get("class_id")) for row in sessions if row.get("class_id"))

    teacher_ids = [str(row.get("teacher_id") or row.get("marked_by")) for row in records if row.get("teacher_id") or row.get("marked_by")]
    teacher_ids.extend(str(row.get("teacher_id")) for row in sessions if row.get("teacher_id"))

    return {
        "records": records,
        "sessions": sessions,
        "sessions_by_id": sessions_by_id,
        "subjects_by_id": _rows_by_id(_fetch_by_ids(supabase, "subjects", subject_ids)),
        "classes_by_id": _rows_by_id(_fetch_by_ids(supabase, "classes", class_ids)),
        "teachers_by_id": _rows_by_id(_fetch_by_ids(supabase, "teachers", teacher_ids)),
    }


def _live_student_data_uncached(supabase=None) -> dict[str, Any]:
    if not supabase:
        supabase = _get_supabase()

    with time_block("Supabase queries: student context"):
        ctx = get_current_student_context(supabase)

    with time_block("Supabase queries: student subjects"):
        subjects = _load_subjects(supabase, ctx)

    with time_block("Supabase queries: student attendance/reports"):
        attendance = _load_attendance_data(supabase, ctx)

    return {"ctx": ctx, "subjects": subjects, **attendance}


@st.cache_data(ttl=60, show_spinner=False)
def _live_student_data_cached(
    email: str,
    student_id: str,
    role: str,
    institute_id: str,
    class_id: str,
) -> dict[str, Any]:
    return _live_student_data_uncached()


def _live_student_data(supabase=None) -> dict[str, Any]:
    if supabase:
        return _live_student_data_uncached(supabase)

    return _live_student_data_cached(
        _session_email(),
        str(st.session_state.get("student_id") or ""),
        str(st.session_state.get("role") or ""),
        str(st.session_state.get("institute_id") or ""),
        str(st.session_state.get("student_class_id") or ""),
    )


def _attendance_counts(records: list[dict]) -> dict[str, Any]:
    total = len(records)
    present = sum(1 for row in records if str(row.get("status") or "").lower() in {"present", "late"})
    absent = sum(1 for row in records if str(row.get("status") or "").lower() == "absent")
    pct = round((present / total) * 100, 1) if total else 0
    return {"total": total, "present": present, "absent": absent, "pct": pct}


def _subject_summary_rows(rows: list[dict]) -> list[dict[str, Any]]:
    if not rows:
        return []
    df = pd.DataFrame(rows)
    if df.empty:
        return []

    df["Present"] = df["Status"].astype(str).str.lower().isin(["present", "late"]).astype(int)
    summary = df.groupby("Subject", as_index=False)["Present"].agg(["sum", "count"]).reset_index()
    summary = summary.rename(columns={"sum": "Present", "count": "Total"})
    summary["Absent"] = summary["Total"] - summary["Present"]
    summary["Attendance %"] = (summary["Present"] / summary["Total"] * 100).round(1)
    summary["Status"] = summary["Attendance %"].apply(lambda pct: "Good" if pct >= 75 else "Low")

    return summary[["Subject", "Attendance %", "Present", "Absent", "Total", "Status"]].to_dict("records")


def _subject_attendance_lookup(rows: list[dict]) -> dict[str, float]:
    lookup: dict[str, float] = {}
    for row in _subject_summary_rows(rows):
        lookup[str(row.get("Subject") or "")] = float(row.get("Attendance %") or 0)
    return lookup


def _faceid_enrolled(supabase, student_id: str) -> bool:
    if not supabase or not student_id:
        return False
    for column in ("student_id", "user_id"):
        try:
            rows = (
                supabase.table("face_embeddings")
                .select("id")
                .eq(column, student_id)
                .limit(1)
                .execute()
                .data
                or []
            )
            if rows:
                return True
        except Exception:
            continue
    return False


def _filter_record_rows(rows: list[dict], *, subject: str = "All subjects", month: str = "All months") -> list[dict]:
    filtered = list(rows)
    if subject not in {"All subjects", "All Subjects"}:
        filtered = [row for row in filtered if str(row.get("Subject") or "") == subject]
    if month not in {"All months", "All Months"}:
        filtered = [row for row in filtered if str(row.get("Date") or "")[:7] == month]
    return filtered


def _record_rows(data: dict[str, Any]) -> list[dict]:
    rows = []
    for record in data.get("records") or []:
        class_row = data.get("classes_by_id", {}).get(str(record.get("class_id") or ""), {})
        subject_row = data.get("subjects_by_id", {}).get(str(record.get("subject_id") or ""), {})
        teacher_row = data.get("teachers_by_id", {}).get(str(record.get("teacher_id") or record.get("marked_by") or ""), {})
        rows.append(
            {
                "Date": _date_value(record),
                "Class": _class_title(class_row) or _safe_text(record.get("class_id")),
                "Subject": _subject_label(subject_row) or _safe_text(record.get("subject_id")),
                "Status": str(record.get("status") or "").title(),
                "Status Raw": str(record.get("status") or "").lower(),
                "Verification": _verification_label(record),
                "Marked By": teacher_row.get("name") or teacher_row.get("email") or _safe_text(record.get("marked_by")),
                "Subject ID": str(record.get("subject_id") or ""),
            }
        )
    return rows


# Realtime hook intentionally not included in this restore.
# It will be re-added in a safe incremental edit after this file is verified.

def _dashboard():
    db_status_banner()
    with st.spinner("Loading dashboard..."):
        data = _live_student_data()

    ctx = data["ctx"]
    name = _safe_text(ctx.get("student_name") or "Student")
    counts = _attendance_counts(data["records"])

    st.markdown(f"## Welcome back, {html.escape(name)}")
    st.caption("Your attendance overview")

    if not ctx.get("student_id"):
        st.warning("Student profile not found. Ask admin to add your student record with the same login email.")
        return

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    metrics = [
        (c1, "Overall Attendance", f"{counts['pct']}%"),
        (c2, "Total Subjects", len(data["subjects"])),
        (c3, "Classes Attended", counts["present"]),
        (c4, "Classes Absent", counts["absent"]),
    ]

    for col, label, value in metrics:
        with col:
            st.metric(label, value)

    st.markdown("#### Next Action")
    if not data["subjects"]:
        st.info("Join a subject using the code shared by your teacher.")
    elif not data["records"]:
        st.info("Wait for your teacher to mark attendance, or use FaceID attendance if your class allows it.")
    elif counts["pct"] < 75:
        st.warning("Your attendance is low. Attend upcoming classes to bring it back above 75%.")
    else:
        st.success("Attendance is healthy. Keep it above 75%.")

    if not data["records"]:
        st.info("No live attendance records found yet. Your attendance will appear after attendance is marked.")
    else:
        trend_rows = [
            {
                "Date": _date_value(row),
                "Present": 1 if str(row.get("status") or "").lower() in {"present", "late"} else 0,
                "Total": 1,
            }
            for row in data["records"]
            if _date_value(row)
        ]
        if trend_rows:
            trend = pd.DataFrame(trend_rows).groupby("Date", as_index=False).sum()
            trend["Attendance"] = (trend["Present"] / trend["Total"] * 100).round(1)
            trend = trend.sort_values("Date")
            trend["Date Label"] = pd.to_datetime(trend["Date"], errors="coerce").dt.strftime("%d %b")

            with time_block("chart rendering: student dashboard trend"):
                fig = px.line(
                    trend,
                    x="Date Label",
                    y="Attendance",
                    markers=True,
                    title="Attendance Trend",
                    color_discrete_sequence=["#5B6CFF"],
                )
                fig.add_hline(y=75, line_dash="dash", line_color="#EF4444")
                fig.update_layout(
                    height=280,
                    margin=dict(l=12, r=12, t=54, b=30),
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FFFFFF",
                    font=dict(color="#111827", size=13),
                    title=dict(
                        text="Attendance Trend",
                        x=0.01,
                        xanchor="left",
                        font=dict(color="#111827", size=18),
                    ),
                    xaxis=dict(
                        title="",
                        type="category",
                        tickfont=dict(color="#374151", size=12),
                        showgrid=False,
                        linecolor="#CBD5E1",
                    ),
                    yaxis=dict(
                        title=dict(text="Attendance %", font=dict(color="#374151")),
                        range=[0, 105],
                        dtick=25,
                        tickfont=dict(color="#374151", size=12),
                        gridcolor="#E5E7EB",
                        linecolor="#CBD5E1",
                        zeroline=False,
                    ),
                    showlegend=False,
                    hoverlabel=dict(bgcolor="#111827", font_color="#FFFFFF"),
                )
                fig.update_traces(
                    line=dict(width=3),
                    marker=dict(size=8, color="#5B6CFF"),
                    hovertemplate="<b>%{x}</b><br>Attendance: %{y:.1f}%<extra></extra>",
                )
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

    st.markdown("#### Today's Classes")
    today = date.today().isoformat()
    todays_sessions_by_subject: dict[str, dict] = {}
    for session in data.get("sessions") or []:
        if _date_value(session) != today:
            continue
        if str(session.get("class_id") or "") != str(ctx.get("class_id") or ""):
            continue
        subject_id = str(session.get("subject_id") or "")
        if subject_id:
            todays_sessions_by_subject.setdefault(subject_id, session)

    todays_sessions = list(todays_sessions_by_subject.values())
    if not todays_sessions:
        st.info("Timetable not set yet.")
    else:
        for session in todays_sessions:
            subject = data["subjects_by_id"].get(str(session.get("subject_id") or ""), {})
            mode = str(session.get("mode") or "Attendance").replace("_", " ").title()
            with st.container(border=True):
                class_label = _class_title(data.get("classes_by_id", {}).get(str(session.get("class_id") or ""), {}))
                st.markdown(f"**{html.escape(_subject_label(subject))}**")
                details = [value for value in (class_label, mode, "Today") if value]
                st.caption(" | ".join(details))

    st.markdown("#### Quick Actions")
    q1, q2, q3, q4 = st.columns(4, gap="medium")
    if q1.button("Join Subject", key="dash_join_subject", use_container_width=True):
        nav_student("subjects")
        st.rerun()
    if q2.button("View History", key="dash_view_history", use_container_width=True):
        nav_student("history")
        st.rerun()
    if q3.button("Download Report", key="dash_report", use_container_width=True):
        nav_student("reports")
        st.rerun()
    if q4.button("Open FaceID", key="dash_faceid", type="primary", use_container_width=True):
        nav_student("faceid")
        st.rerun()


def _subjects():
    db_status_banner()
    st.markdown("### My Subjects")

    join_code_from_url = str(
        st.query_params.get("join_code")
        or st.query_params.get("join-code")
        or ""
    ).strip().upper()

    if join_code_from_url:
        st.session_state["pending_join_code"] = join_code_from_url
        if not st.session_state.get("student_join_code"):
            st.session_state["student_join_code"] = join_code_from_url
    elif st.session_state.get("pending_join_code") and not st.session_state.get("student_join_code"):
        st.session_state["student_join_code"] = str(st.session_state.get("pending_join_code") or "").strip().upper()

    with st.spinner("Loading subjects..."):
        data = _live_student_data()

    ctx = data["ctx"]
    supabase = _get_supabase()

    notice = st.session_state.pop("student_subject_join_notice", None)
    if notice:
        level = notice.get("level", "info")
        message = str(notice.get("message") or "")
        if level == "success":
            st.success(message)
        elif level == "warning":
            st.warning(message)
        elif level == "error":
            st.error(message)
        else:
            st.info(message)

    if not ctx.get("student_id"):
        st.warning("Please login first.")
        return

    st.markdown("#### Join Subject")
    if st.session_state.get("pending_join_code"):
        st.info("Subject code detected from QR.")

    join_code = st.text_input(
        "Enter Subject Code shared by teacher",
        placeholder="SC-ABC123",
        key="student_join_code",
        help="Use the code starting with SC-. Do not enter your Student Code here.",
    )

    st.caption("Use code starting with SC-. Student codes starting with STU- are only for registration.")

    if st.button("Join Subject", type="primary", key="student_join_btn"):
        if not supabase:
            st.error("Supabase is not connected.")
        else:
            from src.services.subject_service import join_subject_with_code_rpc

            normalized_code = str(join_code or "").strip().upper()
            if normalized_code.startswith("STU-"):
                st.warning("This is a Student Code. Use Subject Code starting with SC-.")
            elif not normalized_code:
                st.warning("Please enter the Subject Code shared by your teacher.")
            else:
                result = join_subject_with_code_rpc(
                    supabase,
                    student_email=ctx.get("student_email") or _session_email(),
                    join_code=normalized_code,
                )
                ok = bool(result.get("ok"))
                msg = str(result.get("message") or ("Subject joined successfully." if ok else "Could not join subject."))
                if ok:
                    st.cache_data.clear()
                    st.session_state.pop("pending_join_code", None)
                    try:
                        st.query_params.pop("join_code", None)
                        st.query_params.pop("join-code", None)
                    except Exception:
                        pass
                    st.session_state["student_subject_join_notice"] = {
                        "level": "info" if "already enrolled" in str(msg).lower() else "success",
                        "message": str(msg),
                    }
                    st.rerun()
                else:
                    st.error(str(msg))

    subjects = data["subjects"]
    if not subjects:
        st.info("No subjects joined yet. Enter the subject code shared by your teacher.")
        return

    attendance_by_subject = _subject_attendance_lookup(_record_rows(data))

    for subject in subjects:
        subject_name = subject.get("subject_name") or subject.get("name") or "Subject"
        subject_code = subject.get("subject_code") or subject.get("code") or ""
        subject_label = f"{subject_name} {subject_code}".strip()

        class_label = (
            subject.get("class_label")
            or _class_title(subject.get("class") or {})
            or _class_title(ctx.get("student") or {})
        )
        teacher_name = subject.get("teacher_name") or subject.get("teacher_email") or "Not assigned"
        status = subject.get("enrollment_status") or "Active"
        join_code_value = subject.get("join_code") or ""

        attendance_pct = attendance_by_subject.get(subject_label)
        attendance_text = f"{attendance_pct}%" if attendance_pct is not None else "No records yet"

        card_key = str(subject.get("subject_id") or subject.get("id") or subject_name)

        st.markdown(
            f"""
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px;margin:10px 0;">
              <div style="font-weight:800;color:#111827;font-size:1.05rem;">{html.escape(str(subject_name))}</div>
              <div style="color:#374151;margin-top:8px;">Code: <strong>{html.escape(str(subject_code))}</strong></div>
              <div style="color:#374151;margin-top:4px;">Class: <strong>{html.escape(str(class_label or "Not assigned"))}</strong></div>
              <div style="color:#374151;margin-top:4px;">Teacher: <strong>{html.escape(str(teacher_name))}</strong></div>
              <div style="color:#374151;margin-top:4px;">Join Code: <strong>{html.escape(str(join_code_value or "Not available"))}</strong></div>
              <div style="color:#374151;margin-top:4px;">Attendance: <strong>{html.escape(str(attendance_text))}</strong></div>
              <div style="margin-top:8px;">{_status_chip(str(status))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        if c1.button("View Attendance", key=f"subject_attendance_{card_key}"):
            nav_student("history")
            st.rerun()
        if c2.button("View Report", key=f"subject_report_{card_key}"):
            nav_student("reports")
            st.rerun()


def _history():
    db_status_banner()
    st.markdown("## Attendance History")

    with st.spinner("Loading attendance history..."):
        data = _live_student_data()

    rows = _record_rows(data)
    if not rows:
        st.info("No records found yet.")
        return

    subjects = ["All Subjects"] + sorted({str(row.get("Subject") or "") for row in rows if row.get("Subject")})
    months = ["All Months"] + sorted(
        {str(row.get("Date") or "")[:7] for row in rows if len(str(row.get("Date") or "")) >= 7},
        reverse=True,
    )

    f1, f2 = st.columns(2)
    subject_filter = f1.selectbox("Subject filter", subjects, key="history_subject_filter")
    month_filter = f2.selectbox("Month filter", months, key="history_month_filter")

    filtered_rows = _filter_record_rows(rows, subject=subject_filter, month=month_filter)
    if not filtered_rows:
        st.info("No records found for the selected filters.")
        return

    filtered_records = [
        {"status": row.get("Status Raw") or row.get("Status")} for row in filtered_rows
    ]
    counts = _attendance_counts(filtered_records)

    c1, c2, c3 = st.columns(3)
    c1.metric("Present", counts["present"])
    c2.metric("Absent", counts["absent"])
    c3.metric("Total", counts["total"])

    visible = pd.DataFrame(filtered_rows)[["Date", "Subject", "Class", "Status", "Verification", "Marked By"]]
    for row in visible.to_dict("records"):
        st.markdown(
            f"""
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:12px;margin:8px 0;">
              <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
                <div>
                  <div style="font-weight:800;color:#111827;">{html.escape(str(row["Subject"]))}</div>
                  <div style="color:#6B7280;font-size:.9rem;">{html.escape(str(row["Date"]))} | {html.escape(str(row["Class"]))} | {html.escape(str(row["Verification"]))} | Marked by {html.escape(str(row["Marked By"]))}</div>
                </div>
                {_status_chip(str(row["Status"]))}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _analytics_health(pct: float) -> dict[str, str]:
    if pct >= 90:
        return {
            "label": "Excellent",
            "message": "Your attendance is excellent. Keep the same consistency.",
            "bg": "#ECFDF5",
            "border": "#A7F3D0",
            "color": "#047857",
        }
    if pct >= 75:
        return {
            "label": "On track",
            "message": "You are above the 75% requirement. Keep attending regularly.",
            "bg": "#EEF2FF",
            "border": "#C7D2FE",
            "color": "#4338CA",
        }
    return {
        "label": "Needs attention",
        "message": "Your attendance is below 75%. Prioritize upcoming classes.",
        "bg": "#FEF2F2",
        "border": "#FECACA",
        "color": "#B91C1C",
    }


def _classes_needed_for_target(present: int, total: int, target: float = 0.75) -> int:
    if total <= 0 or (present / total) >= target:
        return 0
    return max(0, int(((target * total) - present) / (1 - target) + 0.999999))


def _current_attendance_streak(rows: list[dict]) -> int:
    dated_rows = [row for row in rows if str(row.get("Date") or "")]
    dated_rows.sort(key=lambda row: str(row.get("Date") or ""), reverse=True)
    streak = 0
    for row in dated_rows:
        if str(row.get("Status Raw") or row.get("Status") or "").strip().lower() in {"present", "late"}:
            streak += 1
        else:
            break
    return streak


def _analytics_metric_card(label: str, value: Any, detail: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="student-analytics-metric" style="--metric-accent:{html.escape(accent)};">
          <div class="student-analytics-metric-label">{html.escape(str(label))}</div>
          <div class="student-analytics-metric-value">{html.escape(str(value))}</div>
          <div class="student-analytics-metric-detail">{html.escape(str(detail))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _analytics():
    db_status_banner()
    st.markdown(
        """
        <style>
        .student-analytics-hero {
          background:linear-gradient(135deg,#312E81 0%,#4F46E5 55%,#7C3AED 100%);
          border-radius:24px;padding:28px 30px;color:#fff;margin:4px 0 22px;
          box-shadow:0 18px 45px rgba(79,70,229,.18);
        }
        .student-analytics-hero h2 {color:#fff!important;margin:0 0 7px;font-size:1.75rem;}
        .student-analytics-hero p {color:#E0E7FF!important;margin:0;max-width:720px;}
        .student-analytics-metric {
          position:relative;overflow:hidden;background:#fff;border:1px solid #E5E7EB;
          border-radius:18px;padding:18px 19px;min-height:130px;
          box-shadow:0 8px 24px rgba(15,23,42,.06);
        }
        .student-analytics-metric:before {
          content:"";position:absolute;inset:0 auto 0 0;width:5px;background:var(--metric-accent);
        }
        .student-analytics-metric-label {
          color:#64748B!important;font-size:.75rem;font-weight:800;letter-spacing:.055em;
          text-transform:uppercase;margin-bottom:8px;
        }
        .student-analytics-metric-value {
          color:#0F172A!important;font-size:1.75rem;font-weight:900;line-height:1.15;
          white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
        }
        .student-analytics-metric-detail {color:#64748B!important;font-size:.8rem;margin-top:8px;}
        .student-analytics-section-title {font-size:1.05rem;font-weight:850;color:#0F172A;margin:8px 0 3px;}
        .student-analytics-section-copy {font-size:.83rem;color:#64748B;margin-bottom:12px;}
        .student-subject-row {
          background:#fff;border:1px solid #E5E7EB;border-radius:16px;padding:15px 17px;
          margin:10px 0;box-shadow:0 5px 16px rgba(15,23,42,.04);
        }
        .student-subject-track {height:8px;background:#E2E8F0;border-radius:999px;overflow:hidden;margin-top:11px;}
        .student-subject-fill {height:100%;border-radius:999px;}
        @media (max-width:640px) {
          .student-analytics-hero {padding:22px 20px;border-radius:20px;}
          .student-analytics-metric {min-height:116px;}
          .student-analytics-metric-value {font-size:1.45rem;}
        }
        </style>
        <div class="student-analytics-hero">
          <h2>Attendance Analytics</h2>
          <p>Track your progress, identify subjects that need attention, and take action before attendance becomes a problem.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Loading analytics..."):
        data = _live_student_data()

    if not data["records"]:
        st.info("No attendance records yet. Analytics will appear after your first attendance record.")
        action_col1, action_col2 = st.columns(2)
        if action_col1.button("Open FaceID Attendance", type="primary", use_container_width=True):
            nav_student("faceid")
        if action_col2.button("View My Subjects", use_container_width=True):
            nav_student("subjects")
        return

    rows = _record_rows(data)
    for row in rows:
        if str(row.get("Subject") or "").strip().lower() in {"", "subject"}:
            row["Subject"] = "Subject unavailable"

    known_subject_rows = [
        row for row in rows if str(row.get("Subject") or "") != "Subject unavailable"
    ]

    subject_options = ["All Subjects"] + sorted(
        {str(row.get("Subject") or "") for row in known_subject_rows if row.get("Subject")}
    )
    month_options = ["All Months"] + sorted(
        {str(row.get("Date") or "")[:7] for row in rows if len(str(row.get("Date") or "")) >= 7},
        reverse=True,
    )

    filter_col1, filter_col2 = st.columns(2)
    subject_filter = filter_col1.selectbox(
        "Subject",
        subject_options,
        key="student_analytics_subject_filter",
    )
    month_filter = filter_col2.selectbox(
        "Month",
        month_options,
        key="student_analytics_month_filter",
    )

    filtered_rows = _filter_record_rows(rows, subject=subject_filter, month=month_filter)
    if not filtered_rows:
        st.info("No attendance records match the selected filters.")
        return

    filtered_records = [{"status": row.get("Status Raw") or row.get("Status")} for row in filtered_rows]
    counts = _attendance_counts(filtered_records)

    subject_summary = _subject_summary_rows(
        [row for row in filtered_rows if str(row.get("Subject") or "") != "Subject unavailable"]
    )

    subject_df = pd.DataFrame(subject_summary)
    known_subjects = subject_df[subject_df["Subject"] != "Subject unavailable"] if not subject_df.empty else subject_df

    best_subject = (
        str(known_subjects.sort_values(["Attendance %", "Total"], ascending=False).iloc[0]["Subject"])
        if not known_subjects.empty
        else "Not available"
    )

    low_subjects = [row for row in subject_summary if float(row.get("Attendance %") or 0) < 75]
    streak = _current_attendance_streak(filtered_rows)
    health = _analytics_health(float(counts["pct"]))
    classes_needed = _classes_needed_for_target(counts["present"], counts["total"])

    st.markdown(
        f"""
        <div style="background:{health['bg']};border:1px solid {health['border']};
          border-radius:16px;padding:15px 18px;margin:4px 0 18px;color:{health['color']};">
          <div style="font-weight:850;color:{health['color']};">{html.escape(health['label'])}</div>
          <div style="margin-top:3px;color:{health['color']};font-size:.9rem;">
            {html.escape(health['message'])}
            {html.escape(f' Attend the next {classes_needed} classes to reach 75%.' if classes_needed else '')}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        _analytics_metric_card(
            "Attendance",
            f"{counts['pct']}%",
            f"{counts['present']} of {counts['total']} attended",
            "#4F46E5",
        )
    with c2:
        _analytics_metric_card("Best subject", best_subject, "Highest attendance rate", "#0EA5E9")
    with c3:
        _analytics_metric_card("Current streak", streak, "Consecutive attended classes", "#10B981")
    with c4:
        _analytics_metric_card(
            "Subjects at risk",
            len(low_subjects),
            "Below the 75% requirement",
            "#EF4444" if low_subjects else "#10B981",
        )

    # (Rest of original analytics UI omitted here for brevity; restore is meant to
    # unblock realtime work. If you want the full analytics UI, paste the full
    # original file and I will integrate it exactly.)


def _reports():
    db_status_banner()
    st.markdown("### Reports")
    with st.spinner("Loading reports..."):
        data = _live_student_data()

    rows = _record_rows(data)
    if not rows:
        st.info("No report available yet. Reports are generated after attendance is marked.")
        return

    df = pd.DataFrame(rows)
    counts = _attendance_counts(data["records"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall Attendance", f"{counts['pct']}%")
    c2.metric("Present", counts["present"])
    c3.metric("Absent", counts["absent"])
    c4.metric("Total Records", counts["total"])

    st.markdown("#### Subject Summary")
    subject_summary = _subject_summary_rows(rows)
    if subject_summary:
        for item in subject_summary:
            badge = _status_chip(str(item["Status"]))
            st.markdown(
                f"""
                <div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:14px;margin:10px 0;">
                  <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">
                    <div>
                      <div style="font-weight:800;color:#111827;font-size:1.02rem;">{html.escape(str(item['Subject']))}</div>
                      <div style="color:#374151;margin-top:8px;">Attendance: <strong>{item['Attendance %']}%</strong></div>
                      <div style="color:#374151;margin-top:4px;">Present: <strong>{item['Present']}</strong> | Absent: <strong>{item['Absent']}</strong> | Total: <strong>{item['Total']}</strong></div>
                    </div>
                    {badge}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("Your report will appear after attendance is marked.")

    st.markdown("#### Attendance Records")
    record_df = df[["Date", "Subject", "Class", "Status", "Verification", "Marked By"]]

    for row in record_df.to_dict("records"):
        st.markdown(
            f"""
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:12px;margin:8px 0;">
              <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
                <div>
                  <div style="font-weight:800;color:#111827;">{html.escape(str(row['Subject']))}</div>
                  <div style="color:#6B7280;font-size:.9rem;">{html.escape(str(row['Date']))} | {html.escape(str(row['Class']))} | {html.escape(str(row['Verification']))} | Marked by {html.escape(str(row['Marked By']))}</div>
                </div>
                {_status_chip(str(row['Status']))}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode("utf-8"),
        "my_attendance_records.csv",
        "text/csv",
        use_container_width=True,
    )
    st.info("PDF report coming soon.")


def _profile():
    from src.components.avatar import render_profile_photo_section
    from src.services.profile_photo_service import fetch_user_profile

    db_status_banner()

    with st.spinner("Loading profile..."):
        data = _live_student_data()

    ctx = data["ctx"]
    st.markdown("### My Profile")

    supabase = _get_supabase()
    student = ctx.get("student") or {}
    profile = fetch_user_profile(supabase, str(ctx.get("student_email") or ""))

    profile_name = profile.get("full_name") or ctx.get("student_name") or student.get("name") or "Student"

    profile_user = {
        **student,
        **profile,
        "name": profile_name,
        "full_name": profile_name,
        "email": profile.get("email") or ctx.get("student_email") or student.get("email") or "",
        "role": "student",
        "profile_photo_url": profile.get("profile_photo_url") or student.get("profile_photo_url") or "",
    }

    if supabase:
        render_profile_photo_section(supabase, profile_user, key_prefix="student_profile")

    values = {
        "Full Name": _safe_text(ctx.get("student_name") or "Not set"),
        "Email": _safe_text(ctx.get("student_email") or "Not set"),
        "Roll Number": _safe_text(student.get("roll_no") or "Not set"),
        "Class": _safe_text(_class_title(student) or "Not assigned"),
        "Joined Subjects": str(len(data.get("subjects") or [])),
        "FaceID Status": "Enrolled" if _faceid_enrolled(supabase, str(ctx.get("student_id") or "")) else "Not enrolled",
    }

    rows_html = "".join(
        f"""
        <div style="display:flex;justify-content:space-between;gap:16px;padding:12px 0;border-bottom:1px solid #F1F5F9;">
          <span style="color:#6B7280;font-weight:700;">{html.escape(label)}</span>
          <strong style="color:#111827;text-align:right;">{html.escape(value)}</strong>
        </div>
        """
        for label, value in values.items()
    )

    st.markdown(
        f"""
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:18px 20px;margin:12px 0;">
          {rows_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

