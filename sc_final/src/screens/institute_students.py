"""Institute Students management page."""
from __future__ import annotations

import html
import uuid
from typing import Any

import streamlit as st

from src.components.avatar import avatar_html
from src.components.form_controls import format_class_option, safe_selectbox
from src.components.user_identity import password_status_label, render_password_reset, role_badge
from src.services.admin_context import get_current_institute_id
from src.services.admin_student_service import add_student, list_classes, list_students
from src.services.institute_service import _db, init_institute_state
from src.services.profile_photo_service import profile_photos_by_email
from src.utils.perf import perf_enabled


def _text(value: Any) -> str:
    return str(value or "").strip()


def _show_debug(data: Any) -> None:
    if not perf_enabled():
        return
    with st.expander("Developer Debug", expanded=False):
        st.code(str(data))


def _class_success_label(class_record: dict[str, Any]) -> str:
    class_name = _text(class_record.get("class_name") or class_record.get("name") or "Class")
    section = _text(class_record.get("section"))
    return f"Class {class_name} - Section {section}" if section else f"Class {class_name}"


def _fallback_classes(inst_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in st.session_state.get("classes", [])
        if _text(row.get("institute_id")) == _text(inst_id)
    ]


def _fallback_students(inst_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in st.session_state.get("students", [])
        if _text(row.get("institute_id")) == _text(inst_id)
    ]


def _load_classes(inst_id: str) -> list[dict[str, Any]]:
    if _db() and inst_id:
        return list_classes(inst_id)
    return _fallback_classes(inst_id)


def _load_students(inst_id: str) -> list[dict[str, Any]]:
    if _db() and inst_id:
        return list_students(inst_id)
    return _fallback_students(inst_id)


def _show_student_success(student: dict[str, Any], code: str) -> None:
    name = _text(student.get("name")) or "Student"
    email = _text(student.get("email"))
    roll_no = _text(student.get("roll_no"))
    invite_message = (
        f"Hi {name}, your SnapClass AI student code is {code}. "
        "Register in the Student Portal using this same email."
    )
    st.success("Student added successfully. Student should login with the same email.")
    st.write(f"Name: {name}")
    st.write(f"Roll No: {roll_no}")
    st.write(f"Email/Login: {email}")
    st.write(f"Student Code: {code}")
    st.info("Next step: the student can register/login with this email and code, then view attendance reports.")
    st.code(code)
    st.text_area("Invite message", value=invite_message, height=92, key=f"student_invite_message_{code}")


