"""Reusable form controls that avoid blank Streamlit dropdown labels."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypeVar

import streamlit as st

T = TypeVar("T")


def _option_label(option: Any) -> str:
    if isinstance(option, dict):
        return str(
            option.get("label")
            or option.get("name")
            or option.get("title")
            or option.get("email")
            or option.get("code")
            or option.get("plan_code")
            or option.get("id")
            or "Unnamed"
        )
    return str(option) if option is not None else "Unnamed"


def format_institute_option(institute: Any) -> str:
    if not institute:
        return "Select institute"
    if not isinstance(institute, dict):
        return str(institute)

    name = str(institute.get("name") or "").strip() or "Unnamed Institute"
    city = str(institute.get("city") or "").strip()
    state = str(institute.get("state") or "").strip()
    admin_email = str(
        institute.get("admin_email") or institute.get("email") or "No admin"
    ).strip()
    location = ", ".join(part for part in (city, state) if part)
    if location:
        return f"{name} - {location} - {admin_email}"
    return f"{name} - {admin_email}"


def format_class_option(class_record: Any) -> str:
    if not class_record:
        return "Select class"
    if not isinstance(class_record, dict):
        return str(class_record)

    class_name = str(
        class_record.get("class_name") or class_record.get("name") or "Class"
    ).strip()
    section = str(class_record.get("section") or "").strip()
    return f"Class {class_name} - Section {section}" if section else f"Class {class_name}"


def format_subject_option(subject: Any) -> str:
    if not subject:
        return "Select subject"
    if not isinstance(subject, dict):
        return str(subject)

    name = str(
        subject.get("subject_name") or subject.get("name") or "Subject"
    ).strip()
    code = str(subject.get("subject_code") or subject.get("code") or "").strip()
    return f"{name} ({code})" if code else name


def format_student_option(student: Any) -> str:
    if not student:
        return "Select student"
    if not isinstance(student, dict):
        return str(student)

    name = str(student.get("name") or "Student").strip()
    roll = str(student.get("roll_no") or student.get("roll") or "No Roll").strip()
    return f"{name} - Roll {roll}"


def safe_selectbox(
    label: str,
    options: Iterable[T] | None,
    *,
    key: str | None = None,
    format_func: Callable[[T], Any] | None = None,
    help: str | None = None,
    index: int | None = 0,
    placeholder: str = "Choose an option",
    disabled: bool = False,
    show_selected: bool = True,
    selected_prefix: str | None = None,
) -> T | None:
    """Safe Streamlit selectbox wrapper with readable labels.

    Use this for dict/object options so the collapsed selected value is always
    readable and a small selected-value preview can be rendered consistently.
    """
    clean_options = list(options or [])

    if not clean_options:
        st.warning(f"No options available for {label}.")
        return None

    def safe_format(option: T) -> str:
        try:
            if format_func:
                value = format_func(option)
                return str(value) if value is not None else "Unnamed"
            return _option_label(option)
        except Exception:
            return _option_label(option)

    safe_index = index
    if safe_index is not None and (
        safe_index < 0 or safe_index >= len(clean_options)
    ):
        safe_index = 0

    selected = st.selectbox(
        label=label,
        options=clean_options,
        index=safe_index,
        format_func=safe_format,
        key=key,
        help=help,
        placeholder=placeholder,
        disabled=disabled,
        label_visibility="visible",
    )

    if show_selected and selected is not None:
        prefix = selected_prefix or f"Selected {label}"
        st.caption(f"{prefix}: {safe_format(selected)}")

    return selected
