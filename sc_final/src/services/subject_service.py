import random
import string
from io import BytesIO
from typing import Any, Dict, List, Optional

import qrcode


def make_join_code(prefix: str = "SC", length: int = 5) -> str:
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}-{random_part}"


def _clean_code(code: str) -> str:
    return (code or "").strip().upper()


def _fetch_subject_after_write(supabase, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    subject_code = payload.get("subject_code") or payload.get("code")
    subject_name = payload.get("subject_name") or payload.get("name")

    try:
        if subject_code:
            rows = (
                supabase.table("subjects")
                .select("*")
                .eq("subject_code", subject_code)
                .limit(1)
                .execute()
                .data
                or []
            )
            if rows:
                return rows
    except Exception:
        pass

    try:
        if subject_name:
            rows = (
                supabase.table("subjects")
                .select("*")
                .eq("subject_name", subject_name)
                .limit(1)
                .execute()
                .data
                or []
            )
            if rows:
                return rows
    except Exception:
        pass

    try:
        if subject_name:
            rows = (
                supabase.table("subjects")
                .select("*")
                .eq("name", subject_name)
                .limit(1)
                .execute()
                .data
                or []
            )
            if rows:
                return rows
    except Exception:
        pass

    return []


def create_subject(supabase, payload: Dict[str, Any]):
    """Insert a subject into subjects and keep old/new column names compatible."""
    clean = dict(payload or {})

    if clean.get("subject_name") and not clean.get("name"):
        clean["name"] = clean["subject_name"]
    if clean.get("name") and not clean.get("subject_name"):
        clean["subject_name"] = clean["name"]

    if clean.get("subject_code") and not clean.get("code"):
        clean["code"] = clean["subject_code"]
    if clean.get("code") and not clean.get("subject_code"):
        clean["subject_code"] = clean["code"]

    supabase.table("subjects").insert(clean).execute()
    return _fetch_subject_after_write(supabase, clean)


def get_teacher_subjects(
    supabase, teacher_id: Optional[str] = None, teacher_email: Optional[str] = None
) -> List[Dict[str, Any]]:
    query = supabase.table("subjects").select("*")

    if teacher_id:
        query = query.eq("teacher_id", teacher_id)
    elif teacher_email:
        # Keep this fallback for older tables if teacher_email exists.
        query = query.eq("teacher_email", teacher_email)

    result = query.execute()
    return result.data or []


def get_subject_by_name(
    supabase,
    subject_name,
    class_name: Optional[str] = None,
    section: Optional[str] = None,
):
    """Fetch one subject by subject_name/name, with optional class/section filters."""
    if not supabase or not subject_name:
        return None

    subject_name = str(subject_name).strip()
    if not subject_name:
        return None

    try:
        query = (
            supabase.table("subjects")
            .select("*")
            .or_(f"subject_name.eq.{subject_name},name.eq.{subject_name}")
            .limit(1)
        )
        if class_name:
            query = query.eq("class_name", str(class_name).strip())
        if section:
            query = query.eq("section", str(section).strip())

        response = query.execute()
        return response.data[0] if response.data else None
    except Exception:
        pass

    for column in ("subject_name", "name"):
        try:
            response = (
                supabase.table("subjects")
                .select("*")
                .eq(column, subject_name)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]
        except Exception:
            continue

    return None


def generate_subject_join_code(
    supabase,
    subject_id,
    teacher_id: Optional[str] = None,
    base_url: str = "http://localhost:8507",
):
    for _ in range(5):
        code = make_join_code()
        existing = (
            supabase.table("subject_join_codes")
            .select("id")
            .eq("join_code", code)
            .limit(1)
            .execute()
        )
        if existing.data:
            continue

        join_url = f"{base_url}?join_code={code}"
        payload = {
            "subject_id": subject_id,
            "teacher_id": teacher_id,
            "join_code": code,
            "join_url": join_url,
            "is_active": True,
        }

        supabase.table("subject_join_codes").insert(payload).execute()
        created = (
            supabase.table("subject_join_codes")
            .select("*")
            .eq("join_code", code)
            .limit(1)
            .execute()
        )
        if created.data:
            return created.data[0]

    return None


def make_qr_image(data: str):
    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def enroll_student_with_code(supabase, student_id, join_code: str):
    """Enroll a student for an active subject join code."""
    if not student_id:
        return False, "Student identity missing."

    code = _clean_code(join_code)
    if not code:
        return False, "Please enter a subject join code."

    try:
        code_result = (
            supabase.table("subject_join_codes")
            .select("*")
            .eq("join_code", code)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )

        if not code_result.data:
            return False, "Invalid or inactive subject code."

        code_row = code_result.data[0]
        subject_id = code_row.get("subject_id")
        if not subject_id:
            return False, "Join code is broken: subject_id missing."

        existing = (
            supabase.table("subject_enrollments")
            .select("id")
            .eq("student_id", student_id)
            .eq("subject_id", subject_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return True, "Already enrolled in this subject."

        payload = {
            "student_id": student_id,
            "subject_id": subject_id,
            "join_code": code,
            "status": "active",
        }

        supabase.table("subject_enrollments").insert(payload).execute()
        created = (
            supabase.table("subject_enrollments")
            .select("*")
            .eq("student_id", student_id)
            .eq("subject_id", subject_id)
            .limit(1)
            .execute()
        )
        return True, created.data or "Subject enrolled successfully."

    except Exception as e:
        return False, str(e)


def get_student_enrolled_subjects(supabase, student_id) -> List[Dict[str, Any]]:
    if not student_id:
        return []

    enrollments = (
        supabase.table("subject_enrollments")
        .select("*")
        .eq("student_id", student_id)
        .eq("status", "active")
        .execute()
    )

    rows = enrollments.data or []
    subject_ids = [r.get("subject_id") for r in rows if r.get("subject_id")]

    if not subject_ids:
        return []

    subjects = supabase.table("subjects").select("*").in_("id", subject_ids).execute()

    subject_rows = subjects.data or []
    for subject in subject_rows:
        if subject.get("subject_name") and not subject.get("name"):
            subject["name"] = subject["subject_name"]
        if subject.get("name") and not subject.get("subject_name"):
            subject["subject_name"] = subject["name"]
        if subject.get("subject_code") and not subject.get("code"):
            subject["code"] = subject["subject_code"]

    return subject_rows
