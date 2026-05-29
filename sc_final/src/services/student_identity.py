"""Student identity resolver for SnapClass AI.

Maps the currently logged-in Streamlit user/session to public.students.id.
This resolver must be used by My Subjects, Attendance History, Reports,
Student Dashboard and FaceID pages.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

_EMAIL_KEYS = ["student_email", "user_email", "email"]
_ROLL_KEYS = ["roll_no", "user_roll", "user_roll_no", "roll"]
_NAME_KEYS = ["student_name", "user_name", "name", "full_name"]


def _first_session_value(keys: list[str]) -> Optional[str]:
    for key in keys:
        value = st.session_state.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _session_user_email() -> Optional[str]:
    direct = _first_session_value(_EMAIL_KEYS)
    if direct:
        return direct.lower()

    user = st.session_state.get("user") or st.session_state.get("auth_user") or {}
    if isinstance(user, dict):
        for key in ["email", "user_email"]:
            value = user.get(key)
            if value is not None and str(value).strip():
                return str(value).strip().lower()
    else:
        value = getattr(user, "email", None)
        if value:
            return str(value).strip().lower()

    return None


def _find_one(supabase, column: str, value: str) -> Optional[dict[str, Any]]:
    if not value:
        return None
    response = (
        supabase.table("students")
        .select("*")
        .eq(column, value)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def _find_by_name(supabase, name: str) -> Optional[dict[str, Any]]:
    if not name:
        return None
    response = (
        supabase.table("students")
        .select("*")
        .ilike("name", name)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def _store_student(row: dict[str, Any]) -> str:
    student_id = row.get("id")
    if student_id:
        st.session_state["student_id"] = str(student_id)

    if row.get("name"):
        st.session_state["student_name"] = str(row.get("name"))
        st.session_state.setdefault("user_name", str(row.get("name")))

    if row.get("email"):
        st.session_state["student_email"] = str(row.get("email")).lower()
        st.session_state.setdefault("user_email", str(row.get("email")).lower())

    if row.get("roll_no"):
        st.session_state["roll_no"] = str(row.get("roll_no"))
        st.session_state.setdefault("user_roll", str(row.get("roll_no")))

    if row.get("class_name"):
        st.session_state["student_class"] = str(row.get("class_name"))

    if row.get("section"):
        st.session_state["student_section"] = str(row.get("section"))

    if row.get("class_id"):
        st.session_state["student_class_id"] = str(row.get("class_id"))

    st.session_state["student_profile"] = row
    return str(student_id) if student_id else ""


def resolve_student_identity(supabase, show_error: bool = True) -> Optional[str]:
    """Return public.students.id and store resolved student fields in session_state."""

    existing = st.session_state.get("student_id")
    if existing:
        return str(existing)

    if not supabase:
        if show_error:
            st.error("Supabase is not connected. Student identity cannot be resolved.")
        return None

    email = _session_user_email()
    roll_no = _first_session_value(_ROLL_KEYS)
    name = _first_session_value(_NAME_KEYS)

    try:
        # Fresh query each time. Do not reuse Supabase query builder.
        row = _find_one(supabase, "email", email) if email else None
        if not row and roll_no:
            row = _find_one(supabase, "roll_no", roll_no)
        if not row and name:
            row = _find_by_name(supabase, name)

        if row:
            return _store_student(row)

    except Exception as exc:
        if show_error:
            st.error(f"Student identity lookup failed: {exc}")
        return None

    if show_error:
        st.error(
            "Student profile not found. Admin/teacher must add this student with the same login email."
        )
    return None
