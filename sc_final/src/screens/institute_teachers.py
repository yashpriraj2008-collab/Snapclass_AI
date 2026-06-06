"""Institute Teachers management page."""
from __future__ import annotations

import html
import json
import uuid
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from src.components.avatar import avatar_html
from src.components.form_controls import (
    format_class_option,
    format_subject_option,
    safe_selectbox,
)
from src.components.user_identity import password_status_label, render_password_reset, role_badge
from src.services.admin_context import get_current_institute_id
from src.services.admin_teacher_service import (
    add_teacher,
    assign_teacher,
    assignment_counts,
    list_classes,
    list_subjects,
    list_teacher_assignments,
    list_teachers,
)
from src.services.institute_service import _db, init_institute_state
from src.services.profile_photo_service import profile_photos_by_email
from src.utils.perf import perf_enabled


def _copy_tools(code: str, message: str) -> None:
    code_json = json.dumps(code)
    message_json = json.dumps(message)
    components.html(
        f"""
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 2px;">
          <button onclick='navigator.clipboard.writeText({code_json})'
            style="border:1px solid #d1d5db;border-radius:6px;background:white;padding:7px 10px;cursor:pointer;">
            Copy Code
          </button>
          <button onclick='navigator.clipboard.writeText({message_json})'
            style="border:1px solid #d1d5db;border-radius:6px;background:white;padding:7px 10px;cursor:pointer;">
            Copy Invite Message
          </button>
        </div>
        """,
        height=46,
    )


def _text(value: Any) -> str:
    return str(value or "").strip()


def _show_debug(data: Any) -> None:
    if not perf_enabled():
        return
    with st.expander("Developer Debug", expanded=False):
        st.code(str(data))


def _teacher_label(teacher: dict[str, Any]) -> str:
    if not isinstance(teacher, dict):
        return _text(teacher) or "Select teacher"
    name = _text(teacher.get("name")) or "Unnamed Teacher"
    email = _text(teacher.get("email")) or "No email"
    code = _text(teacher.get("teacher_code") or teacher.get("invite_code"))
    return f"{name} - {email}" + (f" - {code}" if code else "")


def _status_label(value: Any) -> str:
    return _text(value).title() if value else "Active"


def _fallback_teachers(inst_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in st.session_state.get("teachers", [])
        if _text(row.get("institute_id")) == _text(inst_id)
    ]


def _fallback_classes(inst_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in st.session_state.get("classes", [])
        if _text(row.get("institute_id")) == _text(inst_id)
    ]


def _fallback_subjects(inst_id: str, class_id: str | None = None) -> list[dict[str, Any]]:
    rows = [
        row
        for row in st.session_state.get("subjects", [])
        if _text(row.get("institute_id")) == _text(inst_id)
    ]
    if class_id:
        rows = [row for row in rows if _text(row.get("class_id")) == _text(class_id)]
    return rows


