"""Institute Admin — Attendance management."""

from __future__ import annotations

import streamlit as st

from src.services.institute_service import init_institute_state, _db


def _safe_db():
    try:
        return _db()
    except Exception:
        return None


def _load_classes(inst_id: str):
    db = _safe_db()
    if db and inst_id:
        try:
            return (
                db.table("classes")
                .select("id,class_name,section")
                .eq("institute_id", inst_id)
                .execute()
                .data
                or []
            )
        except Exception:
            return []
    return [c for c in st.session_state.get("classes", []) if c.get("institute_id") == inst_id]


def _load_subjects(inst_id: str, class_id: str | None):
    db = _safe_db()
    if db and inst_id:
        try:
            q = db.table("subjects").select("id,subject_name,subject_code,class_id").eq(
                "institute_id", inst_id
            )
            if class_id:
                q = q.eq("class_id", class_id)
            return q.execute().data or []
        except Exception:
            return []

    subjects = [s for s in st.session_state.get("subjects", []) if s.get("institute_id") == inst_id]
    if class_id:
        subjects = [s for s in subjects if s.get("class_id") == class_id]
    return subjects


def _load_students(inst_id: str, class_id: str | None):
    db = _safe_db()
    if db and inst_id:
        try:
            q = (
                db.table("students")
                .select("id,roll_no,name")
                .eq("institute_id", inst_id)
                .eq("status", "active")
            )
            if class_id:
                q = q.eq("class_id", class_id)
            return q.execute().data or []
        except Exception:
            return []

    students = [
        s
        for s in st.session_state.get("students", [])
        if s.get("institute_id") == inst_id and s.get("status") == "active"
    ]
    if class_id:
        students = [s for s in students if s.get("class_id") == class_id]
    return students


def show_attendance():
    init_institute_state()
    st.markdown("### ✅ Attendance")

    inst_id = st.session_state.get("active_institute_id", "")
    if not inst_id:
        st.warning("Please log in again with your access code.")
        return

    classes = _load_classes(inst_id)
    class_options = {
        f"{c.get('class_name','')} - {c.get('section','')}": c.get("id")
        for c in classes
        if c.get("id")
    }

    if not class_options:
        st.info("Please add a class first before marking attendance.")
        return

    class_label = st.selectbox(
        "Class *",
        list(class_options.keys()),
        index=None,
        placeholder="Select class",
        key="att_class_select",
    )
    selected_class_id = class_options.get(class_label) if class_label else None

    subjects = _load_subjects(inst_id, selected_class_id)
    subject_options = {
        f"{s.get('subject_name','')} ({s.get('subject_code','')})".strip(): s.get("id")
        for s in subjects
        if s.get("id")
    }

    if not subject_options:
        st.info("No subjects found for this class. Add subjects first.")
        return

    subject_label = st.selectbox(
        "Subject *",
        list(subject_options.keys()),
        index=None,
        placeholder="Select subject",
        key="att_subject_select",
    )
    selected_subject_id = subject_options.get(subject_label) if subject_label else None

    date = st.date_input("Date *", key="att_date_pick")
    date_str = date.strftime("%Y-%m-%d")

    students = _load_students(inst_id, selected_class_id)
    if not students:
        st.info("No students found in this class. Add students first.")
        return

    if "att_form" not in st.session_state:
        st.session_state.att_form = {}

    with st.form("attendance_form"):
        st.caption("Mark Present / Absent for all students")
        records = []

        for s in students:
            roll = s.get("roll_no", "")
            name = s.get("name", "")
            key = f"att_{date_str}_{selected_class_id}_{selected_subject_id}_{roll}"
            default_present = True

            present = st.checkbox(
                f"{name} — {roll}",
                value=st.session_state.att_form.get(key, default_present),
                key=key,
            )
            st.session_state.att_form[key] = present

            records.append(
                {
                    "student_id": s.get("id"),
                    "status": "present" if present else "absent",
                }
            )

        submitted = st.form_submit_button("💾 Save Attendance", type="primary", use_container_width=True)

    if not submitted:
        return

    try:
        from src.services.attendance_service import mark_manual_attendance

        db = _safe_db()
        ok, message, saved_count, errors = mark_manual_attendance(
            supabase=db,
            teacher_id=st.session_state.get("teacher_id") or st.session_state.get("user_id"),
            class_id=selected_class_id,
            subject_id=selected_subject_id,
            attendance_date=date_str,
            records=records,
        )

        if ok:
            st.success(f"Attendance saved successfully. {saved_count} records saved.")
            if errors:
                st.warning(f"{len(errors)} row(s) skipped: {', '.join(errors[:3])}")
        else:
            st.error(f"Attendance not saved: {message}")
            if errors:
                st.caption("; ".join(errors[:5]))
    except Exception as e:
        st.exception(e)
