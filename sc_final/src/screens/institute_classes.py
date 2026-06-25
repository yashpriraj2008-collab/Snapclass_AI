"""Classes & Subjects management for institute admin."""
from __future__ import annotations

import uuid
from typing import Any

import pandas as pd
import streamlit as st

from src.components.form_controls import format_class_option, safe_selectbox
from src.services.admin_class_subject_service import (
    add_class,
    add_subject,
    list_classes,
    list_students,
    list_subjects,
    list_teachers,
)
from src.services.admin_context import get_current_institute_id
from src.services.admin_teacher_service import list_teacher_assignments
from src.services.institute_service import _db, init_institute_state


def _text(value: Any) -> str:
    return str(value or "").strip()


def _fallback_rows(key: str, inst_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in st.session_state.get(key, [])
        if _text(row.get("institute_id")) == _text(inst_id)
    ]


def _load_classes(inst_id: str) -> list[dict[str, Any]]:
    if _db() and inst_id:
        return list_classes(inst_id)
    return _fallback_rows("classes", inst_id)


def _load_subjects(inst_id: str) -> list[dict[str, Any]]:
    if _db() and inst_id:
        return list_subjects(inst_id)
    return _fallback_rows("subjects", inst_id)


def _load_students(inst_id: str) -> list[dict[str, Any]]:
    if _db() and inst_id:
        return list_students(inst_id)
    return _fallback_rows("students", inst_id)


def _load_teachers(inst_id: str) -> list[dict[str, Any]]:
    if _db() and inst_id:
        return list_teachers(inst_id)
    return _fallback_rows("teachers", inst_id)


def _teacher_label(teacher: dict[str, Any] | None) -> str:
    if not teacher:
        return "No teacher"
    name = _text(teacher.get("name")) or "Unnamed Teacher"
    email = _text(teacher.get("email"))
    return f"{name} - {email}" if email else name


