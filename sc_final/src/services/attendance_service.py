from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

import streamlit as st

from src.database.client import get_supabase_client

VALID_STATUSES = {"present", "absent", "late"}
VALID_MODES = {"manual", "faceid", "ai"}
VALID_VERIFICATION_METHODS = {"manual", "faceid", "manual_faceid", "ai"}


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


def _clean_verification_method(value: Any, fallback: str = "manual") -> str:
    method = str(value or fallback or "manual").strip().lower()
    return method if method in VALID_VERIFICATION_METHODS else "manual"


def _date_only(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()

    text = str(value).strip()
    if not text:
        return None

    candidate = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate).date().isoformat()
    except Exception:
        pass

    if len(text) >= 10:
        return text[:10]
    return text


def _unsupported_columns_from_error(error: Exception, payload: dict[str, Any]) -> list[str]:
    raw = str(error).lower()
    return [column for column in payload if column.lower() in raw and "column" in raw]


def _insert_with_supported_columns(supabase, table: str, payload: dict[str, Any]) -> None:
    try:
        supabase.table(table).insert(payload).execute()
        return
    except Exception as exc:
        unsupported = _unsupported_columns_from_error(exc, payload)
        if not unsupported:
            raise

    retry = dict(payload)
    for column in unsupported:
        retry.pop(column, None)
    supabase.table(table).insert(retry).execute()


def _update_with_supported_columns(supabase, table: str, row_id: str, payload: dict[str, Any]) -> None:
    try:
        supabase.table(table).update(payload).eq("id", row_id).execute()
        return
    except Exception as exc:
        unsupported = _unsupported_columns_from_error(exc, payload)
        if not unsupported:
            raise

    retry = dict(payload)
    for column in unsupported:
        retry.pop(column, None)
    supabase.table(table).update(retry).eq("id", row_id).execute()


def _verification_badge_value(value: Any) -> str:
    method = str(value or "manual").strip().lower()
    if method in {"manual_faceid", "manual+faceid", "manual + faceid"}:
        return "manual_faceid"
    if method == "faceid":
        return "faceid"
    return "manual"


def _faceid_verification_payload(confidence: Any = None) -> dict[str, Any]:
    now = datetime.utcnow().isoformat()
    payload: dict[str, Any] = {
        "verification_method": "faceid",
        "attendance_verification": "faceid",
        "faceid_verified_at": now,
        "marked_at": now,
    }
    if confidence is not None:
        payload["confidence"] = confidence
        payload["faceid_confidence"] = confidence
        payload["verification_score"] = confidence
    return payload


def _session_query(supabase, *, class_id: str, subject_id: str, attendance_date: str, mode: str, date_column: str = "attendance_date"):
    return (
        supabase.table("attendance_sessions")
        .select("*")
        .eq("class_id", class_id)
        .eq("subject_id", subject_id)
        .eq(date_column, attendance_date)
        .eq("mode", mode)
    )


