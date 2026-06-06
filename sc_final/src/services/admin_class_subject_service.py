from __future__ import annotations

import uuid
from typing import Any

import streamlit as st

from src.database.client import get_supabase_client


def _db():
    return get_supabase_client()


def _text(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return _text(value).lower()


def _first(table: str, **eq: Any) -> dict[str, Any] | None:
    db = _db()
    if not db:
        return None
    try:
        query = db.table(table).select("*")
        for key, value in eq.items():
            query = query.eq(key, value)
        rows = query.limit(1).execute().data or []
        return rows[0] if rows else None
    except Exception:
        return None


def _safe_insert(table: str, payload: dict[str, Any]) -> tuple[bool, str]:
    db = _db()
    if not db:
        return False, "Supabase is not configured. Add .streamlit/secrets.toml."
    try:
        db.table(table).insert(payload).execute()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _insert_with_supported_columns(table: str, payload: dict[str, Any]) -> tuple[bool, str]:
    ok, error = _safe_insert(table, payload)
    if ok:
        return True, ""

    raw = error.lower()
    retry = dict(payload)
    changed = False
    for column in (
        "teacher_id",
        "class_name",
        "section",
        "name",
        "subject_name",
        "subject_code",
        "code",
        "status",
        "updated_at",
    ):
        if column in retry and column in raw:
            retry.pop(column, None)
            changed = True
    if not changed:
        return False, error
    return _safe_insert(table, retry)


def list_classes(institute_id: str) -> list[dict[str, Any]]:
    db = _db()
    if not db or not institute_id:
        return []
    try:
        return (
            db.table("classes")
            .select("*")
            .eq("institute_id", institute_id)
            .order("created_at", desc=False)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


def list_subjects(institute_id: str) -> list[dict[str, Any]]:
    db = _db()
    if not db or not institute_id:
        return []
    try:
        return (
            db.table("subjects")
            .select("*")
            .eq("institute_id", institute_id)
            .order("created_at", desc=False)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


def list_students(institute_id: str) -> list[dict[str, Any]]:
    db = _db()
    if not db or not institute_id:
        return []
    try:
        return db.table("students").select("*").eq("institute_id", institute_id).execute().data or []
    except Exception:
        return []


def list_teachers(institute_id: str) -> list[dict[str, Any]]:
    db = _db()
    if not db or not institute_id:
        return []
    try:
        return db.table("teachers").select("*").eq("institute_id", institute_id).execute().data or []
    except Exception:
        return []


def add_class(
    *,
    institute_id: str,
    class_name: str,
    section: str,
    academic_year: str,
) -> dict[str, Any]:
    institute_id = _text(institute_id)
    class_name = _text(class_name)
    section = _text(section).upper()
    academic_year = _text(academic_year)

    if not institute_id:
        return {"ok": False, "message": "Institute session is missing."}
    if not class_name:
        return {"ok": False, "message": "Class name is required."}
    if not section:
        return {"ok": False, "message": "Section is required."}
    if not academic_year:
        return {"ok": False, "message": "Academic year is required."}

    for row in list_classes(institute_id):
        if (
            _norm(row.get("class_name") or row.get("name")) == _norm(class_name)
            and _norm(row.get("section")) == _norm(section)
            and _norm(row.get("academic_year")) == _norm(academic_year)
        ):
            return {
                "ok": False,
                "message": f"Class {class_name}-{section} already exists for {academic_year}.",
                "class": row,
            }

    payload = {
        "id": str(uuid.uuid4()),
        "institute_id": institute_id,
        "class_name": class_name,
        "section": section,
        "academic_year": academic_year,
        "status": "active",
    }
    ok, error = _insert_with_supported_columns("classes", payload)
    if not ok:
        return {"ok": False, "message": "Class could not be saved.", "debug": error}
    row = _first("classes", id=payload["id"]) or payload
    st.cache_data.clear()
    return {"ok": True, "class": row}


def add_subject(
    *,
    institute_id: str,
    class_record: dict[str, Any] | None,
    subject_name: str,
    subject_code: str = "",
    teacher_id: str = "",
) -> dict[str, Any]:
    institute_id = _text(institute_id)
    class_record = class_record or {}
    class_id = _text(class_record.get("id"))
    class_name = _text(class_record.get("class_name") or class_record.get("name"))
    section = _text(class_record.get("section"))
    subject_name = _text(subject_name)
    subject_code = _text(subject_code).upper()
    teacher_id = _text(teacher_id)

    if not institute_id:
        return {"ok": False, "message": "Institute session is missing."}
    if not class_id:
        return {"ok": False, "message": "Select a class."}
    if not subject_name:
        return {"ok": False, "message": "Subject name is required."}

    for row in list_subjects(institute_id):
        same_class = _text(row.get("class_id")) == class_id
        same_code = subject_code and _norm(row.get("subject_code") or row.get("code")) == _norm(subject_code)
        same_name = _norm(row.get("subject_name") or row.get("name")) == _norm(subject_name)
        if same_class and (same_code or same_name):
            return {"ok": False, "message": "This subject already exists for the selected class.", "subject": row}

    payload = {
        "id": str(uuid.uuid4()),
        "institute_id": institute_id,
        "class_id": class_id,
        "teacher_id": teacher_id or None,
        "name": subject_name,
        "subject_name": subject_name,
        "code": subject_code,
        "subject_code": subject_code,
        "class_name": class_name,
        "section": section,
        "status": "active",
    }
    ok, error = _insert_with_supported_columns("subjects", payload)
    if not ok:
        return {"ok": False, "message": "Subject could not be saved.", "debug": error}
    row = _first("subjects", id=payload["id"]) or payload
    st.cache_data.clear()
    return {"ok": True, "subject": row}
