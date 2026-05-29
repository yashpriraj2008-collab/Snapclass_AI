from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from src.database.client import get_supabase_client

VALID_STATUSES = {"present", "absent", "late"}
VALID_MODES = {"manual", "faceid", "ai"}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_status(value: Any) -> str:
    status = str(value or "present").strip().lower()
    return status if status in VALID_STATUSES else "present"


def _clean_mode(value: Any) -> str:
    mode = str(value or "manual").strip().lower()
    return mode if mode in VALID_MODES else "manual"


def _get_or_create_session(
    supabase,
    *,
    class_id: str,
    subject_id: str,
    attendance_date: str,
    teacher_id: str | None = None,
    institute_id: str | None = None,
    mode: str = "manual",
) -> dict[str, Any]:
    query = (
        supabase.table("attendance_sessions")
        .select("*")
        .eq("class_id", class_id)
        .eq("subject_id", subject_id)
        .eq("date", attendance_date)
        .eq("mode", mode)
    )
    if teacher_id:
        query = query.eq("teacher_id", teacher_id)

    existing = query.limit(1).execute()
    if existing.data:
        return existing.data[0]

    payload: dict[str, Any] = {
        "class_id": class_id,
        "subject_id": subject_id,
        "date": attendance_date,
        "mode": mode,
    }
    if teacher_id:
        payload["teacher_id"] = teacher_id
    if institute_id:
        payload["institute_id"] = institute_id

    supabase.table("attendance_sessions").insert(payload).execute()

    created_query = (
        supabase.table("attendance_sessions")
        .select("*")
        .eq("class_id", class_id)
        .eq("subject_id", subject_id)
        .eq("date", attendance_date)
        .eq("mode", mode)
    )
    if teacher_id:
        created_query = created_query.eq("teacher_id", teacher_id)

    created = created_query.limit(1).execute()
    if not created.data:
        raise RuntimeError("Could not create attendance session.")
    return created.data[0]


def create_or_get_attendance_session(
    supabase,
    teacher_id,
    class_id,
    subject_id,
    attendance_date,
    institute_id=None,
    mode: str = "manual",
):
    """Create or reuse one attendance session for class + subject + date."""
    if not supabase:
        return None, "Supabase client unavailable."
    if not all([class_id, subject_id, attendance_date]):
        return None, "class_id, subject_id, and attendance_date are required."

    try:
        session = _get_or_create_session(
            supabase,
            class_id=str(class_id),
            subject_id=str(subject_id),
            attendance_date=str(attendance_date),
            teacher_id=_text(teacher_id),
            institute_id=_text(institute_id),
            mode=_clean_mode(mode),
        )
        return session, None
    except Exception as exc:
        return None, str(exc)


def _save_records_for_session(
    supabase,
    session_id,
    records,
    marked_by,
    attendance_date=None,
):
    """Save one attendance_records row per student for an existing session."""
    if not session_id:
        return False, "session_id missing", 0, []

    saved_count = 0
    errors = []

    for row in records or []:
        student_id = _text((row or {}).get("student_id"))
        status = str((row or {}).get("status", "")).strip().lower()

        if not student_id:
            errors.append("Missing student_id")
            continue
        if status not in VALID_STATUSES:
            errors.append(f"Invalid status for {student_id}: {status}")
            continue

        payload = {
            "session_id": str(session_id),
            "student_id": student_id,
            "status": status,
            "marked_by": _text(marked_by),
            "marked_at": datetime.utcnow().isoformat(),
        }
        row_date = _text((row or {}).get("attendance_date")) or _text(attendance_date)
        if row_date:
            payload["attendance_date"] = row_date

        try:
            existing = (
                supabase.table("attendance_records")
                .select("id")
                .eq("session_id", str(session_id))
                .eq("student_id", student_id)
                .limit(1)
                .execute()
            )
            if existing.data:
                record_id = existing.data[0]["id"]
                supabase.table("attendance_records").update(payload).eq("id", record_id).execute()
            else:
                supabase.table("attendance_records").insert(payload).execute()
            saved_count += 1
        except Exception as exc:
            errors.append(f"Failed for student {student_id}: {exc}")

    success = saved_count > 0
    message = f"Saved {saved_count} attendance records." if success else "No attendance records saved."
    return success, message, saved_count, errors


def mark_manual_attendance(
    supabase,
    teacher_id,
    class_id,
    subject_id,
    attendance_date,
    records,
    institute_id=None,
):
    session, session_error = create_or_get_attendance_session(
        supabase=supabase,
        teacher_id=teacher_id,
        class_id=class_id,
        subject_id=subject_id,
        attendance_date=attendance_date,
        institute_id=institute_id,
        mode="manual",
    )
    if session_error:
        return False, session_error, 0, []

    return _save_records_for_session(
        supabase=supabase,
        session_id=session["id"],
        records=records,
        marked_by=teacher_id,
        attendance_date=attendance_date,
    )


def save_attendance_records(*args, **kwargs):
    """Save attendance records.

    New MVP call:
      save_attendance_records(supabase, session_id, records, marked_by)

    Backward-compatible call:
      save_attendance_records(records)
    """
    if args and hasattr(args[0], "table"):
        supabase = args[0]
        session_id = args[1] if len(args) > 1 else kwargs.get("session_id")
        records = args[2] if len(args) > 2 else kwargs.get("records")
        marked_by = args[3] if len(args) > 3 else kwargs.get("marked_by")
        ok, message, saved_count, errors = _save_records_for_session(
            supabase,
            session_id,
            records,
            marked_by,
            kwargs.get("attendance_date"),
        )
        return {
            "success": ok,
            "saved": saved_count,
            "error": None if ok else message,
            "message": message,
            "errors": errors,
            "data": [],
            "skipped": len(errors),
        }

    records = args[0] if args else kwargs.get("records", [])
    return _save_attendance_records_legacy(records)


