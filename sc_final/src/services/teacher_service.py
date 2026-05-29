from __future__ import annotations

from typing import Any

import streamlit as st


def _get_logged_in_email() -> str | None:
    email = (
        st.session_state.get("email")
        or st.session_state.get("user_email")
        or st.session_state.get("teacher_email")
    )
    if email:
        return str(email).strip().lower()

    user = st.session_state.get("user")
    if isinstance(user, dict) and user.get("email"):
        return str(user.get("email")).strip().lower()

    return None


def resolve_teacher_identity(supabase, show_error: bool = True) -> dict[str, Any] | None:
    """Resolve the logged-in teacher to public.teachers.id."""
    if not supabase:
        if show_error:
            st.error("Supabase is not connected. Teacher identity cannot be resolved.")
        return None

    existing_id = st.session_state.get("teacher_id")
    existing_email = st.session_state.get("teacher_email")
    if existing_id and existing_email:
        return {
            "id": existing_id,
            "name": st.session_state.get("teacher_name"),
            "email": existing_email,
        }

    email = _get_logged_in_email()
    if not email:
        if show_error:
            st.error("Teacher email not found in session.")
        return None

    try:
        response = (
            supabase.table("teachers")
            .select("*")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        if not response.data:
            if show_error:
                st.error(
                    "Teacher profile not found. Admin must add this teacher with the same login email."
                )
            return None

        teacher = response.data[0]
        st.session_state["teacher_id"] = teacher.get("id")
        st.session_state["teacher_name"] = teacher.get("name")
        st.session_state["teacher_email"] = teacher.get("email")
        return teacher
    except Exception as exc:
        if show_error:
            st.error(f"Teacher identity lookup failed: {exc}")
        return None


def get_teacher_assignments(supabase, teacher_id) -> list[dict[str, Any]]:
    if not supabase or not teacher_id:
        return []

    try:
        response = (
            supabase.table("teacher_assignments")
            .select("*, classes(*), subjects(*)")
            .eq("teacher_id", teacher_id)
            .execute()
        )
        return response.data or []
    except Exception:
        try:
            response = (
                supabase.table("teacher_assignments")
                .select("*")
                .eq("teacher_id", teacher_id)
                .execute()
            )
            return response.data or []
        except Exception:
            return []
