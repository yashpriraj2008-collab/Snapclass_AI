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
    if existing_id:
        try:
            rows = (
                supabase.table("teachers")
                .select("*")
                .eq("id", existing_id)
                .limit(1)
                .execute()
                .data
                or []
            )
            if rows:
                teacher = rows[0]
                st.session_state["teacher_name"] = teacher.get("name")
                st.session_state["teacher_email"] = teacher.get("email")
                st.session_state["institute_id"] = teacher.get("institute_id")
                return teacher
        except Exception:
            pass

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
        st.session_state["institute_id"] = teacher.get("institute_id")
        return teacher
    except Exception as exc:
        if show_error:
            st.error(f"Teacher identity lookup failed: {exc}")
        return None


def get_teacher_by_email(supabase, email: str) -> dict[str, Any] | None:
    if not supabase:
        return None
    email_norm = str(email or "").strip().lower()
    if not email_norm:
        return None
    try:
        rows = supabase.table("teachers").select("*").eq("email", email_norm).limit(1).execute().data or []
        return rows[0] if rows else None
    except Exception:
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


def _active(row: dict[str, Any]) -> bool:
    return str(row.get("status") or "active").strip().lower() in {"", "active"}


def _legacy_teacher_assignments(
    supabase,
    teacher_id: str,
    teacher_email: str = "",
) -> list[dict[str, Any]]:
    """Build assignment rows from legacy subject/class ownership columns."""
    rows: list[dict[str, Any]] = []

    subject_queries = [("teacher_id", teacher_id)]
    if teacher_email:
        subject_queries.append(("teacher_email", teacher_email))
    for column, value in subject_queries:
        try:
            subjects = (
                supabase.table("subjects")
                .select("*")
                .eq(column, value)
                .execute()
                .data
                or []
            )
        except Exception:
            continue
        for subject in subjects:
            class_id = str(subject.get("class_id") or "").strip()
            subject_id = str(subject.get("id") or "").strip()
            if not class_id or not subject_id or not _active(subject):
                continue
            rows.append(
                {
                    "id": f"subject-owner:{subject_id}",
                    "teacher_id": teacher_id,
                    "class_id": class_id,
                    "subject_id": subject_id,
                    "institute_id": subject.get("institute_id"),
                    "assignment_type": "subject_teacher",
                    "status": "active",
                    "subjects": subject,
                }
            )

    try:
        classes = (
            supabase.table("classes")
            .select("*")
            .eq("teacher_id", teacher_id)
            .execute()
            .data
            or []
        )
    except Exception:
        classes = []
    for class_row in classes:
        class_id = str(class_row.get("id") or "").strip()
        if not class_id or not _active(class_row):
            continue
        rows.append(
            {
                "id": f"class-owner:{class_id}",
                "teacher_id": teacher_id,
                "class_id": class_id,
                "subject_id": None,
                "institute_id": class_row.get("institute_id"),
                "assignment_type": "class_teacher",
                "status": "active",
                "classes": class_row,
            }
        )
    return rows


def _merge_assignments(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for group in groups:
        for row in group:
            if not _active(row):
                continue
            key = (
                str(row.get("class_id") or "").strip(),
                str(row.get("subject_id") or "").strip(),
            )
            if not key[0] or key in seen:
                continue
            seen.add(key)
            merged.append(row)
    return merged


def get_teacher_assignments(supabase, teacher_id) -> list[dict[str, Any]]:
    if not supabase or not teacher_id:
        return []

    assignments: list[dict[str, Any]] = []
    try:
        response = (
            supabase.table("teacher_assignments")
            .select("*, classes(*), subjects(*)")
            .eq("teacher_id", teacher_id)
            .eq("status", "active")
            .execute()
        )
        assignments = response.data or []
    except Exception:
        try:
            response = (
                supabase.table("teacher_assignments")
                .select("*")
                .eq("teacher_id", teacher_id)
                .eq("status", "active")
                .execute()
            )
            assignments = response.data or []
        except Exception:
            try:
                response = (
                    supabase.table("teacher_assignments")
                    .select("*")
                    .eq("teacher_id", teacher_id)
                    .execute()
                )
                rows = response.data or []
                assignments = [row for row in rows if _active(row)]
            except Exception:
                assignments = []

    teacher_email = str(st.session_state.get("teacher_email") or "").strip().lower()
    legacy = _legacy_teacher_assignments(
        supabase,
        str(teacher_id),
        teacher_email,
    )
    return _hydrate_assignments(
        supabase,
        _merge_assignments(assignments, legacy),
    )


def validate_teacher_assignment(supabase, *, teacher_id: str, class_id: str, subject_id: str) -> bool:
    if not supabase or not all([teacher_id, class_id, subject_id]):
        return False
    try:
        rows = (
            supabase.table("teacher_assignments")
            .select("id,status")
            .eq("teacher_id", teacher_id)
            .eq("class_id", class_id)
            .eq("subject_id", subject_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if any(_active(row) for row in rows):
            return True
    except Exception:
        pass

    return any(
        str(row.get("class_id") or "") == str(class_id)
        and str(row.get("subject_id") or "") == str(subject_id)
        for row in get_teacher_assignments(supabase, teacher_id)
    )


def get_students_for_teacher_class(supabase, *, teacher_id: str, class_id: str) -> list[dict[str, Any]]:
    if not supabase or not teacher_id or not class_id:
        return []
    assignments = get_teacher_assignments(supabase, teacher_id)
    assignment = next(
        (row for row in assignments if str(row.get("class_id") or "") == str(class_id)),
        None,
    )
    if not assignment:
        return []

    institute_id = str(assignment.get("institute_id") or "")
    class_row = assignment.get("classes") if isinstance(assignment.get("classes"), dict) else {}
    try:
        query = supabase.table("students").select("*").eq("class_id", class_id)
        if institute_id:
            query = query.eq("institute_id", institute_id)
        try:
            rows = query.eq("status", "active").execute().data or []
        except Exception:
            query = supabase.table("students").select("*").eq("class_id", class_id)
            if institute_id:
                query = query.eq("institute_id", institute_id)
            rows = query.execute().data or []
    except Exception:
        rows = []

    students_by_id = {
        str(row.get("id")): row
        for row in rows
        if row.get("id") and str(row.get("status") or "active").strip().lower() in {"", "active"}
    }

    class_name = str(class_row.get("class_name") or class_row.get("name") or "").strip().lower()
    section = str(class_row.get("section") or "").strip().lower()
    if class_name:
        try:
            query = supabase.table("students").select("*")
            if institute_id:
                query = query.eq("institute_id", institute_id)
            legacy_rows = query.execute().data or []
            for row in legacy_rows:
                if row.get("class_id"):
                    continue
                row_class = str(row.get("class_name") or "").strip().lower()
                row_section = str(row.get("section") or "").strip().lower()
                combined_matches = row_class in {
                    class_name,
                    f"{class_name}-{section}".strip("-"),
                    f"{class_name} {section}".strip(),
                }
                if (
                    row.get("id")
                    and combined_matches
                    and row_section in {"", section}
                    and str(row.get("status") or "active").strip().lower() in {"", "active"}
                ):
                    students_by_id.setdefault(str(row["id"]), row)
        except Exception:
            pass

    return list(students_by_id.values())
