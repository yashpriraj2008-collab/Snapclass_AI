from __future__ import annotations

from typing import Any

from src.database.client import get_supabase_client


def save_attendance_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Save attendance rows to Supabase.

    Requirements:
    - Never save locally.
    - Upsert into table("attendance").
    - Conflict target: student_id,class_id,subject_id,attendance_date
    """

    if not records:
        return {"success": False, "saved": 0, "error": ValueError("No records to save."), "data": []}

    supabase = get_supabase_client()
    if not supabase:
        return {"success": False, "saved": 0, "error": ConnectionError("Supabase client unavailable."), "data": []}

    clean_records: list[dict[str, Any]] = []

    for r in records:
        if not isinstance(r, dict):
            continue

        student_id = r.get("student_id")
        class_id = r.get("class_id")
        subject_id = r.get("subject_id")
        attendance_date = r.get("attendance_date")

        if not student_id:
            continue
        if not class_id:
            continue
        if not subject_id:
            continue
        if not attendance_date:
            continue

        clean_records.append(
            {
                "student_id": student_id,
                "class_id": class_id,
                "subject_id": subject_id,
                "attendance_date": str(attendance_date),
                "status": r.get("status", "present"),
                "teacher_id": r.get("teacher_id"),
            }
        )

    if not clean_records:
        return {
            "success": False,
            "saved": 0,
            "error": ValueError("Clean records empty. Missing student_id/class_id/subject_id/date."),
            "data": [],
        }

    try:
        response = (
            supabase.table("attendance")
            .upsert(
                clean_records,
                on_conflict="student_id,class_id,subject_id,attendance_date",
            )
            .execute()
        )

        data = getattr(response, "data", None) or []

        return {
            "success": True,
            "saved": len(data) if data else len(clean_records),
            "error": None,
            "data": data,
        }

    except Exception as e:
        return {"success": False, "saved": 0, "error": e, "data": []}



# Backward-compatible alias for old call sites (if any remain)
def save_attendance(records: list[dict[str, Any]]) -> dict[str, Any]:
    return save_attendance_records(records)
