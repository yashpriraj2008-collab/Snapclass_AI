import random
import string
from io import BytesIO
from typing import Any, Dict, List, Optional


import qrcode


def make_join_code(prefix: str = "SC", length: int = 5) -> str:
    random_part = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )
    # Keep format compatible with examples like CS101 / MATH12A.
    return f"{prefix}-{random_part}"


def create_subject(supabase, payload: Dict[str, Any]):
    """Insert a subject into `subjects`.

    Expected payload keys depend on your DB schema. This function simply
    inserts whatever is provided.
    """
    result = supabase.table("subjects").insert(payload).execute()
    return result.data


def get_teacher_subjects(
    supabase, teacher_id: Optional[str] = None, teacher_email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Return subjects created by a specific teacher."""
    query = supabase.table("subjects").select("*")

    if teacher_id:
        query = query.eq("teacher_id", teacher_id)
    elif teacher_email:
        query = query.eq("teacher_email", teacher_email)

    result = query.execute()
    return result.data or []


def generate_subject_join_code(
    supabase,
    subject_id,
    teacher_id: Optional[str] = None,
    base_url: str = "http://localhost:8507",
):
    """Create a join code row in `subject_join_codes` and return it."""
    code = make_join_code()
    # QR contains the join URL.
    join_url = f"{base_url}?join_code={code}"

    payload = {
        "subject_id": subject_id,
        "teacher_id": teacher_id,
        "join_code": code,
        "join_url": join_url,
        "is_active": True,
    }

    result = supabase.table("subject_join_codes").insert(payload).execute()
    return result.data[0] if result.data else None


def make_qr_image(data: str):
    """Return an in-memory PNG buffer containing the QR."""
    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def enroll_student_with_code(supabase, student_id, join_code: str):
    """Enroll a student for an active subject join code."""
    code_result = (
        supabase.table("subject_join_codes")
        .select("*")
        .eq("join_code", join_code.strip())
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not code_result.data:
        return False, "Invalid or inactive subject code."

    code_row = code_result.data[0]
    subject_id = code_row["subject_id"]

    payload = {
        "student_id": student_id,
        "subject_id": subject_id,
        "join_code": join_code.strip(),
        "status": "active",
    }

    try:
        result = (
            supabase.table("subject_enrollments")
            .upsert(payload, on_conflict="student_id,subject_id")
            .execute()
        )
        return True, result.data
    except Exception as e:
        return False, repr(e)


def get_student_enrolled_subjects(supabase, student_id) -> List[Dict[str, Any]]:
    """Return subjects a student is enrolled in (status=active)."""
    enrollments = (
        supabase.table("subject_enrollments")
        .select("*")
        .eq("student_id", student_id)
        .eq("status", "active")
        .execute()
    )

    rows = enrollments.data or []
    subject_ids = [r["subject_id"] for r in rows if r.get("subject_id")]

    if not subject_ids:
        return []

    subjects = (
        supabase.table("subjects")
        .select("*")
        .in_("id", subject_ids)
        .execute()
    )

    return subjects.data or []

