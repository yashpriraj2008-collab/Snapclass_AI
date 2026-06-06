import random
import string
from datetime import datetime, timedelta, timezone
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
    st.cache_data.clear()
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
    regenerate: bool = False,
):
    """Create or fetch an active join code for a subject.

    Phase 1 expectations:
      - Join code: SC- + 6 uppercase random chars
      - Join link: <APP_BASE_URL>/?join-code=<JOIN_CODE>
    """

    base_url = (
        base_url
        or st.secrets.get("APP_BASE_URL", "")
        or st.secrets.get("APP_PUBLIC_URL", "")
        or ""
    ).strip().rstrip("/")
    if not base_url:
        base_url = "http://localhost:8507"

    if regenerate:
        try:
            update_payload = {
                "is_active": False,
                "status": "inactive",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            query = supabase.table("subject_join_codes").update(update_payload).eq("subject_id", subject_id)
            if teacher_id is not None:
                query = query.eq("teacher_id", teacher_id)
            query.execute()
            st.cache_data.clear()
        except Exception:
            try:
                query = supabase.table("subject_join_codes").update({"is_active": False}).eq("subject_id", subject_id)
                if teacher_id is not None:
                    query = query.eq("teacher_id", teacher_id)
                query.execute()
                st.cache_data.clear()
            except Exception:
                pass

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
            if join_code:
                row["join_url"] = f"{base_url}/?join-code={join_code}"
            return row
    except Exception:
        try:
            query = (
                supabase.table("subject_join_codes")
                .select("*")
                .eq("subject_id", subject_id)
                .eq("status", "active")
                .limit(1)
            )
            if teacher_id is not None:
                query = query.eq("teacher_id", teacher_id)
            existing = query.execute().data or []
            if existing:
                row = existing[0]
                join_code = row.get("join_code") or ""
                if join_code:
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
                "status": "active",
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            }
            # If teacher_id is None but schema requires it, insertion will fail and
            # we will keep trying with a new code (or fall through).

            insert_payloads = [
                payload,
                {k: v for k, v in payload.items() if k not in {"status", "expires_at"}},
                {k: v for k, v in payload.items() if k not in {"status", "expires_at", "join_url"}},
            ]
            inserted = False
            for insert_payload in insert_payloads:
                try:
                    supabase.table("subject_join_codes").insert(insert_payload).execute()
                    inserted = True
                    break
                except Exception:
                    continue
            if not inserted:
                continue
            st.cache_data.clear()

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
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def join_subject_with_code_rpc(supabase, *, student_email: str, join_code: str) -> dict[str, Any]:
    if not supabase:
        return {"ok": False, "message": "Supabase is not connected."}
    student_email = str(student_email or "").strip().lower()
    join_code = _clean_code(join_code)
    if not student_email:
        return {"ok": False, "message": "Student email missing. Please login again."}
    if not join_code:
        return {"ok": False, "message": "Please enter the Subject Code shared by your teacher."}

    try:
        response = supabase.rpc(
            "join_subject_with_code",
            {
                "p_student_email": student_email,
                "p_join_code": join_code,
            },
        ).execute()
        data = getattr(response, "data", response)
        if isinstance(data, list):
            data = data[0] if data else {}
        return data if isinstance(data, dict) else {"ok": False, "message": str(data or "Could not join subject.")}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def _fetch_rows_by_ids(supabase, table: str, ids: list) -> List[Dict[str, Any]]:
    clean_ids = sorted({str(row_id) for row_id in ids if row_id})
    if not clean_ids:
        return []
    try:
        return supabase.table(table).select("*").in_("id", clean_ids).execute().data or []
    except Exception:
        rows: List[Dict[str, Any]] = []
        for row_id in clean_ids:
            try:
                rows.extend(supabase.table(table).select("*").eq("id", row_id).execute().data or [])
            except Exception:
                continue
        return rows


def _rows_by_id(rows: list[dict]) -> Dict[str, Dict[str, Any]]:
    return {str(row.get("id")): row for row in rows if row.get("id")}


def _subject_name(row: dict | None) -> str:
    row = row or {}
    return str(row.get("subject_name") or row.get("name") or row.get("subject") or "subject").strip()


def _join_code_candidates(code: str) -> list[str]:
    candidates = [code]
    if code.startswith("SC-"):
        if "O" in code:
            candidates.append(code.replace("O", "0"))
        if "0" in code:
            candidates.append(code.replace("0", "O"))
    return list(dict.fromkeys(candidates))


