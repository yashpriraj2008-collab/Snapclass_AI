from __future__ import annotations

import re
import secrets
import string
import uuid
from typing import Any

from src.database.client import get_supabase_client
from src.services.auth_service import ensure_user_profile_for_existing_auth_user

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
STUDENT_PROFILE_MAPPING_ERROR = (
    "Student saved, but login profile could not be created. "
    "Check user_profiles RLS/schema."
)


def _db():
    return get_supabase_client()


def _text(value: Any) -> str:
    return str(value or "").strip()


def _email(value: Any) -> str:
    return _text(value).lower()


def _student_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "STU-" + "".join(secrets.choice(alphabet) for _ in range(8))


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


def _safe_update(table: str, row_id: str, payload: dict[str, Any]) -> tuple[bool, str]:
    db = _db()
    if not db:
        return False, "Supabase is not configured. Add .streamlit/secrets.toml."
    try:
        db.table(table).update(payload).eq("id", row_id).execute()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _safe_update_by_email(table: str, email: str, payload: dict[str, Any]) -> tuple[bool, str]:
    db = _db()
    if not db:
        return False, "Supabase is not configured. Add .streamlit/secrets.toml."
    try:
        db.table(table).update(payload).eq("email", email).execute()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _insert_student_with_supported_columns(payload: dict[str, Any]) -> tuple[bool, str]:
    ok, error = _safe_insert("students", payload)
    if ok:
        return True, ""

    raw = error.lower()
    retry = dict(payload)
    changed = False
    for column in ("class_name", "section", "student_code", "invite_status", "phone", "parent_name", "parent_phone", "status"):
        if column in retry and column in raw:
            retry.pop(column, None)
            changed = True

    if not changed:
        return False, error
    return _safe_insert("students", retry)


def ensure_student_profile(
    *,
    institute_id: str,
    name: str,
    email: str,
    roll_no: str,
    class_name: str,
) -> dict[str, Any]:
    return ensure_user_profile_for_existing_auth_user(
        email=email,
        role="student",
        institute_id=_text(institute_id),
        status="active",
    )


def add_student(
    *,
    institute_id: str,
    name: str,
    email: str,
    roll_no: str,
    class_record: dict[str, Any] | None,
    phone: str = "",
    parent_name: str = "",
    parent_phone: str = "",
) -> dict[str, Any]:
    institute_id = _text(institute_id)
    name = _text(name)
    email_norm = _email(email)
    roll_no = _text(roll_no)
    class_record = class_record or {}
    class_id = _text(class_record.get("id"))
    class_name = _text(class_record.get("class_name") or class_record.get("name"))
    section = _text(class_record.get("section"))

    if not institute_id:
        return {"ok": False, "message": "Institute session is missing."}
    if not name:
        return {"ok": False, "message": "Student name is required."}
    if not roll_no:
        return {"ok": False, "message": "Roll number is required."}
    if not EMAIL_RE.match(email_norm):
        return {"ok": False, "message": "Enter a valid student email."}
    if not class_id:
        return {"ok": False, "message": "Select a class before adding a student."}

    existing_email = _first("students", institute_id=institute_id, email=email_norm)
    if existing_email:
        return {"ok": False, "message": "A student with this email already exists.", "student": existing_email}

    existing_roll = _first("students", institute_id=institute_id, class_id=class_id, roll_no=roll_no)
    if existing_roll:
        return {"ok": False, "message": "This roll number already exists in the selected class.", "student": existing_roll}

    code = _student_code()
    payload = {
        "id": str(uuid.uuid4()),
        "institute_id": institute_id,
        "class_id": class_id,
        "class_name": class_name,
        "section": section,
        "name": name,
        "email": email_norm,
        "roll_no": roll_no,
        "phone": _text(phone),
        "parent_name": _text(parent_name),
        "parent_phone": _text(parent_phone),
        "student_code": code,
        "invite_status": "pending",
        "status": "active",
    }
    ok, error = _insert_student_with_supported_columns(payload)
    if not ok:
        return {"ok": False, "message": "Student could not be saved.", "debug": error}

    student = _first("students", id=payload["id"]) or payload
    profile = ensure_student_profile(
        institute_id=institute_id,
        name=name,
        email=email_norm,
        roll_no=roll_no,
        class_name=f"{class_name}-{section}" if section else class_name,
    )
    if not profile.get("ok"):
        if profile.get("pending_auth"):
            return {
                "ok": True,
                "student": student,
                "student_code": code,
                "login_pending": True,
                "message": (
                    "Student saved. Login account pending. Create Supabase Auth user "
                    "or ask student to register with the same email."
                ),
            }
        return {
            "ok": False,
            "message": STUDENT_PROFILE_MAPPING_ERROR,
            "student": student,
            "debug": profile.get("debug"),
        }

    return {"ok": True, "student": student, "profile": profile.get("profile"), "student_code": code}


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


def list_students(institute_id: str) -> list[dict[str, Any]]:
    db = _db()
    if not db or not institute_id:
        return []
    try:
        return (
            db.table("students")
            .select("*")
            .eq("institute_id", institute_id)
            .order("created_at", desc=True)
            .execute()
            .data
            or []
        )
    except Exception:
        return []