def _get_or_create_session(
    supabase,
    *,
    class_id: str,
    subject_id: str,
    attendance_date: str,
    teacher_id: str | None = None,
    institute_id: str | None = None,
    mode: str = "manual",
    created_by: str | None = None,
) -> dict[str, Any]:
    try:
        query = _session_query(
            supabase,
            class_id=class_id,
            subject_id=subject_id,
            attendance_date=attendance_date,
            mode=mode,
        )
        if teacher_id:
            query = query.eq("teacher_id", teacher_id)
        if institute_id:
            query = query.eq("institute_id", institute_id)
        existing = query.limit(1).execute()
    except Exception:
        query = _session_query(
            supabase,
            class_id=class_id,
            subject_id=subject_id,
            attendance_date=attendance_date,
            mode=mode,
            date_column="date",
        )
        if teacher_id:
            query = query.eq("teacher_id", teacher_id)
        if institute_id:
            query = query.eq("institute_id", institute_id)
        existing = query.limit(1).execute()
    if existing.data:
        return existing.data[0]

    payload: dict[str, Any] = {
        "class_id": class_id,
        "subject_id": subject_id,
        "attendance_date": attendance_date,
        "date": attendance_date,
        "mode": mode,
        "status": "completed",
    }
    if teacher_id:
        payload["teacher_id"] = teacher_id
    if institute_id:
        payload["institute_id"] = institute_id
    if created_by:
        payload["created_by"] = created_by

    _insert_with_supported_columns(supabase, "attendance_sessions", payload)

    try:
        created_query = _session_query(
            supabase,
            class_id=class_id,
            subject_id=subject_id,
            attendance_date=attendance_date,
            mode=mode,
        )
        if teacher_id:
            created_query = created_query.eq("teacher_id", teacher_id)
        if institute_id:
            created_query = created_query.eq("institute_id", institute_id)
        created = created_query.limit(1).execute()
    except Exception:
        created_query = _session_query(
            supabase,
            class_id=class_id,
            subject_id=subject_id,
            attendance_date=attendance_date,
            mode=mode,
            date_column="date",
        )
        if teacher_id:
            created_query = created_query.eq("teacher_id", teacher_id)
        if institute_id:
            created_query = created_query.eq("institute_id", institute_id)
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
            created_by=_text(teacher_id),
        )
        return session, None
    except Exception as exc:
        return None, str(exc)


def get_or_create_attendance_session(
    supabase,
    *,
    class_id: str,
    subject_id: str,
    attendance_date: str,
    teacher_id: str | None = None,
    institute_id: str | None = None,
    mode: str = "manual",
) -> dict[str, Any] | None:
    session, error = create_or_get_attendance_session(
        supabase=supabase,
        teacher_id=teacher_id,
        class_id=class_id,
        subject_id=subject_id,
        attendance_date=attendance_date,
        institute_id=institute_id,
        mode=mode,
    )
    if error:
        return None
    return session


def upsert_attendance_record(
    supabase,
    *,
    session_id: str,
    student_id: str,
    status: str,
    marked_by: str | None = None,
    attendance_date: str | None = None,
    class_id: str | None = None,
    subject_id: str | None = None,
    institute_id: str | None = None,
    attendance_verification: str = "manual",
    confidence: Any = None,
) -> dict[str, Any]:
    ok, message, saved_count, errors = _save_records_for_session(
        supabase=supabase,
        session_id=session_id,
        records=[
            {
                "student_id": student_id,
                "status": status,
                "attendance_date": attendance_date,
                "class_id": class_id,
                "subject_id": subject_id,
                "institute_id": institute_id,
                "verification_method": attendance_verification,
                "confidence": confidence,
            }
        ],
        marked_by=marked_by,
        attendance_date=attendance_date,
        default_verification_method=attendance_verification,
        default_confidence=confidence,
    )
    return {"ok": ok, "message": message, "saved_count": saved_count, "errors": errors}


def _save_records_for_session(
    supabase,
    session_id,
    records,
    marked_by,
    attendance_date=None,
    default_verification_method: str = "manual",
    default_confidence: Any = None,
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

        row_date = _date_only((row or {}).get("attendance_date")) or _date_only(attendance_date)
        verification_method = _clean_verification_method(
            (row or {}).get("verification_method") or (row or {}).get("mode"),
            default_verification_method,
        )
        confidence = (row or {}).get("confidence", default_confidence)

        payload = {
            "session_id": str(session_id),
            "student_id": student_id,
            "status": status,
            "marked_by": _text(marked_by),
            "marked_at": datetime.utcnow().isoformat(),
            "verification_method": verification_method,
            "attendance_verification": verification_method,
        }
        if row_date:
            payload["attendance_date"] = row_date
        if confidence is not None:
            payload["confidence"] = confidence
        for optional_column in ("class_id", "subject_id", "institute_id"):
            if (row or {}).get(optional_column):
                payload[optional_column] = _text((row or {}).get(optional_column))

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
                _update_with_supported_columns(supabase, "attendance_records", record_id, payload)
            else:
                _insert_with_supported_columns(supabase, "attendance_records", payload)
            saved_count += 1
        except Exception as exc:
            errors.append(f"Failed for student {student_id}: {exc}")

    success = saved_count > 0
    message = f"Saved {saved_count} attendance records." if success else "No attendance records saved."
    if success:
        st.cache_data.clear()
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
        default_verification_method="manual",
    )