def _save_attendance_records_legacy(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Persist attendance through attendance_sessions + attendance_records."""
    if not records:
        return {"success": False, "saved": 0, "error": "No records to save.", "data": [], "skipped": 0}

    supabase = get_supabase_client()
    if not supabase:
        return {
            "success": False,
            "saved": 0,
            "error": "Supabase client unavailable.",
            "data": [],
            "skipped": 0,
        }

    clean_records: list[dict[str, Any]] = []
    skipped = 0

    for record in records:
        if not isinstance(record, dict):
            skipped += 1
            continue

        student_id = _text(record.get("student_id"))
        class_id = _text(record.get("class_id"))
        subject_id = _text(record.get("subject_id"))
        attendance_date = _text(record.get("attendance_date") or record.get("date"))

        if not all([student_id, class_id, subject_id, attendance_date]):
            skipped += 1
            continue

        clean_records.append(
            {
                "student_id": student_id,
                "class_id": class_id,
                "subject_id": subject_id,
                "attendance_date": attendance_date,
                "status": _clean_status(record.get("status")),
                "marked_by": _text(record.get("marked_by") or record.get("teacher_id")),
                "teacher_id": _text(record.get("teacher_id") or record.get("marked_by")),
                "institute_id": _text(record.get("institute_id")),
                "mode": _clean_mode(record.get("mode")),
            }
        )

    if not clean_records:
        return {
            "success": False,
            "saved": 0,
            "error": "Clean records empty. Missing student_id/class_id/subject_id/date.",
            "data": [],
            "skipped": skipped,
        }

    try:
        grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for record in clean_records:
            grouped[
                (
                    record["class_id"],
                    record["subject_id"],
                    record["attendance_date"],
                    record["mode"],
                )
            ].append(record)

        saved_rows: list[dict[str, Any]] = []

        for (class_id, subject_id, attendance_date, mode), group in grouped.items():
            first = group[0]
            session = _get_or_create_session(
                supabase,
                class_id=class_id,
                subject_id=subject_id,
                attendance_date=attendance_date,
                teacher_id=first.get("teacher_id"),
                institute_id=first.get("institute_id"),
                mode=mode,
            )
            session_id = session.get("id")
            if not session_id:
                raise RuntimeError("attendance_sessions row has no id.")

            rows = [
                {
                    "session_id": session_id,
                    "student_id": record["student_id"],
                    "status": record["status"],
                    "marked_by": record.get("marked_by"),
                    "attendance_date": record["attendance_date"],
                    "class_id": record["class_id"],
                    "subject_id": record["subject_id"],
                }
                for record in group
            ]

            ok, message, saved_count, errors = _save_records_for_session(
                supabase,
                session_id,
                rows,
                first.get("marked_by") or first.get("teacher_id"),
                attendance_date,
            )
            if not ok:
                raise RuntimeError(message)
            saved_rows.extend(rows[:saved_count] if saved_count else rows)
            skipped += len(errors)

        return {
            "success": True,
            "saved": len(saved_rows),
            "error": None,
            "data": saved_rows,
            "skipped": skipped,
        }
    except Exception as exc:
        return {"success": False, "saved": 0, "error": str(exc), "data": [], "skipped": skipped}


def _flatten_attendance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        session = item.pop("attendance_sessions", None) or {}
        if session:
            item.setdefault("attendance_date", session.get("date"))
            item.setdefault("class_id", session.get("class_id"))
            item.setdefault("subject_id", session.get("subject_id"))
            item.setdefault("mode", session.get("mode"))
            item.setdefault("teacher_id", session.get("teacher_id"))
        if "status" in item:
            item["status"] = str(item["status"]).lower()
        flattened.append(item)
    return flattened


def get_student_attendance_records(supabase, student_id: str) -> list[dict[str, Any]]:
    """Fetch live attendance history for a student_id."""
    if not supabase or not student_id:
        return []

    try:
        response = (
            supabase.table("attendance_records")
            .select("*, attendance_sessions(date, class_id, subject_id, mode, teacher_id)")
            .eq("student_id", student_id)
            .order("marked_at", desc=True)
            .execute()
        )
        rows = response.data or []
        if rows:
            return _flatten_attendance_rows(rows)
    except Exception:
        pass

    return []


def get_session_attendance_records(
    supabase,
    *,
    class_id: str | None = None,
    subject_id: str | None = None,
    attendance_date: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch attendance records for a specific session scope."""
    if not supabase:
        return []

    try:
        query = supabase.table("attendance_records").select("*, attendance_sessions(date, class_id, subject_id, mode, teacher_id)")
        if class_id:
            query = query.eq("class_id", class_id)
        if subject_id:
            query = query.eq("subject_id", subject_id)
        if attendance_date:
            query = query.eq("attendance_date", attendance_date)
        response = query.order("marked_at", desc=True).execute()
        return _flatten_attendance_rows(response.data or [])
    except Exception:
        return []


def save_attendance(records: list[dict[str, Any]]) -> dict[str, Any]:
    return save_attendance_records(records)
