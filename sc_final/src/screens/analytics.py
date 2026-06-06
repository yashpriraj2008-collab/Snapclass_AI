"""Institute Admin — Analytics."""

from __future__ import annotations

import streamlit as st

from src.services.admin_context import get_current_institute_id
from src.services.institute_service import init_institute_state, _db


def _db_safe():
    try:
        return _db()
    except Exception:
        return None


def show_analytics():
    init_institute_state()
    st.markdown("### 📊 Analytics")

    inst_id = get_current_institute_id()
    if not inst_id:
        st.warning("Please log in again with your institute admin account.")
        return

    db = _db_safe()

    # If Supabase isn't connected, avoid presenting demo numbers as real analytics.
    if not db:
        st.info("No analytics data yet. Add students and mark attendance first.")
        return

    try:
        teachers = (
            db.table("teachers").select("id").eq("institute_id", inst_id).execute().data or []
        )
        students = (
            db.table("students").select("id").eq("institute_id", inst_id).execute().data or []
        )
        classes = (
            db.table("classes").select("id").eq("institute_id", inst_id).execute().data or []
        )
        subjects = (
            db.table("subjects").select("id").eq("institute_id", inst_id).execute().data or []
        )

        sessions = (
            db.table("attendance_sessions")
            .select("id")
            .eq("institute_id", inst_id)
            .execute()
            .data
            or []
        )
        session_ids = [row.get("id") for row in sessions if row.get("id")]
        if session_ids:
            att = (
                db.table("attendance_records")
                .select("student_id,status")
                .in_("session_id", session_ids)
                .execute()
                .data
                or []
            )
        else:
            att = []
        total = len(att)
        present = sum(1 for r in att if str(r.get("status")).lower() in {"present", "late"})
        absent = sum(1 for r in att if str(r.get("status")).lower() == "absent")

        threshold = st.session_state.get("attendance_threshold") or (
            db.table("institutes")
            .select("attendance_threshold")
            .eq("id", inst_id)
            .limit(1)
            .execute()
            .data
            or [{}]
        )[0].get("attendance_threshold", 75)

        # Compute per-student pct.
        att2 = att
        by_sid = {}
        for r in att2:
            sid = r.get("student_id")
            if not sid:
                continue
            by_sid.setdefault(sid, []).append(str(r.get("status")).lower())

        low_attendance_count = 0
        for _, statuses in by_sid.items():
            t = len(statuses)
            if t == 0:
                continue
            p = sum(1 for s in statuses if s in {"present", "late"})
            pct = (p / t) * 100
            if pct < float(threshold):
                low_attendance_count += 1

        if total == 0:
            st.info("No analytics data yet. Add students and mark attendance first.")
            return

        overall_pct = round((present / total) * 100, 1) if total else 0.0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Overall Attendance %", f"{overall_pct}%")
        c2.metric("Total Students", len(students))
        c3.metric("Total Teachers", len(teachers))
        c4.metric("Total Classes", len(classes))
        c5.metric("Low Attendance", low_attendance_count)

        # Simple charts
        import pandas as pd
        import altair as alt

        df = pd.DataFrame(
            [
                {"status": "present", "count": present},
                {"status": "absent", "count": absent},
            ]
        )
        bar = (
            alt.Chart(df)
            .mark_bar()
            .encode(x="status", y="count", color="status")
            .properties(height=220)
        )
        st.subheader("Attendance Status Split")
        st.altair_chart(bar, use_container_width=True)

    except Exception:
        st.info("No analytics data yet. Add students and mark attendance first.")
