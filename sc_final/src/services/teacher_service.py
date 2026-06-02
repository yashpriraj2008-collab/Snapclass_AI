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


def _fetch_rows_by_ids(supabase, table: str, ids: list[str]) -> dict[str, dict[str, Any]]:
    clean_ids = sorted({str(value) for value in ids if value})
    if not supabase or not clean_ids:
        return {}

    try:
        rows = supabase.table(table).select("*").in_("id", clean_ids).execute().data or []
        return {str(row.get("id")): row for row in rows if row.get("id")}
    except Exception:
        rows_by_id: dict[str, dict[str, Any]] = {}
        for row_id in clean_ids:
            try:
                rows = (
                    supabase.table(table)
                    .select("*")
                    .eq("id", row_id)
                    .limit(1)
                    .execute()
                    .data
                    or []
                )
                if rows:
                    rows_by_id[row_id] = rows[0]
            except Exception:
                continue
        return rows_by_id


def _hydrate_assignments(supabase, assignments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    class_ids = [str(row.get("class_id")) for row in assignments if row.get("class_id")]
    subject_ids = [str(row.get("subject_id")) for row in assignments if row.get("subject_id")]
    classes_by_id = _fetch_rows_by_ids(supabase, "classes", class_ids)
    subjects_by_id = _fetch_rows_by_ids(supabase, "subjects", subject_ids)

    hydrated: list[dict[str, Any]] = []
    for row in assignments:
        item = dict(row)
        class_id = str(item.get("class_id") or "")
        subject_id = str(item.get("subject_id") or "")
        if class_id and not isinstance(item.get("classes"), dict):
            item["classes"] = classes_by_id.get(class_id, {})
        if subject_id and not isinstance(item.get("subjects"), dict):
            item["subjects"] = subjects_by_id.get(subject_id, {})
        hydrated.append(item)
    return hydrated


def get_teacher_assignments(supabase, teacher_id) -> list[dict[str, Any]]:
    if not supabase or not teacher_id:
        return []

    try:
        response = (
            supabase.table("teacher_assignments")
            .select("*, classes(*), subjects(*)")
            .eq("teacher_id", teacher_id)
            .eq("status", "active")
            .execute()
        )
        return _hydrate_assignments(supabase, response.data or [])
    except Exception:
        try:
            response = (
                supabase.table("teacher_assignments")
                .select("*")
                .eq("teacher_id", teacher_id)
                .eq("status", "active")
                .execute()
            )
            return _hydrate_assignments(supabase, response.data or [])
        except Exception:
            try:
                response = (
                    supabase.table("teacher_assignments")
                    .select("*")
                    .eq("teacher_id", teacher_id)
                    .execute()
                )
                rows = response.data or []
                active_rows = [
                    row
                    for row in rows
                    if str(row.get("status") or "active").strip().lower() == "active"
                ]
                return _hydrate_assignments(supabase, active_rows)
            except Exception:
                return []