def enroll_student_with_code(supabase, student_id, join_code: str):
    """Enroll a student for an active subject join code."""
    if not student_id:
        return False, "Student identity missing."

    code = _clean_code(join_code)
    if not code:
        return False, "Please enter the Subject Code shared by your teacher."
    if code.startswith("STU-"):
        return False, "This is a Student Code. Use Subject Code starting with SC-."
    if not supabase:
        return False, "Supabase is not connected."

    try:
        candidates = _join_code_candidates(code)
        code_result = (
            supabase.table("subject_join_codes")
            .select("*")
            .in_("join_code", candidates)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        if not code_result.data:
            try:
                code_result = (
                    supabase.table("subject_join_codes")
                    .select("*")
                    .in_("code", candidates)
                    .eq("is_active", True)
                    .limit(1)
                    .execute()
                )
            except Exception:
                pass

        if not code_result.data:
            return False, "Invalid or inactive subject code."

        code_row = code_result.data[0]
        subject_id = code_row.get("subject_id")
        if not subject_id:
            return False, "Join code is broken: subject_id missing."

        subject_rows = _fetch_rows_by_ids(supabase, "subjects", [subject_id])
        subject_row = subject_rows[0] if subject_rows else {}
        subject_name = _subject_name(subject_row)

        existing = (
            supabase.table("subject_enrollments")
            .select("id")
            .eq("student_id", student_id)
            .eq("subject_id", subject_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return True, f"You are already enrolled in {subject_name}."

        payload = {
            "student_id": student_id,
            "subject_id": subject_id,
            "join_code": code_row.get("join_code") or code_row.get("code") or code,
            "status": "active",
        }

        try:
            supabase.table("subject_enrollments").insert(
                {**payload, "updated_at": datetime.now(timezone.utc).isoformat()}
            ).execute()
        except Exception as exc:
            error_text = str(exc).lower()
            if "row-level security" in error_text or "42501" in error_text:
                return False, "Could not join this subject because database permissions blocked enrollment. Ask admin to check subject_enrollments RLS."
            if "updated_at" not in error_text:
                raise
            try:
                supabase.table("subject_enrollments").insert(payload).execute()
            except Exception as exc2:
                error_text = str(exc2).lower()
                if "row-level security" in error_text or "42501" in error_text:
                    return False, "Could not join this subject because database permissions blocked enrollment. Ask admin to check subject_enrollments RLS."
                raise
        created = (
            supabase.table("subject_enrollments")
            .select("*")
            .eq("student_id", student_id)
            .eq("subject_id", subject_id)
            .limit(1)
            .execute()
        )
        if created.data:
            st.cache_data.clear()
            return True, f"Subject joined successfully: {subject_name}."
        st.cache_data.clear()
        return True, f"Subject joined successfully: {subject_name}."

    except Exception as e:
        return False, str(e)


def get_student_enrolled_subjects(supabase, student_id) -> List[Dict[str, Any]]:
    """Return active enrolled subjects merged with class, teacher, and enrollment data.

    This intentionally avoids Supabase embedded joins because FK names can vary across
    deployments. The page needs a stable Python-merged shape.
    """
    if not supabase or not student_id:
        return []

    try:
        enrollments = (
            supabase.table("subject_enrollments")
            .select("*")
            .eq("student_id", student_id)
            .eq("status", "active")
            .execute()
        )
        enrollment_rows = enrollments.data or []
    except Exception:
        enrollments = (
            supabase.table("subject_enrollments")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )
        enrollment_rows = [
            row for row in (enrollments.data or [])
            if str(row.get("status") or "active").strip().lower() in {"", "active"}
        ]

    subject_ids = [row.get("subject_id") for row in enrollment_rows if row.get("subject_id")]

    if not subject_ids:
        return []

    subject_rows = _fetch_rows_by_ids(supabase, "subjects", subject_ids)
    subjects_by_id = _rows_by_id(subject_rows)
    class_rows = _fetch_rows_by_ids(supabase, "classes", [row.get("class_id") for row in subject_rows])
    teacher_rows = _fetch_rows_by_ids(supabase, "teachers", [row.get("teacher_id") for row in subject_rows])
    classes_by_id = _rows_by_id(class_rows)
    teachers_by_id = _rows_by_id(teacher_rows)

    join_code_rows: list[dict] = []
    try:
        join_code_rows = (
            supabase.table("subject_join_codes")
            .select("*")
            .in_("subject_id", sorted({str(row_id) for row_id in subject_ids if row_id}))
            .eq("is_active", True)
            .execute()
            .data
            or []
        )
    except Exception:
        join_code_rows = []
    join_codes_by_subject: Dict[str, str] = {}
    for code_row in join_code_rows:
        subject_key = str(code_row.get("subject_id") or "")
        join_codes_by_subject.setdefault(subject_key, code_row.get("join_code") or code_row.get("code") or "")

    merged: list[dict] = []
    for enrollment in enrollment_rows:
        subject = subjects_by_id.get(str(enrollment.get("subject_id") or ""))
        if not subject:
            continue
        subject = dict(subject)
        class_row = classes_by_id.get(str(subject.get("class_id") or ""), {})
        teacher_row = teachers_by_id.get(str(subject.get("teacher_id") or ""), {})
        subject_name = subject.get("subject_name") or subject.get("name") or subject.get("subject") or "Subject"
        subject_code = subject.get("subject_code") or subject.get("code") or ""
        class_name = class_row.get("class_name") or class_row.get("name") or class_row.get("grade") or ""
        section = class_row.get("section") or ""
        teacher_name = teacher_row.get("name") or teacher_row.get("full_name") or teacher_row.get("email") or ""
        merged.append(
            {
                **subject,
                "subject_id": str(subject.get("id") or ""),
                "subject_name": subject_name,
                "name": subject_name,
                "subject_code": subject_code,
                "code": subject_code,
                "class": class_row,
                "class_id": subject.get("class_id"),
                "class_name": class_name,
                "section": section,
                "institute_id": subject.get("institute_id"),
                "enrollment_class_id": enrollment.get("class_id"),
                "enrollment_institute_id": enrollment.get("institute_id"),
                "class_label": f"{class_name}-{section}".strip("-") if class_name or section else "",
                "teacher": teacher_row,
                "teacher_id": subject.get("teacher_id"),
                "teacher_name": teacher_name,
                "teacher_email": teacher_row.get("email") or "",
                "enrollment": enrollment,
                "enrollment_status": str(enrollment.get("status") or "active").title(),
                "join_code": enrollment.get("join_code") or join_codes_by_subject.get(str(subject.get("id") or "")) or "",
            }
        )

    return merged


def get_subjects_for_student(supabase, student_id) -> List[Dict[str, Any]]:
    return get_student_enrolled_subjects(supabase, student_id)