def _load_page_data(inst_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    if _db() and inst_id:
        teachers = list_teachers(inst_id)
        classes = list_classes(inst_id)
        subjects = list_subjects(inst_id)
        counts = assignment_counts(inst_id)
        return teachers, classes, subjects, counts

    teachers = _fallback_teachers(inst_id)
    classes = _fallback_classes(inst_id)
    subjects = _fallback_subjects(inst_id)
    counts: dict[str, int] = {}
    for assignment in st.session_state.get("teacher_assignments", []):
        teacher_id = _text(assignment.get("teacher_id"))
        if _text(assignment.get("institute_id")) == _text(inst_id) and teacher_id:
            counts[teacher_id] = counts.get(teacher_id, 0) + 1
    return teachers, classes, subjects, counts


def _render_teacher_success(teacher: dict[str, Any], code: str) -> None:
    teacher_name = _text(teacher.get("name")) or "Teacher"
    teacher_email = _text(teacher.get("email"))
    invite_message = (
        f"Hi {teacher_name}, your SnapClass AI teacher invite code is {code}. "
        "Use this code to register in the Teacher Portal with this same email."
    )
    st.success("Teacher added. Now assign this teacher to a class/subject.")
    st.markdown(
        f"""
        **Teacher:** {html.escape(teacher_name)}<br>
        **Email:** {html.escape(teacher_email)}<br>
        **Invite Code:** `{html.escape(code)}`<br><br>
        Login is not created here. The teacher should register from the Teacher Portal using this email and code.
        """,
        unsafe_allow_html=True,
    )
    st.code(code)
    st.text_area("Invite message", value=invite_message, height=92, key="teacher_invite_message")
    _copy_tools(code, invite_message)


def _render_add_teacher(inst_id: str) -> None:
    st.subheader("Add New Teacher")
    st.caption("Create the teacher profile first. You can assign classes and subjects below.")

    with st.form("add_teacher_form"):
        c1, c2 = st.columns(2)
        t_name = c1.text_input("Teacher Name *", placeholder="Dr. Priya Sharma")
        t_email = c2.text_input("Email *", placeholder="teacher@school.com")
        c3, c4 = st.columns(2)
        t_phone = c3.text_input("Phone", placeholder="+91 98765 43210")
        t_code = c4.text_input("Teacher Code", placeholder="Auto-generated if empty")
        submitted = st.form_submit_button("Add Teacher", type="primary", use_container_width=True)

    if not submitted:
        return

    if _db() and inst_id:
        result = add_teacher(
            institute_id=inst_id,
            name=t_name,
            email=t_email,
            phone=t_phone,
            teacher_code=t_code,
        )
        if result.get("ok"):
            teacher = result.get("teacher") or {}
            code = _text(result.get("invite_code") or teacher.get("invite_code") or result.get("teacher_code") or teacher.get("teacher_code"))
            if result.get("login_pending"):
                st.warning(result.get("message") or "Teacher saved. Login account pending.")
            _render_teacher_success(teacher, code)
        else:
            st.error(result.get("message") or "Teacher could not be saved.")
            if result.get("debug"):
                _show_debug(result.get("debug"))
        return

    if not _text(t_name) or "@" not in _text(t_email):
        st.error("Teacher name and a valid email are required.")
        return

    email_norm = _text(t_email).lower()
    existing = [
        row
        for row in _fallback_teachers(inst_id)
        if _text(row.get("email")).lower() == email_norm
    ]
    if existing:
        st.error("A teacher with this email already exists.")
        return

    code = _text(t_code).upper() or "TCH-DEMO"
    record = {
        "id": str(uuid.uuid4()),
        "institute_id": inst_id,
        "name": _text(t_name),
        "email": email_norm,
        "phone": _text(t_phone),
        "teacher_code": code,
        "invite_code": code,
        "invite_status": "pending",
        "status": "active",
    }
    st.session_state.teachers.append(record)
    _render_teacher_success(record, code)


def _render_assign_teacher(inst_id: str, teachers: list[dict[str, Any]], classes: list[dict[str, Any]]) -> None:
    st.subheader("Assign Teacher to Class/Subject")

    if not teachers:
        st.info("Add a teacher first, then assign them to a class and subject.")
        return
    if not classes:
        st.info("Add classes first before assigning teachers.")
        return

    selected_teacher = safe_selectbox(
        "Teacher",
        teachers,
        key="assign_teacher_teacher",
        format_func=_teacher_label,
        index=None,
        placeholder="Choose a teacher",
        selected_prefix="Selected Teacher",
    )
    selected_class = safe_selectbox(
        "Class",
        classes,
        key="assign_teacher_class",
        format_func=format_class_option,
        index=None,
        placeholder="Choose a class",
        selected_prefix="Selected Class",
    )

    class_id = _text((selected_class or {}).get("id"))
    if not class_id:
        st.info("Select a class to load subjects for assignment.")
        return

    subjects = list_subjects(inst_id, class_id) if _db() and class_id else _fallback_subjects(inst_id, class_id)
    if not subjects:
        st.info("Add subjects for the selected class before assigning teachers.")
        return

    selected_subject = safe_selectbox(
        "Subject",
        subjects,
        key="assign_teacher_subject",
        format_func=format_subject_option,
        index=None,
        placeholder="Choose a subject",
        selected_prefix="Selected Subject",
    )

    assignment_type = st.radio(
        "Assignment Type",
        ["subject_teacher", "class_teacher"],
        horizontal=True,
        key="assign_teacher_type",
    )

    if not st.button("Assign Teacher", type="primary", use_container_width=True, key="assign_teacher_submit"):
        return

    teacher_id = _text((selected_teacher or {}).get("id"))
    subject_id = _text((selected_subject or {}).get("id"))

    if _db() and inst_id:
        result = assign_teacher(
            institute_id=inst_id,
            teacher_id=teacher_id,
            class_id=class_id,
            subject_id=subject_id,
            assignment_type=assignment_type,
        )
        if result.get("ok"):
            st.success("Teacher assigned successfully.")
            st.rerun()
        else:
            st.error(result.get("message") or "Teacher assignment could not be saved.")
            if result.get("debug"):
                _show_debug(result.get("debug"))
        return

    if not all([teacher_id, class_id, subject_id]):
        st.error("Select teacher, class, and subject.")
        return

    assignments = st.session_state.setdefault("teacher_assignments", [])
    duplicate = any(
        _text(row.get("teacher_id")) == teacher_id
        and _text(row.get("class_id")) == class_id
        and _text(row.get("subject_id")) == subject_id
        for row in assignments
    )
    if duplicate:
        st.error("This teacher is already assigned to that class and subject.")
        return

    assignments.append(
        {
            "id": str(uuid.uuid4()),
            "institute_id": inst_id,
            "teacher_id": teacher_id,
            "class_id": class_id,
            "subject_id": subject_id,
            "assignment_type": assignment_type,
            "status": "active",
        }
    )
    st.success("Teacher assigned successfully.")


def _render_teachers_list(
    inst_id: str,
    teachers: list[dict[str, Any]],
    assignment_count_by_teacher: dict[str, int],
) -> None:
    st.subheader("Teachers List")

    if not teachers:
        st.info(
            "No teachers added yet. Add your first teacher, then assign them to a class and subject so they can mark attendance."
        )
        return

    search = st.text_input("Search Teachers", placeholder="Name or email...", key="t_search")
    if search:
        needle = search.strip().lower()
        teachers = [
            teacher
            for teacher in teachers
            if needle in _text(teacher.get("name")).lower()
            or needle in _text(teacher.get("email")).lower()
        ]

    assignments = list_teacher_assignments(inst_id) if _db() and inst_id else st.session_state.get("teacher_assignments", [])
    photo_by_email = profile_photos_by_email(
        _db(),
        [_text(teacher.get("email")) for teacher in teachers],
    )
    assignments_by_teacher: dict[str, list[dict[str, Any]]] = {}
    for assignment in assignments:
        if _text(assignment.get("institute_id")) != _text(inst_id):
            continue
        assignments_by_teacher.setdefault(_text(assignment.get("teacher_id")), []).append(assignment)

    for teacher in teachers:
        teacher_id = _text(teacher.get("id"))
        teacher_assignments = assignments_by_teacher.get(teacher_id, [])
        class_labels = sorted({
            format_class_option(row.get("classes"))
            for row in teacher_assignments
            if isinstance(row.get("classes"), dict)
        })
        subject_labels = sorted({
            format_subject_option(row.get("subjects"))
            for row in teacher_assignments
            if isinstance(row.get("subjects"), dict)
        })
        name = html.escape(_text(teacher.get("name")) or "Unknown")
        email = html.escape(_text(teacher.get("email")) or "No email")
        status = html.escape(_status_label(teacher.get("profile_status") or teacher.get("status") or teacher.get("invite_status")))
        teacher_code = html.escape(_text(teacher.get("teacher_code") or teacher.get("invite_code")) or "-")
        classes_text = html.escape(", ".join(class_labels) or "Not assigned")
        subjects_text = html.escape(", ".join(subject_labels) or "Not assigned")
        password_status = password_status_label(teacher)
        photo_url = (
            _text(teacher.get("profile_photo_url"))
            or photo_by_email.get(_text(teacher.get("email")).lower(), "")
        )
        teacher_avatar = avatar_html(
            {
                "name": _text(teacher.get("name")) or "Teacher",
                "profile_photo_url": photo_url,
            },
            size=52,
        )

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;">
                  <div style="display:flex;gap:12px;align-items:center;">
                    {teacher_avatar}
                    <div>
                      <h3 style="margin:0 0 6px;">{name}</h3>
                      <div style="color:#6B7280;">Email: {email}</div>
                    </div>
                  </div>
                  {role_badge("teacher")}
                </div>
                <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 20px;margin-top:14px;">
                  <div><b>Status:</b> {status}</div>
                  <div><b>Teacher Code:</b> {teacher_code}</div>
                  <div><b>Assigned Class:</b> {classes_text}</div>
                  <div><b>Assigned Subject:</b> {subjects_text}</div>
                  <div><b>Password:</b> {password_status}</div>
                  <div><b>Assignments:</b> {assignment_count_by_teacher.get(teacher_id, 0)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_password_reset(
                _text(teacher.get("email")),
                key=f"reset_teacher_password_{teacher_id}",
            )


def show_teachers() -> None:
    init_institute_state()
    st.session_state.setdefault("teacher_assignments", [])

    inst_id = get_current_institute_id()
    st.markdown("### Teachers")
    st.caption("Add teachers, map their teacher profile, and assign class/subject access.")

    if not inst_id:
        st.warning("Please log in again with your institute admin account.")
        return

    _render_add_teacher(inst_id)
    st.divider()

    teachers, classes, _subjects, counts = _load_page_data(inst_id)
    _render_assign_teacher(inst_id, teachers, classes)
    st.divider()

    teachers, _classes, _subjects, counts = _load_page_data(inst_id)
    _render_teachers_list(inst_id, teachers, counts)