def mark_faceid_attendance(
    supabase,
    *,
    student_id: str,
    class_id: str,
    subject_id: str,
    attendance_date: str,
    teacher_id: str | None = None,
    institute_id: str | None = None,
    confidence: Any = None,
) -> dict[str, Any]:
    """Mark or verify FaceID attendance without duplicating session/student records."""
    if not supabase:
        return {"ok": False, "message": "Supabase client unavailable.", "error": "supabase_missing"}
    if not all([student_id, class_id, subject_id, attendance_date]):
        return {
            "ok": False,
            "message": "Student, class, subject, and date are required.",
            "error": "missing_required_fields",
        }

    try:
        session = _get_or_create_session(
            supabase,
            class_id=str(class_id),
            subject_id=str(subject_id),
            attendance_date=str(attendance_date),
            teacher_id=_text(teacher_id),
            institute_id=_text(institute_id),
            mode="manual",
            created_by=_text(teacher_id),
        )
        session_id = str(session.get("id") or "")
        if not session_id:
            return {"ok": False, "message": "Could not create attendance session.", "error": "session_missing"}

        existing = (
            supabase.table("attendance_records")
            .select("*")
            .eq("session_id", session_id)
            .eq("student_id", str(student_id))
            .limit(1)
            .execute()
            .data
            or []
        )

        if existing:
            current = existing[0]
            next_method = "faceid"
            payload = _faceid_verification_payload(confidence)
            payload.update(
                {
                    "status": "present",
                    "verification_method": next_method,
                    "attendance_verification": next_method,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
            _update_with_supported_columns(supabase, "attendance_records", str(current["id"]), payload)
            st.cache_data.clear()
            return {
                "ok": True,
                "message": "FaceID verified successfully.",
                "session_id": session_id,
                "record_id": current.get("id"),
                "verification_method": next_method,
                "updated_existing": True,
            }

        payload = _faceid_verification_payload(confidence)
        payload.update(
            {
                "session_id": session_id,
                "student_id": str(student_id),
                "status": "present",
                "marked_by": _text(teacher_id),
                "attendance_date": _date_only(attendance_date),
                "class_id": str(class_id),
                "subject_id": str(subject_id),
                "institute_id": _text(institute_id),
            }
        )
        _insert_with_supported_columns(supabase, "attendance_records", payload)
        st.cache_data.clear()
        return {
            "ok": True,
            "message": "FaceID attendance marked successfully.",
            "session_id": session_id,
            "verification_method": "faceid",
            "updated_existing": False,
        }
    except Exception as exc:
        raw = str(exc).lower()
        message = (
            "Database permission blocked FaceID update."
            if "row-level security" in raw or "rls" in raw or "42501" in raw
            else "Attendance could not be saved."
        )
        return {"ok": False, "message": message, "error": str(exc)}


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
            kwargs.get("verification_method", "manual"),
            kwargs.get("confidence"),
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
        attendance_date = _date_only(record.get("attendance_date") or record.get("date"))
        mode = _clean_mode(record.get("mode"))
        verification_method = _clean_verification_method(record.get("verification_method"), mode)
        confidence = record.get("confidence")

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
                "mode": mode,
                "verification_method": verification_method,
                "confidence": confidence,
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
                created_by=first.get("teacher_id"),
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
                    "verification_method": record.get("verification_method"),
                    "confidence": record.get("confidence"),
                }
                for record in group
            ]

            ok, message, saved_count, errors = _save_records_for_session(
                supabase,
                session_id,
                rows,
                first.get("marked_by") or first.get("teacher_id"),
                attendance_date,
                default_verification_method=first.get("verification_method") or mode,
                default_confidence=first.get("confidence"),
            )
            if not ok:
                raise RuntimeError(message)
            saved_rows.extend(rows[:saved_count] if saved_count else rows)
            skipped += len(errors)

        st.cache_data.clear()
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
        session_date = _date_only(
            session.get("attendance_date")
            or session.get("date")
            or session.get("created_at")
            or session.get("marked_at")
        )
        record_date = _date_only(
            item.get("attendance_date")
            or item.get("marked_at")
            or item.get("created_at")
        )
        if session:
            session_values = {
                "attendance_date": session_date,
                "class_id": session.get("class_id"),
                "subject_id": session.get("subject_id"),
                "mode": session.get("mode"),
                "teacher_id": session.get("teacher_id"),
                "session_status": session.get("status"),
                "created_by": session.get("created_by"),
            }
            for key, value in session_values.items():
                if not item.get(key) and value is not None:
                    item[key] = value
        if not item.get("attendance_date"):
            item["attendance_date"] = record_date or session_date
        if "status" in item and item["status"] is not None:
            item["status"] = str(item["status"]).lower()
        if "verification_method" in item and item["verification_method"] is not None:
            item["verification_method"] = str(item["verification_method"]).lower()
        if "attendance_verification" in item and item["attendance_verification"] is not None:
            item["attendance_verification"] = str(item["attendance_verification"]).lower()
        flattened.append(item)
    return flattened


