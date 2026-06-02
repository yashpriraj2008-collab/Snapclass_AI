import random
import string
from io import BytesIO
from typing import Any, Dict, List, Optional

import qrcode
import streamlit as st


def make_join_code(prefix: str = "SC", length: int = 6) -> str:
    """Join code format: SC- + 6 uppercase alphanumerics."""
    random_part = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )
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


def get_teacher_subjects(supabase, teacher_id: Optional[str]) -> List[Dict[str, Any]]:
    """Return subjects assigned to a teacher via public.teacher_assignments.

    Required mapping:
      - teacher_assignments.teacher_id must match public.teachers.id
      - fetch class from public.classes using class_id
      - fetch subject from public.subjects using subject_id

    Output fields include (best-effort for assignment_type):
      assignment_id, teacher_id, class_id, class_name, section,
      subject_id, subject_name, subject_code, assignment_type
    """
    if not supabase or not teacher_id:
        return []

    # Load assignments first, then hydrate classes/subjects.
    assignments = (
        supabase.table("teacher_assignments")
        .select("id, teacher_id, class_id, subject_id, assignment_type")
        .eq("teacher_id", teacher_id)
        .execute()
    ).data or []

    if not assignments:
        return []

    class_ids = sorted(
        {str(a.get("class_id")) for a in assignments if a.get("class_id")}
    )
    subject_ids = sorted(
        {str(a.get("subject_id")) for a in assignments if a.get("subject_id")}
    )

    classes_by_id: Dict[str, Dict[str, Any]] = {}
    if class_ids:
        classes_rows = (
            supabase.table("classes")
            .select("id, class_name, name, section")
            .in_("id", class_ids)
            .execute()
        ).data or []
        for c in classes_rows:
            classes_by_id[str(c.get("id"))] = c

    subjects_by_id: Dict[str, Dict[str, Any]] = {}
    if subject_ids:
        subject_rows = (
            supabase.table("subjects")
            .select("id, subject_name, name, subject_code, code, class_id")
            .in_("id", subject_ids)
            .execute()
        ).data or []
        for s in subject_rows:
            subjects_by_id[str(s.get("id"))] = s

    out: List[Dict[str, Any]] = []
    for a in assignments:
        class_id = a.get("class_id")
        subject_id = a.get("subject_id")
        c = classes_by_id.get(str(class_id), {})
        s = subjects_by_id.get(str(subject_id), {})

        class_name = c.get("class_name") or c.get("name") or "Class"
        section = c.get("section") or ""
        subject_name = s.get("subject_name") or s.get("name") or "Subject"
        subject_code = s.get("subject_code") or s.get("code") or ""

        out.append(
            {
                "assignment_id": a.get("id"),
                "teacher_id": a.get("teacher_id"),
                "class_id": class_id,
                "class_name": class_name,
                "section": section,
                "subject_id": subject_id,
                "subject_name": subject_name,
                "subject_code": subject_code,
                "assignment_type": a.get("assignment_type") or a.get("status") or "assigned",
            }
        )

    return out


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
    base_url: Optional[str] = None,
):
    """Create or fetch an active join code for a subject.

    Phase 1 expectations:
      - Join code: SC- + 6 uppercase random chars
      - Join link: http://localhost:8507/?join-code=<JOIN_CODE>
    """

    base_url = (base_url or st.secrets.get("APP_PUBLIC_URL", "") or "").strip().rstrip("/")
    if not base_url:
        base_url = "http://localhost:8507"

    # Prefer existing active join code for (subject_id, teacher_id)
    # (If teacher_id is missing, fall back to subject-only lookup).
    try:
        query = (
            supabase.table("subject_join_codes")
            .select("*")
            .eq("subject_id", subject_id)
            .eq("is_active", True)
            .limit(1)
        )
        if teacher_id is not None:
            query = query.eq("teacher_id", teacher_id)

        existing = query.execute().data or []
        if existing:
            row = existing[0]
            join_code = row.get("join_code") or ""
            if not row.get("join_url") and join_code:
                row["join_url"] = f"{base_url}/?join-code={join_code}"
            return row
    except Exception:
        pass

    # Create one.
    for _ in range(8):
        code = make_join_code()
        try:
            # Prevent collisions.
            collision = (
                supabase.table("subject_join_codes")
                .select("id")
                .eq("join_code", code)
                .limit(1)
                .execute()
            ).data
            if collision:
                continue

            join_url = f"{base_url}/?join-code={code}"

            payload: Dict[str, Any] = {
                "subject_id": subject_id,
                "teacher_id": teacher_id,
                "join_code": code,
                "join_url": join_url,
                "is_active": True,
            }
            # If teacher_id is None but schema requires it, insertion will fail and
            # we will keep trying with a new code (or fall through).

            # Insert: NO insert().select().execute()
            supabase.table("subject_join_codes").insert(payload).execute()

            # Re-query separately.
            created = (
                supabase.table("subject_join_codes")
                .select("*")
                .eq("join_code", code)
                .limit(1)
                .execute()
            ).data or []
            if created:
                return created[0]
        except Exception:
            continue

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
