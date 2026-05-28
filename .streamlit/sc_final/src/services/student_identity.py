"""Student identity resolver.

Goal: ensure all student pages use the same resolved Supabase `students.id`
(Student ID) and related fields from `st.session_state`.

This module is intentionally defensive: it can be used even when some
session keys differ between login flows.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st


def _get_email_keys() -> list[str]:
    # Different parts of the app may store email under different keys.
    return ["student_email", "user_email", "email"]


def _candidate_roll_keys() -> list[str]:
    return ["roll_no", "user_roll", "user_roll_no", "roll"]


def _candidate_name_keys() -> list[str]:
    return ["student_name", "user_name", "name"]


def _get_first_non_empty(d: dict[str, Any], keys: list[str]) -> Optional[Any]:
    for k in keys:
        v = d.get(k)
        if v is not None and str(v).strip() != "":
            return v
    return None


def resolve_student_identity(supabase) -> Optional[str]:
    """Resolve and store student identity in session_state.

    Resolution priority:
      1) st.session_state['student_id']
      2) email match against students.email/user_email
      3) roll_no match against students.roll_no
      4) name match against students.name (best-effort)

    When a student is found, stores:
      - st.session_state['student_id']
      - st.session_state['roll_no']
      - st.session_state['student_name']
      - st.session_state['student_class']

    Returns resolved student_id (or None).
    """

    # Already resolved.
    existing = st.session_state.get("student_id")
    if existing:
        st.session_state["student_id"] = str(existing)
        return str(existing)

    user_obj = st.session_state.get("user", {}) or {}

    # Candidate values from session.
    session_email = _get_first_non_empty(st.session_state, _get_email_keys()) or user_obj.get("email")
    session_roll = _get_first_non_empty(st.session_state, _candidate_roll_keys()) or user_obj.get("roll_no")
    session_name = _get_first_non_empty(st.session_state, _candidate_name_keys()) or user_obj.get("name")

    # If Supabase is not available, we can only set what we already have.
    if not supabase:
        if session_roll:
            st.session_state["roll_no"] = str(session_roll)
        if session_name:
            st.session_state["student_name"] = str(session_name)
        return None

    # 1) Try email.
    if session_email:
        try:
            # Prefer column `email` (schema in this repo uses students.email).
            res = (
                supabase.table("students")
                .select("id,roll_no,name,class_name,email")
                .eq("email", session_email)
                .limit(1)
                .execute()
            )
            data = res.data or []
            if data:
                row = data[0]
                _store_from_row(row)
                return str(row.get("id"))
        except Exception:
            # Fall through to other matching.
            pass

    # 2) Try roll.
    if session_roll:
        try:
            res = (
                supabase.table("students")
                .select("id,roll_no,name,class_name,email")
                .eq("roll_no", str(session_roll))
                .limit(1)
                .execute()
            )
            data = res.data or []
            if data:
                row = data[0]
                _store_from_row(row)
                return str(row.get("id"))
        except Exception:
            pass

    # 3) Try name (best-effort).
    if session_name:
        try:
            res = (
                supabase.table("students")
                .select("id,roll_no,name,class_name,email")
                .eq("name", str(session_name))
                .limit(1)
                .execute()
            )
            data = res.data or []
            if data:
                row = data[0]
                _store_from_row(row)
                return str(row.get("id"))
        except Exception:
            pass

    return None


def _store_from_row(row: dict[str, Any]) -> None:
    student_id = row.get("id")
    if student_id:
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

    # Keep also legacy keys used by other pages.
    if name is not None and not st.session_state.get("user_name"):
        st.session_state["user_name"] = str(name)
    if roll_no is not None and not st.session_state.get("user_roll"):
        st.session_state["user_roll"] = str(roll_no)

