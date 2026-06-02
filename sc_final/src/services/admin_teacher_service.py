from __future__ import annotations

import re
import secrets
import string
import uuid
from typing import Any

from src.database.client import get_supabase_client
from src.services.auth_service import ensure_user_profile_for_existing_auth_user

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TEACHER_SCHEMA_FIX_MESSAGE = (
    "Database schema missing required teacher column. "
    "Run database/fix_teachers_invite_status.sql."
)
TEACHER_INVITE_CODE_SCHEMA_MESSAGE = (
    "Database schema missing teachers.invite_code. "
    "Run database/fix_teacher_invite_code.sql."
)


def _db():
    return get_supabase_client()


def _text(value: Any) -> str:
    return str(value or "").strip()


def _email(value: Any) -> str:
    return _text(value).lower()


def _teacher_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "TCH-" + "".join(secrets.choice(alphabet) for _ in range(8))


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


def _is_missing_teacher_schema_column(error: str) -> bool:
    raw = (error or "").lower()
    if not ("pgrst204" in raw or "schema cache" in raw or "could not find" in raw):
        return False
    if "invite_code" in raw:
        return True
    return any(column in raw for column in ("invite_status", "teacher_code", "updated_at"))


def _teacher_schema_message(error: str) -> str:
    raw = (error or "").lower()
    if "invite_code" in raw:
        return TEACHER_INVITE_CODE_SCHEMA_MESSAGE
    if _is_missing_teacher_schema_column(error):
        return TEACHER_SCHEMA_FIX_MESSAGE
    return ""


def _with_supported_columns(table: str, payload: dict[str, Any]) -> tuple[bool, str]:
    ok, error = _safe_insert(table, payload)
    if ok:
        return True, ""
    if table == "teachers":
        schema_message = _teacher_schema_message(error)
        if schema_message:
            return False, schema_message

    raw = error.lower()
    retry = dict(payload)
    changed = False
    for column in ("phone",):
        if column in retry and column in raw:
            retry.pop(column, None)
            changed = True

    if not changed:
        return False, error
    ok, retry_error = _safe_insert(table, retry)
    if not ok and table == "teachers":
        schema_message = _teacher_schema_message(retry_error)
        if schema_message:
            return False, schema_message
    return ok, retry_error


def ensure_teacher_profile(
    *,
    institute_id: str,
    name: str,
    email: str,
) -> dict[str, Any]:
    return ensure_user_profile_for_existing_auth_user(
        email=email,
        role="teacher",
        institute_id=_text(institute_id),
        status="active",
    )


def add_teacher(
    *,
    institute_id: str,
    name: str,
    email: str,
    phone: str = "",
    teacher_code: str = "",
) -> dict[str, Any]:
    institute_id = _text(institute_id)
    name = _text(name)
    email_norm = _email(email)
    phone = _text(phone)
    teacher_code = _text(teacher_code).upper() or _teacher_code()
    invite_code = _teacher_code()

    if not institute_id:
        return {"ok": False, "message": "Institute session is missing."}
    if not name:
        return {"ok": False, "message": "Teacher name is required."}
    if not EMAIL_RE.match(email_norm):
        return {"ok": False, "message": "Enter a valid teacher email."}

    existing = _first("teachers", institute_id=institute_id, email=email_norm)
    if existing:
        return {"ok": False, "message": "A teacher with this email already exists.", "teacher": existing}

    payload = {
        "id": str(uuid.uuid4()),
        "institute_id": institute_id,
        "name": name,
        "email": email_norm,
        "phone": phone,
        "teacher_code": teacher_code,
        "invite_code": invite_code,
        "invite_status": "pending",
        "status": "active",
    }
    ok, error = _with_supported_columns("teachers", payload)
    if not ok:
        if error in {TEACHER_SCHEMA_FIX_MESSAGE, TEACHER_INVITE_CODE_SCHEMA_MESSAGE}:
            return {"ok": False, "message": error}
        return {"ok": False, "message": "Teacher could not be saved.", "debug": error}

    teacher = _first("teachers", id=payload["id"]) or payload
    profile = ensure_teacher_profile(institute_id=institute_id, name=name, email=email_norm)
    if not profile.get("ok"):
        if profile.get("pending_auth"):
            return {
                "ok": True,
                "teacher": teacher,
                "teacher_code": teacher_code,
                "invite_code": invite_code,
                "login_pending": True,
                "message": (
                    "Teacher saved. Login account pending. Create Supabase Auth user "
                    "or ask teacher to register with the same email."
                ),
            }
        return {
            "ok": False,
            "message": "Teacher saved, but user profile mapping failed.",
            "teacher": teacher,
            "debug": profile.get("debug"),
        }

    return {
        "ok": True,
        "teacher": teacher,
        "profile": profile.get("profile"),
        "teacher_code": teacher_code,
        "invite_code": invite_code,
    }


