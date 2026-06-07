from __future__ import annotations

import re
import secrets
import string
import uuid
from typing import Any

import streamlit as st

from src.database.client import get_supabase_client
from src.services.auth_service import ensure_user_profile_for_existing_auth_user

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REQUIRED_STUDENT_COLUMNS = {
    "institute_id",
    "class_id",
    "class_name",
    "section",
    "roll_no",
    "name",
    "email",
    "phone",
    "status",
}
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
    for column in ("student_code", "invite_status", "parent_name", "parent_phone"):
        if column in retry and column in raw:
            retry.pop(column, None)
            changed = True

    if not changed:
        return False, error
    return _safe_insert("students", retry)


def _student_payload(
    *,
    student_id: str,
    institute_id: str,
    class_record: dict[str, Any],
    roll_no: str,
    name: str,
    email: str,
    phone: str,
    parent_name: str,
    parent_phone: str,
    student_code: str,
) -> dict[str, Any]:
    return {
        "id": student_id,
        "institute_id": institute_id,
        "class_id": _text(class_record.get("id")),
        "class_name": _text(class_record.get("class_name") or class_record.get("name")),
        "section": _text(class_record.get("section")),
        "roll_no": roll_no,
        "name": name,
        "email": email,
        "phone": _text(phone),
        "status": "active",
        "parent_name": _text(parent_name),
        "parent_phone": _text(parent_phone),
        "student_code": student_code,
        "invite_status": "pending",
    }


def _required_student_fields_match(student: dict[str, Any], payload: dict[str, Any]) -> bool:
    return all(_text(student.get(column)) == _text(payload.get(column)) for column in REQUIRED_STUDENT_COLUMNS)


def _auto_enroll_student_in_class_active_subjects(db, *, student_id: str | None, class_id: str | None) -> bool:
    """Auto-enroll a newly added student into all active subjects for the given class.

    Avoid duplicate subject_enrollments by checking existence first.
    Returns True if any enrollment was created.
    """
    if not db or not student_id or not class_id:
        return False

    subjects = (
        db.table("subjects")
        .select("*")
        .eq("class_id", class_id)
        .execute()
        .data
        or []
    )
    subjects = [
        subject
        for subject in subjects
        if str(subject.get("status") or "active").strip().lower() in {"", "active"}
        and subject.get("is_active") is not False
    ]
    subject_ids = [str(s.get("id")) for s in subjects if s.get("id")]
    if not subject_ids:
        return False

    created_any = False
    for subject_id in subject_ids:
        existing = (
            db.table("subject_enrollments")
            .select("id")
            .eq("student_id", student_id)
            .eq("subject_id", subject_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if existing:
            continue

        payload = {
            "student_id": student_id,
            "subject_id": subject_id,
            "status": "active",
        }
        try:
            db.table("subject_enrollments").insert(payload).execute()
            created_any = True
        except Exception:
            # Avoid breaking admin add flow if enrollment is blocked by RLS.
            continue

    return created_any



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
    payload = _student_payload(
        student_id=str(uuid.uuid4()),
        institute_id=institute_id,
        class_record=class_record,
        roll_no=roll_no,
        name=name,
        email=email_norm,
        phone=phone,
        parent_name=parent_name,
        parent_phone=parent_phone,
        student_code=code,
    )
    ok, error = _insert_student_with_supported_columns(payload)
    if not ok:
        return {"ok": False, "message": "Student could not be saved.", "debug": error}

    student = _first("students", id=payload["id"]) or payload
    if not _required_student_fields_match(student, payload):
        return {
            "ok": False,
            "message": "Student record is incomplete. Class mapping was not saved.",
            "student": student,
            "debug": {
                "required_fields": sorted(REQUIRED_STUDENT_COLUMNS),
                "saved_student": student,
            },
        }
    profile = ensure_student_profile(
        institute_id=institute_id,
        name=name,
        email=email_norm,
        roll_no=roll_no,
        class_name=f"{class_name}-{section}" if section else class_name,
    )
    if not profile.get("ok"):
        if profile.get("pending_auth"):
            st.cache_data.clear()
            # Even if auth profile is pending, we can still create the subject enrollments.
            # (The student will be enrolled by student_id once created.)
            enroll_ok = False
            try:
                enroll_ok = _auto_enroll_student_in_class_active_subjects(db=_db(), student_id=student.get("id"), class_id=class_id)
            except Exception:
                enroll_ok = False

            return {
                "ok": True,
                "student": student,
                "student_code": code,
                "login_pending": True,
                "subject_enrolled": bool(enroll_ok),
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

    # Auto-enroll the student in all active subjects for that class.
    # This reduces later attendance/visibility confusion.
    subject_enrolled = False
    try:
        subject_enrolled = _auto_enroll_student_in_class_active_subjects(db=_db(), student_id=student.get("id"), class_id=class_id)
    except Exception:
        subject_enrolled = False

    st.cache_data.clear()
    return {
        "ok": True,
        "student": student,
        "profile": profile.get("profile"),
        "student_code": code,
        "subject_enrolled": bool(subject_enrolled),
    }



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
        students = (
            db.table("students")
            .select("*")
            .eq("institute_id", institute_id)
            .order("created_at", desc=True)
            .execute()
            .data
            or []
        )
        try:
            profiles = (
                db.table("user_profiles")
                .select("user_id,email,role,status")
                .eq("institute_id", institute_id)
                .execute()
                .data
                or []
            )
        except Exception:
            profiles = []
        profiles_by_email = {_email(row.get("email")): row for row in profiles if row.get("email")}
        for student in students:
            profile = profiles_by_email.get(_email(student.get("email"))) or {}
            student["role"] = "student"
            student["profile_status"] = profile.get("status")
            student["user_id"] = student.get("user_id") or profile.get("user_id")
        return students
    except Exception:
        return []