def _filtered_by_date(rows: list[dict[str, Any]], attendance_date: str | None) -> list[dict[str, Any]]:
    if not attendance_date:
        return rows
    target = _date_only(attendance_date)
    if not target:
        return rows
    return [row for row in rows if _date_only(row.get("attendance_date")) == target]


def get_student_attendance_records(supabase, student_id: str) -> list[dict[str, Any]]:
    """Fetch live attendance history for a student_id."""
    if not supabase or not student_id:
        return []

    try:
        response = (
            supabase.table("attendance_records")
            .select("*, attendance_sessions(attendance_date, date, class_id, subject_id, mode, teacher_id, created_by, status, created_at, updated_at)")
            .eq("student_id", student_id)
            .order("marked_at", desc=True)
            .execute()
        )
        rows = response.data or []
        if rows:
            return _flatten_attendance_rows(rows)
    except Exception:
        pass

    try:
        response = (
            supabase.table("attendance_records")
            .select("*")
            .eq("student_id", student_id)
            .order("marked_at", desc=True)
            .execute()
        )
        rows = response.data or []
        session_ids = sorted({row.get("session_id") for row in rows if row.get("session_id")})
        sessions_by_id: dict[str, dict[str, Any]] = {}
        if session_ids:
            sessions = (
                supabase.table("attendance_sessions")
                .select("id,attendance_date,date,class_id,subject_id,mode,teacher_id,created_by,status,created_at,updated_at")
                .in_("id", session_ids)
                .execute()
            )
            sessions_by_id = {str(row.get("id")): row for row in sessions.data or []}

        for row in rows:
            session = sessions_by_id.get(str(row.get("session_id")))
            if session:
                row["attendance_sessions"] = session
        return _flatten_attendance_rows(rows)
    except Exception:
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
        query = supabase.table("attendance_records").select(
            "*, attendance_sessions(attendance_date, date, class_id, subject_id, mode, teacher_id, created_by, status, created_at, updated_at)"
        )
        if class_id:
            query = query.eq("class_id", class_id)
        if subject_id:
            query = query.eq("subject_id", subject_id)
        response = query.order("marked_at", desc=True).execute()
        rows = _flatten_attendance_rows(response.data or [])
        if attendance_date:
            rows = _filtered_by_date(rows, attendance_date)
        return rows
    except Exception:
        return []


def save_attendance(records: list[dict[str, Any]]) -> dict[str, Any]:
    return save_attendance_records(records)
