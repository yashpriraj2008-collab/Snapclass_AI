"""Student identity resolver.

Highest-priority flow: map the logged-in user to `public.students.id`.

PRD priority order (must match):
1) If st.session_state["student_id"] already exists.
2) Else check logged-in email from session_state.
3) Else check roll_no.
4) Else check student name.
5) Query public.students.
6) If found, store:
   - st.session_state["student_id"]
   - st.session_state["student_name"]
   - st.session_state["roll_no"]
   - st.session_state["student_class"]
   - st.session_state["student_section"]
7) If not found, show exact message:
   "Student profile not found. Admin/teacher must add this student with the same login email."

This module is intentionally defensive and supports slightly different
session key names across login flows.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st


_EMAIL_KEYS: list[str] = [
    "student_email",
    "user_email",
    "email",
]

# Some flows may store a nested user object.
_USER_EMAIL_NESTED_KEYS: list[str] = ["email", "user_email"]

_ROLL_KEYS: list[str] = ["roll_no", "user_roll", "user_roll_no", "roll"]
_NAME_KEYS: list[str] = ["student_name", "user_name", "name"]


def _get_from_session_any(keys: list[str]) -> Optional[Any]:
    for k in keys:
        v = st.session_state.get(k)
        if v is not None and str(v).strip() != "":
            return v
    return None


def _get_user_nested_email(user_obj: dict[str, Any]) -> Optional[Any]:
    for k in _USER_EMAIL_NESTED_KEYS:
        v = user_obj.get(k)
        if v is not None and str(v).strip() != "":
            return v
    return None


def _first_non_empty_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def resolve_student_identity(supabase) -> Optional[str]:
    """Resolve and store student identity in session_state.

    Returns resolved student_id (string) or None.
    """

    # 1) Already resolved.
    existing = st.session_state.get("student_id")
    if existing:
        st.session_state["student_id"] = str(existing)
        # Return early; downstream pages may still need other keys.
        _hydrate_missing_from_session_only(existing)
        return str(existing)

    if not supabase:
        # Still best-effort to populate what we already have.
        _populate_from_session_only()
        return st.session_state.get("student_id")

    user_obj = st.session_state.get("user", {}) or {}

    # 2) Email
    session_email = (
        _first_non_empty_str(_get_from_session_any(_EMAIL_KEYS))
        or _first_non_empty_str(_get_user_nested_email(user_obj))
        or None
    )

    # 3) roll_no
    session_roll = _first_non_empty_str(_get_from_session_any(_ROLL_KEYS))

    # 4) student name
    session_name = _first_non_empty_str(_get_from_session_any(_NAME_KEYS))

    # If we have nothing to match with, we cannot resolve.
    if not (session_email or session_roll or session_name):
        _show_student_not_found_message()
        return None

    # 5) Query public.students with best available match.
    # Prefer email > roll_no > name (as in PRD).
    query = (
        supabase.table("students")
        .select("id,roll_no,name,class_name,section,email")
        .limit(1)
    )

    try_email = bool(session_email)
    try_roll = bool(session_roll)
    try_name = bool(session_name)

    if try_email:
        res = query.eq("email", session_email).execute()
        row = (res.data or [None])[0]
        if row:
            _store_from_row(row)
            return str(row.get("id"))

    if try_roll:
        res = query.eq("roll_no", session_roll).execute()
        row = (res.data or [None])[0]
        if row:
            _store_from_row(row)
            return str(row.get("id"))

    if try_name:
        res = query.eq("name", session_name).execute()
        row = (res.data or [None])[0]
        if row:
            _store_from_row(row)
            return str(row.get("id"))

    # 7) Not found
    _show_student_not_found_message()
    return None


def _store_from_row(row: dict[str, Any]) -> None:
    student_id = row.get("id")
    if student_id is not None:
        st.session_state["student_id"] = str(student_id)

    roll_no = row.get("roll_no")
    if roll_no is not None:
        st.session_state["roll_no"] = str(roll_no)

    name = row.get("name")
    if name is not None:
        st.session_state["student_name"] = str(name)

    class_name = row.get("class_name")
    if class_name is not None:
        st.session_state["student_class"] = str(class_name)

    section = row.get("section")
    if section is not None:
        st.session_state["student_section"] = str(section)

    # Also store legacy keys used by older parts of the app.
    if row.get("name") is not None:
        st.session_state.setdefault("user_name", str(row.get("name")))
    if row.get("roll_no") is not None:
        st.session_state.setdefault("user_roll", str(row.get("roll_no")))


def _show_student_not_found_message() -> None:
    st.error(
        "Student profile not found. Admin/teacher must add this student with the same login email."
    )


def _hydrate_missing_from_session_only(student_id: Any) -> None:
    # Only fill missing keys from what we already have.
    if not st.session_state.get("roll_no"):
        roll = _first_non_empty_str(_get_from_session_any(_ROLL_KEYS))
        if roll:
            st.session_state["roll_no"] = roll
    if not st.session_state.get("student_name"):
        name = _first_non_empty_str(_get_from_session_any(_NAME_KEYS))
        if name:
            st.session_state["student_name"] = name
    if not st.session_state.get("student_class"):
        cls = st.session_state.get("student_class") or st.session_state.get("class_name")
        cls = _first_non_empty_str(cls)
        if cls:
            st.session_state["student_class"] = cls
    if not st.session_state.get("student_section"):
        sec = st.session_state.get("student_section") or st.session_state.get("section")
        sec = _first_non_empty_str(sec)
        if sec:
            st.session_state["student_section"] = sec


def _populate_from_session_only() -> None:
    # Best-effort: if session already has some student fields, keep them.
    if not st.session_state.get("roll_no"):
        roll = _first_non_empty_str(_get_from_session_any(_ROLL_KEYS))
        if roll:
            st.session_state["roll_no"] = roll
    if not st.session_state.get("student_name"):
        name = _first_non_empty_str(_get_from_session_any(_NAME_KEYS))
        if name:
            st.session_state["student_name"] = name
    if not st.session_state.get("student_class"):
        cls = _first_non_empty_str(st.session_state.get("student_class") or st.session_state.get("class_name"))
        if cls:
            st.session_state["student_class"] = cls
    if not st.session_state.get("student_section"):
        sec = _first_non_empty_str(st.session_state.get("student_section") or st.session_state.get("section"))
        if sec:
            st.session_state["student_section"] = sec