def _render_add_student(inst_id: str, classes: list[dict[str, Any]]) -> None:
    st.subheader("Add New Student")
    st.caption("Create the student record with the same email they will use for login.")

    if not classes:
        st.info("Please create a class first before adding students.")
        return

    with st.form("add_student_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        s_name = c1.text_input("Student Name *", placeholder="Aarav Sharma")
        s_roll = c2.text_input("Roll Number *", placeholder="12A-01")

        selected_class = safe_selectbox(
            "Class *",
            classes,
            key="admin_student_class_select",
            format_func=format_class_option,
            index=None,
            placeholder="Choose class",
            show_selected=False,
        )
        if selected_class:
            st.success(f"Selected Class: {_class_success_label(selected_class)}")
        else:
            st.info("Select a class before adding a student.")

        c3, c4 = st.columns(2)
        s_email = c3.text_input("Email *", placeholder="student@example.com")
        s_phone = c4.text_input("Phone", placeholder="+91 98765 43210")

        c5, c6 = st.columns(2)
        p_name = c5.text_input("Parent Name")
        p_phone = c6.text_input("Parent Phone")
        submitted = st.form_submit_button("Add Student", type="primary", use_container_width=True)

    if not submitted:
        return

    if _db() and inst_id:
        result = add_student(
            institute_id=inst_id,
            name=s_name,
            email=s_email,
            roll_no=s_roll,
            class_record=selected_class,
            phone=s_phone,
            parent_name=p_name,
            parent_phone=p_phone,
        )
        if result.get("ok"):
            student = result.get("student") or {}
            code = _text(result.get("student_code") or student.get("student_code"))
            if result.get("login_pending"):
                st.warning(result.get("message") or "Student saved. Login account pending.")
            _show_student_success(student, code)
        else:
            st.error(result.get("message") or "Student could not be saved.")
            if result.get("debug"):
                _show_debug(result.get("debug"))
        return

    if not selected_class:
        st.error("Select a class before adding a student.")
        return
    if not _text(s_name) or not _text(s_roll) or "@" not in _text(s_email):
        st.error("Student name, roll number, and a valid email are required.")
        return

    email_norm = _text(s_email).lower()
    class_id = _text(selected_class.get("id"))
    duplicate_email = any(_text(row.get("email")).lower() == email_norm for row in _fallback_students(inst_id))
    duplicate_roll = any(
        _text(row.get("class_id")) == class_id and _text(row.get("roll_no")).lower() == _text(s_roll).lower()
        for row in _fallback_students(inst_id)
    )
    if duplicate_email:
        st.error("A student with this email already exists.")
        return
    if duplicate_roll:
        st.error("This roll number already exists in the selected class.")
        return

    code = "STU-DEMO"
    record = {
        "id": str(uuid.uuid4()),
        "institute_id": inst_id,
        "class_id": class_id,
        "class_name": _text(selected_class.get("class_name") or selected_class.get("name")),
        "section": _text(selected_class.get("section")),
        "roll_no": _text(s_roll),
        "name": _text(s_name),
        "email": email_norm,
        "phone": _text(s_phone),
        "parent_name": _text(p_name),
        "parent_phone": _text(p_phone),
        "student_code": code,
        "invite_status": "pending",
        "status": "active",
    }
    st.session_state.students.append(record)
    _show_student_success(record, code)


def _render_students_list(inst_id: str, students: list[dict[str, Any]]) -> None:
    st.subheader("Students List")

    if not students:
        st.info("No students added yet. Add your first student, then they can login and view attendance reports.")
        return

    search = st.text_input("Search Students", placeholder="Name, email, or roll...", key="s_search")
    if search:
        needle = search.strip().lower()
        students = [
            row
            for row in students
            if needle in _text(row.get("name")).lower()
            or needle in _text(row.get("email")).lower()
            or needle in _text(row.get("roll_no")).lower()
        ]

    joined_subjects: dict[str, list[str]] = {}
    db = _db()
    photo_by_email = profile_photos_by_email(
        db,
        [_text(student.get("email")) for student in students],
    )
    student_ids = [_text(row.get("id")) for row in students if row.get("id")]
    if db and student_ids:
        try:
            enrollments = (
                db.table("subject_enrollments")
                .select("student_id,status,subjects(name,subject_name,code,subject_code)")
                .in_("student_id", student_ids)
                .execute()
                .data
                or []
            )
            for enrollment in enrollments:
                if _text(enrollment.get("status") or "active").lower() not in {"", "active"}:
                    continue
                subject = enrollment.get("subjects") if isinstance(enrollment.get("subjects"), dict) else {}
                label = _text(subject.get("subject_name") or subject.get("name"))
                if label:
                    joined_subjects.setdefault(_text(enrollment.get("student_id")), []).append(label)
        except Exception as exc:
            _show_debug({"student_subject_enrollments_error": str(exc)})

    for student in students:
        student_id = _text(student.get("id"))
        name = _text(student.get("name") or student.get("full_name")) or "Unknown"
        email = _text(student.get("email")) or "No email"
        roll_no = _text(student.get("roll_no")) or "-"
        class_name = _text(student.get("class_name")) or "-"
        section = _text(student.get("section"))
        class_label = f"{class_name}-{section}" if section else class_name
        status = _text(student.get("profile_status") or student.get("status") or student.get("invite_status") or "active").title()
        subjects = ", ".join(sorted(set(joined_subjects.get(student_id, [])))) or "Not joined"
        photo_url = (
            _text(student.get("profile_photo_url"))
            or photo_by_email.get(_text(student.get("email")).lower(), "")
        )
        student_avatar = avatar_html(
            {
                "name": name,
                "profile_photo_url": photo_url,
            },
            size=52,
        )

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;">
                  <div style="display:flex;gap:12px;align-items:center;">
                    {student_avatar}
                    <div>
                      <h3 style="margin:0 0 6px;">{html.escape(name)}</h3>
                      <div style="color:#6B7280;">Email: {html.escape(email)}</div>
                    </div>
                  </div>
                  {role_badge("student")}
                </div>
                <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 20px;margin-top:14px;">
                  <div><b>Status:</b> {html.escape(status)}</div>
                  <div><b>Roll No:</b> {html.escape(roll_no)}</div>
                  <div><b>Class:</b> {html.escape(class_label)}</div>
                  <div><b>Joined Subjects:</b> {html.escape(subjects)}</div>
                  <div><b>Password:</b> {password_status_label(student)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_password_reset(
                _text(student.get("email")),
                key=f"reset_student_password_{student_id}",
            )


def show_students() -> None:
    init_institute_state()
    inst_id = get_current_institute_id()

    st.markdown("### Students")
    st.caption("Add students, map their login email, and review student records.")

    if not inst_id:
        st.warning("Please log in again with your institute admin account.")
        return

    classes = _load_classes(inst_id)
    _render_add_student(inst_id, classes)

    st.divider()
    students = _load_students(inst_id)
    _render_students_list(inst_id, students)