def list_teachers(institute_id: str) -> list[dict[str, Any]]:
    db = _db()
    if not db or not institute_id:
        return []
    try:
        return (
            db.table("teachers")
            .select("*")
            .eq("institute_id", institute_id)
            .order("created_at", desc=True)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


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


def list_subjects(institute_id: str, class_id: str | None = None) -> list[dict[str, Any]]:
    db = _db()
    if not db or not institute_id:
        return []
    try:
        query = db.table("subjects").select("*").eq("institute_id", institute_id)
        if class_id:
            query = query.eq("class_id", class_id)
        return query.order("created_at", desc=False).execute().data or []
    except Exception:
        return []


def list_teacher_assignments(institute_id: str) -> list[dict[str, Any]]:
    db = _db()
    if not db or not institute_id:
        return []
    try:
        return (
            db.table("teacher_assignments")
            .select("*, teachers(*), classes(*), subjects(*)")
            .eq("institute_id", institute_id)
            .execute()
            .data
            or []
        )
    except Exception:
        try:
            return (
                db.table("teacher_assignments")
                .select("*")
                .eq("institute_id", institute_id)
                .execute()
                .data
                or []
            )
        except Exception:
            return []


def assignment_counts(institute_id: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in list_teacher_assignments(institute_id):
        teacher_id = _text(row.get("teacher_id"))
        if teacher_id:
            counts[teacher_id] = counts.get(teacher_id, 0) + 1
    return counts


def assign_teacher(
    *,
    institute_id: str,
    teacher_id: str,
    class_id: str,
    subject_id: str,
    assignment_type: str,
) -> dict[str, Any]:
    institute_id = _text(institute_id)
    teacher_id = _text(teacher_id)
    class_id = _text(class_id)
    subject_id = _text(subject_id)
    assignment_type = _text(assignment_type) or "subject_teacher"

    if not all([institute_id, teacher_id, class_id, subject_id]):
        return {"ok": False, "message": "Select teacher, class, and subject."}
    if assignment_type not in {"class_teacher", "subject_teacher"}:
        return {"ok": False, "message": "Invalid assignment type."}

    existing = _first(
        "teacher_assignments",
        teacher_id=teacher_id,
        class_id=class_id,
        subject_id=subject_id,
    )
    if existing:
        return {"ok": False, "message": "This teacher is already assigned to that class and subject."}

    payload = {
        "id": str(uuid.uuid4()),
        "institute_id": institute_id,
        "teacher_id": teacher_id,
        "class_id": class_id,
        "subject_id": subject_id,
        "assignment_type": assignment_type,
        "status": "active",
    }
    ok, error = _safe_insert("teacher_assignments", payload)
    if not ok:
        return {"ok": False, "message": "Teacher assignment could not be saved.", "debug": error}

    row = _first("teacher_assignments", id=payload["id"]) or payload
    return {"ok": True, "assignment": row}