def _setup_progress(
    inst_id: str,
    classes: list[dict[str, Any]],
    subjects: list[dict[str, Any]],
    students: list[dict[str, Any]],
    teachers: list[dict[str, Any]],
) -> None:
    st.subheader("Setup Progress")
    if _db() and inst_id:
        assignments = list_teacher_assignments(inst_id)
    else:
        assignments = [
            row for row in st.session_state.get("teacher_assignments", [])
            if _text(row.get("institute_id")) == _text(inst_id)
        ]
    assignment_done = bool(assignments) and bool(classes) and bool(subjects) and bool(teachers)
    items = [
        ("Class created", bool(classes)),
        ("Subject added", bool(subjects)),
        ("Teacher added", bool(teachers)),
        ("Teacher assigned", assignment_done),
        ("Student added", bool(students)),
    ]

    # Colorize progress state:
    # - Done      => green
    # - Pending   => orange
    # - Incomplete=> red (only used if we can't compute properly)
    def _state_color(done: bool) -> str:
        return "#10B981" if done else "#F59E0B"  # green/orange

    cols = st.columns(len(items))
    for col, (label, done) in zip(cols, items):
        state = "Done" if done else "Pending"
        color = _state_color(done)
        col.markdown(
            f"""
            <div style="text-align:center;">
              <div style="font-size:.78rem;color:#6B7280;font-weight:600;margin-bottom:6px;">{label}</div>
              <div style="font-size:1.15rem;font-weight:800;color:{color};">{state}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _class_counts(classes: list[dict[str, Any]], subjects: list[dict[str, Any]], students: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts = {str(row.get("id")): {"subjects": 0, "students": 0} for row in classes}
    for subject in subjects:
        class_id = str(subject.get("class_id") or "")
        if class_id in counts:
            counts[class_id]["subjects"] += 1
    for student in students:
        class_id = str(student.get("class_id") or "")
        if class_id in counts:
            counts[class_id]["students"] += 1
    return counts


def _render_add_class(inst_id: str) -> None:
    st.subheader("Add Class")

    CLASS_NAME_OPTIONS = [
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "JEE",
        "NEET",
        "Foundation",
        "Dropper",
    ]
    SECTION_OPTIONS = ["A", "B", "C", "D", "E", "F"]
    ACADEMIC_YEAR_OPTIONS = [
        "2025-26",
        "2026-27",
        "2027-28",
        "2028-29",
    ]

    DEFAULT_ACAD_YEAR = "2026-27"

    with st.form("add_class_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        cls_name = c1.selectbox(
            "Class Name *",
            CLASS_NAME_OPTIONS,
            index=0,
            key="add_class_name_select",
        )
        section = c2.selectbox(
            "Section *",
            SECTION_OPTIONS,
            index=0,
            key="add_class_section_select",
        )
        acad_yr = c3.selectbox(
            "Academic Year *",
            ACADEMIC_YEAR_OPTIONS,
            index=ACADEMIC_YEAR_OPTIONS.index(DEFAULT_ACAD_YEAR)
            if DEFAULT_ACAD_YEAR in ACADEMIC_YEAR_OPTIONS
            else 0,
            key="add_class_acad_year_select",
        )

        # Custom gradient button so the action isn't default Streamlit styling.
        st.markdown(
            """
            <style>
              div[data-testid='stForm'] button[type='submit'] { 
                background: linear-gradient(90deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%) !important;
                color: white !important;
                border: none !important;
                border-radius: 16px !important;
                height: 52px !important;
                font-weight: 700;
              }
              div[data-testid='stForm'] button[type='submit']:hover {
                filter: brightness(1.05);
                transform: translateY(-1px);
                transition: all 120ms ease;
              }
            </style>
            """,
            unsafe_allow_html=True,
        )
        submitted = st.form_submit_button(
            "Add Class", use_container_width=True, type="primary"
        )

    if not submitted:
        return


    if _db() and inst_id:
        result = add_class(
            institute_id=inst_id,
            class_name=cls_name,
            section=section,
            academic_year=acad_yr,
        )
        if result.get("ok"):
            row = result.get("class") or {}
            st.success(
                f"Class {row.get('class_name', cls_name)}-{row.get('section', section)} created successfully. Next step: Add subjects for this class."
            )
            st.rerun()
        else:
            st.error(result.get("message") or "Class could not be saved.")
            if result.get("debug"):
                with st.expander("Developer Debug", expanded=False):
                    st.code(str(result.get("debug")))
        return

    class_name = _text(cls_name)
    section_value = _text(section).upper()
    academic_year = _text(acad_yr)
    if not class_name or not section_value or not academic_year:
        st.error("Please select class name, section, and academic year.")
        return


    duplicate = any(
        _text(row.get("class_name")).lower() == class_name.lower()
        and _text(row.get("section")).lower() == section_value.lower()
        and _text(row.get("academic_year")).lower() == academic_year.lower()
        for row in _fallback_rows("classes", inst_id)
    )
    if duplicate:
        st.error(f"Class {class_name}-{section_value} already exists for {academic_year}.")
        return

    record = {
        "id": str(uuid.uuid4()),
        "institute_id": inst_id,
        "class_name": class_name,
        "section": section_value,
        "academic_year": academic_year,
        "status": "active",
    }
    st.session_state.classes.append(record)
    st.success(f"Class {class_name}-{section_value} created successfully. Next step: Add subjects for this class.")


def _render_classes_list(classes: list[dict[str, Any]], subjects: list[dict[str, Any]], students: list[dict[str, Any]]) -> None:
    st.subheader("Classes List")
    if not classes:
        st.info("No classes added yet. Create your first class before adding students and subjects.")
        return

    counts = _class_counts(classes, subjects, students)
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Class": row.get("class_name", ""),
                    "Section": row.get("section", ""),
                    "Academic Year": row.get("academic_year", ""),
                    "Subjects": counts.get(str(row.get("id")), {}).get("subjects", 0),
                    "Students": counts.get(str(row.get("id")), {}).get("students", 0),
                    "Status": row.get("status", "active"),
                    "Actions": "Add Subject / View Students",
                }
                for row in classes
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_add_subject(inst_id: str, classes: list[dict[str, Any]], teachers: list[dict[str, Any]]) -> None:
    st.subheader("Add Subject")
    if not classes:
        st.info("Please add a class first before adding subjects.")
        return

    with st.form("add_subject_form", clear_on_submit=True):
        selected_class = safe_selectbox(
            "Class *",
            classes,
            key="subject_class_select",
            format_func=format_class_option,
            index=None,
            placeholder="Choose class",
            show_selected=False,
        )
        if selected_class:
            st.success(f"Selected Class: {format_class_option(selected_class)}")
        else:
            st.info("Select a class before adding a subject.")

        c1, c2 = st.columns(2)
        s_name = c1.text_input("Subject Name *", placeholder="Physics")
        s_code = c2.text_input("Subject Code", placeholder="PHY12")

        teacher_options: list[dict[str, Any] | None] = [None] + teachers if teachers else [None]
        selected_teacher = st.selectbox(
            "Teacher",
            teacher_options,
            format_func=_teacher_label,
            key="subject_teacher_select",
        )
        submitted = st.form_submit_button("Add Subject", type="primary", use_container_width=True)

    if not submitted:
        return

    teacher_id = _text((selected_teacher or {}).get("id")) if isinstance(selected_teacher, dict) else ""
    if _db() and inst_id:
        result = add_subject(
            institute_id=inst_id,
            class_record=selected_class,
            subject_name=s_name,
            subject_code=s_code,
            teacher_id=teacher_id,
        )
        if result.get("ok"):
            subject = result.get("subject") or {}
            st.success(f"{subject.get('subject_name', s_name)} added successfully.")
            st.rerun()
        else:
            st.error(result.get("message") or "Subject could not be saved.")
            if result.get("debug"):
                with st.expander("Developer Debug", expanded=False):
                    st.code(str(result.get("debug")))
        return

    if not selected_class:
        st.error("Select a class.")
        return
    subject_name = _text(s_name)
    subject_code = _text(s_code).upper()
    if not subject_name:
        st.error("Subject name required.")
        return

    duplicate = any(
        _text(row.get("class_id")) == _text(selected_class.get("id"))
        and (
            (subject_code and _text(row.get("subject_code")).lower() == subject_code.lower())
            or _text(row.get("subject_name") or row.get("name")).lower() == subject_name.lower()
        )
        for row in _fallback_rows("subjects", inst_id)
    )
    if duplicate:
        st.error("This subject already exists for the selected class.")
        return

    record = {
        "id": str(uuid.uuid4()),
        "institute_id": inst_id,
        "class_id": selected_class.get("id"),
        "teacher_id": teacher_id or None,
        "name": subject_name,
        "subject_name": subject_name,
        "subject_code": subject_code,
        "class_name": selected_class.get("class_name") or selected_class.get("name"),
        "section": selected_class.get("section"),
        "status": "active",
    }
    st.session_state.subjects.append(record)
    st.success(f"{subject_name} added successfully.")


def _render_subjects_list(subjects: list[dict[str, Any]], classes: list[dict[str, Any]], teachers: list[dict[str, Any]]) -> None:
    st.subheader("Subjects List")
    if not subjects:
        st.info("No subjects added yet.")
        return

    class_by_id = {str(row.get("id")): row for row in classes}
    teacher_by_id = {str(row.get("id")): row for row in teachers}
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Subject Name": row.get("subject_name") or row.get("name", ""),
                    "Subject Code": row.get("subject_code", ""),
                    "Class": (class_by_id.get(str(row.get("class_id"))) or row).get("class_name", ""),
                    "Section": (class_by_id.get(str(row.get("class_id"))) or row).get("section", ""),
                    "Teacher": _teacher_label(teacher_by_id.get(str(row.get("teacher_id")))) if row.get("teacher_id") else "-",
                    "Status": row.get("status", "active"),
                }
                for row in subjects
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def show_classes_subjects() -> None:
    init_institute_state()
    inst_id = get_current_institute_id()
    st.markdown("### Classes & Subjects")

    if not inst_id:
        st.warning("Please log in again with your institute admin account.")
        return

    classes = _load_classes(inst_id)
    subjects = _load_subjects(inst_id)
    students = _load_students(inst_id)
    teachers = _load_teachers(inst_id)
    _setup_progress(inst_id, classes, subjects, students, teachers)

    tab_cls, tab_sub = st.tabs(["Classes", "Subjects"])

    with tab_cls:
        _render_add_class(inst_id)
        st.divider()
        _render_classes_list(_load_classes(inst_id), _load_subjects(inst_id), _load_students(inst_id))

    with tab_sub:
        classes = _load_classes(inst_id)
        teachers = _load_teachers(inst_id)
        _render_add_subject(inst_id, classes, teachers)
        st.divider()
        _render_subjects_list(_load_subjects(inst_id), classes, teachers)
