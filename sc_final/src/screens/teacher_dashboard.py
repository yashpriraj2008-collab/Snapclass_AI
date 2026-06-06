"""Teacher portal — all pages."""
import json
import streamlit as st
import plotly.express as px
from datetime import date
import html
import os
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

# use components via the main streamlit import to avoid import resolution issues
components = st.components.v1


from src.components.sidebar import teacher_sidebar
from src.components.ui import db_status_banner
from src.utils.ui_select import safe_selectbox
from src.utils.session import nav_teacher, check_route_access
from src.utils.perf import time_block

def show_teacher_portal():
    with time_block("auth context load"):
        check_route_access()
    with time_block("sidebar render"):
        teacher_sidebar()
    p = st.session_state.get("teacher_page", "dashboard")
    with time_block(f"current page render: teacher/{p}"):
        if p == "dashboard":
            _dashboard()
        elif p == "manual_att":
            _manual_att()
        elif p == "ai_att":
            _ai_att()
        elif p == "classes":
            _classes()
        elif p == "students":
            _students()
        elif p == "analytics":
            _analytics()
        elif p == "reports":
            _reports()
        elif p == "profile":
            _profile()
        else:
            _dashboard()

def _safe_text(value):
    return "" if value is None else str(value).strip()


def _class_title(class_row):
    class_row = class_row or {}
    name = (
        class_row.get("class_name")
        or class_row.get("name")
        or class_row.get("grade")
        or class_row.get("class")
        or ""
    )
    section = class_row.get("section") or ""
    if name and section:
        return f"{name}-{section}"
    return str(name or "Class")


def _format_class_label(row: dict | None, *, fallback_id: str = "") -> str:
    row = row or {}
    label = _class_title(row)
    if label and label != "Class":
        return label
    return "Class" if not fallback_id else "Class"


def _class_lookup(row: dict | None, classes_by_id: dict[str, dict]) -> dict:
    row = row or {}
    class_id = str(row.get("class_id") or "")
    class_row = dict(classes_by_id.get(class_id, {}) or {})
    if not class_row:
        class_row = {
            "id": class_id,
            "class_name": row.get("class_name") or row.get("class"),
            "name": row.get("class_name") or row.get("class"),
            "section": row.get("section"),
        }
    return class_row


def _get_current_teacher_id():
    return st.session_state.get("teacher_id")


def _get_current_institute_id():
    current = st.session_state.get("current_institute")
    current_id = current.get("id") if isinstance(current, dict) else current
    return (
        st.session_state.get("institute_id")
        or current_id
        or st.session_state.get("current_institute_id")
    )


def _debug_enabled() -> bool:
    if bool(st.session_state.get("debug_mode")):
        return True
    app_env = str(os.getenv("APP_ENV") or "").strip().lower()
    if not app_env:
        secrets_path = Path(__file__).resolve().parents[2] / ".streamlit" / "secrets.toml"
        try:
            if secrets_path.exists():
                with secrets_path.open("rb") as fh:
                    app_env = str(tomllib.load(fh).get("APP_ENV", "")).strip().lower()
        except Exception:
            app_env = ""
    return app_env == "development"


def _demo_data_enabled() -> bool:
    app_env = str(os.getenv("APP_ENV") or "").strip().lower()
    enabled = str(os.getenv("DEMO_DATA_ENABLED") or "").strip().lower()
    if not enabled:
        secrets_path = Path(__file__).resolve().parents[2] / ".streamlit" / "secrets.toml"
        try:
            if secrets_path.exists():
                with secrets_path.open("rb") as fh:
                    secrets_data = tomllib.load(fh)
                enabled = str(secrets_data.get("DEMO_DATA_ENABLED", "")).strip().lower()
                app_env = app_env or str(secrets_data.get("APP_ENV", "")).strip().lower()
        except Exception:
            enabled = ""
    return app_env == "development" and enabled == "true"


def _show_debug(title: str, data: Any) -> None:
    if not _debug_enabled():
        return
    with st.expander(title, expanded=False):
        if isinstance(data, str):
            st.code(data)
        else:
            st.write(data)


def get_current_teacher_context(supabase=None) -> dict[str, Any]:
    """Resolve the logged-in teacher and active assignment scope."""
    if not supabase:
        try:
            from src.database.client import get_supabase_client

            supabase = get_supabase_client()
        except Exception:
            supabase = None

    user_email = (
        st.session_state.get("email")
        or st.session_state.get("user_email")
        or st.session_state.get("teacher_email")
    )
    if not user_email and isinstance(st.session_state.get("user"), dict):
        user_email = st.session_state["user"].get("email")
    user_email = str(user_email or "").strip().lower()

    context: dict[str, Any] = {
        "user_email": user_email,
        "teacher": None,
        "teacher_id": None,
        "institute_id": _get_current_institute_id(),
        "assignments": [],
        "assigned_class_ids": [],
        "assigned_subject_ids": [],
    }
    if not supabase or not user_email:
        st.session_state["teacher_context"] = context
        return context

    try:
        from src.services.teacher_service import get_teacher_assignments, resolve_teacher_identity

        teacher = resolve_teacher_identity(supabase, show_error=False)
        teacher_id = (teacher or {}).get("id")
        raw_assignments = get_teacher_assignments(supabase, teacher_id)
        institute_id = (
            (teacher or {}).get("institute_id")
            or next((row.get("institute_id") for row in raw_assignments if row.get("institute_id")), None)
            or _get_current_institute_id()
        )
        if institute_id:
            st.session_state["institute_id"] = institute_id
        assignments, invalid_assignments = _valid_teacher_assignments(
            raw_assignments,
            institute_id=str(institute_id or ""),
        )
        class_ids = sorted({str(row.get("class_id")) for row in assignments if row.get("class_id")})
        subject_ids = sorted({str(row.get("subject_id")) for row in assignments if row.get("subject_id")})
        context.update(
            {
                "teacher": teacher,
                "teacher_id": teacher_id,
                "institute_id": institute_id,
                "assignments": assignments,
                "assigned_class_ids": class_ids,
                "assigned_subject_ids": subject_ids,
                "invalid_assignments": invalid_assignments,
            }
        )
    except Exception as exc:
        _show_debug("Developer Debug", {"teacher_context_error": str(exc)})

    st.session_state["teacher_context"] = context
    return context


def _class_id(row: dict | None) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get("id") or row.get("class_id") or "").strip()


def _subject_id(row: dict | None) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get("subject_id") or row.get("id") or "").strip()


def _subject_label(subject: dict | None) -> str:
    if not subject:
        return "Select subject"
    name = subject.get("subject_name") or subject.get("name") or subject.get("title") or "Unnamed Subject"
    code = subject.get("subject_code") or subject.get("code") or ""
    return f"{name} ({code})" if code else str(name)


def _subject_label_plain(subject: dict | None) -> str:
    if not subject:
        return "Subject"
    name = subject.get("subject_name") or subject.get("name") or subject.get("title") or "Subject"
    code = subject.get("subject_code") or subject.get("code") or ""
    return f"{name} {code}".strip()


def _assignment_class(row: dict) -> dict:
    class_row = row.get("classes") if isinstance(row.get("classes"), dict) else {}
    class_row = dict(class_row or {})
    if row.get("class_id") and not class_row.get("id"):
        class_row["id"] = row.get("class_id")
    return class_row


def _assignment_subject(row: dict) -> dict | None:
    subject_id = row.get("subject_id")
    if not subject_id:
        return None
    subject = row.get("subjects") if isinstance(row.get("subjects"), dict) else {}
    subject = dict(subject or {})
    subject.setdefault("id", subject_id)
    subject.setdefault("subject_id", subject_id)
    subject.setdefault("class_id", row.get("class_id"))
    return subject


def _valid_teacher_assignments(
    assignments: list[dict],
    *,
    institute_id: str,
) -> tuple[list[dict], list[dict]]:
    valid: list[dict] = []
    rejected: list[dict] = []
    expected_institute = str(institute_id or "")
    for assignment in assignments:
        class_row = _assignment_class(assignment)
        subject_row = _assignment_subject(assignment) or {}
        institute_values = [
            str(value)
            for value in (
                assignment.get("institute_id"),
                class_row.get("institute_id"),
                subject_row.get("institute_id"),
            )
            if value
        ]
        assignment_class_id = str(assignment.get("class_id") or "")
        subject_class_id = str(subject_row.get("class_id") or "")
        assignment_class_keys = _class_section_keys(
            _class_name(class_row),
            _section(class_row),
        )
        subject_class_keys = _class_section_keys(
            subject_row.get("class_name") or subject_row.get("class"),
            subject_row.get("section"),
        )
        same_logical_class = bool(
            assignment_class_keys
            and subject_class_keys
            and assignment_class_keys.intersection(subject_class_keys)
        )
        institute_mismatch = bool(
            expected_institute
            and any(value != expected_institute for value in institute_values)
        )
        class_mismatch = bool(
            assignment_class_id
            and subject_class_id
            and assignment_class_id != subject_class_id
            and not same_logical_class
        )
        if institute_mismatch or class_mismatch:
            rejected.append(assignment)
        else:
            valid.append(assignment)
    return valid, rejected


def _unique_assignment_classes(assignments: list[dict]) -> list[dict]:
    classes: list[dict] = []
    seen: set[tuple[str, str] | tuple[str, str, str]] = set()
    for row in assignments:
        class_row = _assignment_class(row)
        cid = _class_id(class_row) or str(row.get("class_id") or "")
        name = _norm_match(_class_name(class_row))
        section = _norm_match(_section(class_row))
        key: tuple[str, str] | tuple[str, str, str]
        key = ("label", name, section) if name else ("id", cid)
        if not cid or key in seen:
            continue
        seen.add(key)
        classes.append(class_row)
    return classes


def _assignment_matches_class(assignment: dict, class_row: dict) -> bool:
    assignment_class = _assignment_class(assignment)
    assignment_id = _class_id(assignment_class) or str(assignment.get("class_id") or "")
    selected_id = _class_id(class_row)
    if assignment_id and selected_id and assignment_id == selected_id:
        return True
    assignment_name = _norm_match(_class_name(assignment_class))
    selected_name = _norm_match(_class_name(class_row))
    return bool(
        assignment_name
        and selected_name
        and assignment_name == selected_name
        and _norm_match(_section(assignment_class)) == _norm_match(_section(class_row))
    )


def _assignment_subjects_for_class(assignments: list[dict], class_id: str) -> list[dict]:
    selected_class = next(
        (
            _assignment_class(row)
            for row in assignments
            if str(row.get("class_id") or "") == str(class_id)
        ),
        {"id": class_id},
    )
    subjects: list[dict] = []
    seen: set[str] = set()
    for row in assignments:
        if not _assignment_matches_class(row, selected_class):
            continue
        subject = _assignment_subject(row)
        if not subject:
            continue
        sid = _subject_id(subject)
        if sid and sid not in seen:
            seen.add(sid)
            subjects.append(subject)
    return subjects


def _assignments_missing_subject_for_class(assignments: list[dict], class_id: str) -> bool:
    selected_class = next(
        (
            _assignment_class(row)
            for row in assignments
            if str(row.get("class_id") or "") == str(class_id)
        ),
        {"id": class_id},
    )
    return any(
        _assignment_matches_class(row, selected_class) and not row.get("subject_id")
        for row in assignments
    )


def _load_students_for_classes(supabase, institute_id: str, class_ids: list[str]) -> list[dict]:
    if not supabase or not class_ids:
        return []
    try:
        query = supabase.table("students").select("*").in_("class_id", class_ids)
        if institute_id:
            query = query.eq("institute_id", institute_id)
        return [row for row in (query.execute().data or []) if _student_visible_for_teacher(row)]
    except Exception:
        rows: list[dict] = []
        for class_id in class_ids:
            try:
                query = supabase.table("students").select("*").eq("class_id", class_id)
                if institute_id:
                    query = query.eq("institute_id", institute_id)
                rows.extend([row for row in (query.execute().data or []) if _student_visible_for_teacher(row)])
            except Exception:
                continue
        return rows


def _class_name(row: dict | None) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get("class_name") or row.get("name") or row.get("grade") or "").strip()


def _section(row: dict | None) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get("section") or "").strip()


def _norm_match(value: Any) -> str:
    return str(value or "").strip().lower()


def _class_section_keys(class_name: Any, section: Any) -> set[tuple[str, str]]:
    name = _norm_match(class_name)
    sec = _norm_match(section)
    keys: set[tuple[str, str]] = set()
    if name:
        keys.add((name, sec))
        if sec:
            keys.add((f"{name}-{sec}", ""))
            keys.add((f"{name} {sec}", ""))
    return keys


def _student_is_active(row: dict) -> bool:
    if "status" not in row:
        return True
    status = _norm_match(row.get("status"))
    return status in {"", "active"}


def _is_demo_student(row: dict) -> bool:
    email = _norm_match(row.get("email"))
    return email.endswith("@demo.com")


def _student_visible_for_teacher(row: dict) -> bool:
    return _student_is_active(row) and (_demo_data_enabled() or not _is_demo_student(row))


def _load_assigned_students(supabase, institute_id: str, assignments: list[dict]) -> tuple[list[dict], list[dict]]:
    class_rows = _unique_assignment_classes(assignments)
    assignment_class_rows = [_assignment_class(row) for row in assignments]
    class_ids = sorted({
        _class_id(row)
        for row in assignment_class_rows
        if _class_id(row)
    })
    subject_ids = sorted({_subject_id(row) for row in (_assignment_subject(item) for item in assignments) if _subject_id(row)})
    assigned_pairs: set[tuple[str, str]] = set()
    for row in assignment_class_rows:
        assigned_pairs.update(_class_section_keys(_class_name(row), _section(row)))

    students_by_id: dict[str, dict] = {}
    missing_class_id_matches: list[dict] = []
    enrollment_matches: list[dict] = []

    if class_ids:
        try:
            query = supabase.table("students").select("*").in_("class_id", class_ids)
            if institute_id:
                query = query.eq("institute_id", institute_id)
            for row in query.execute().data or []:
                if _student_visible_for_teacher(row):
                    students_by_id[str(row.get("id") or f"class_id:{len(students_by_id)}")] = row
        except Exception as exc:
            _show_debug("Developer Debug", {"students_by_class_id_error": str(exc)})
            for class_id in class_ids:
                try:
                    query = supabase.table("students").select("*").eq("class_id", class_id)
                    if institute_id:
                        query = query.eq("institute_id", institute_id)
                    for row in query.execute().data or []:
                        if _student_visible_for_teacher(row):
                            students_by_id[str(row.get("id") or f"class_id:{class_id}:{len(students_by_id)}")] = row
                except Exception as item_exc:
                    _show_debug("Developer Debug", {"students_single_class_error": str(item_exc), "class_id": class_id})

    if assigned_pairs:
        try:
            query = supabase.table("students").select("*")
            if institute_id:
                query = query.eq("institute_id", institute_id)
            all_students = query.execute().data or []
            for row in all_students:
                if row.get("class_id") or not _student_visible_for_teacher(row):
                    continue
                student_keys = _class_section_keys(row.get("class_name"), row.get("section"))
                if student_keys.intersection(assigned_pairs):
                    key = str(row.get("id") or f"name_section:{len(students_by_id)}")
                    students_by_id.setdefault(key, row)
                    missing_class_id_matches.append(row)
        except Exception as exc:
            _show_debug("Developer Debug", {"students_class_name_section_fallback_error": str(exc)})

    if subject_ids:
        try:
            enrollment_query = (
                supabase.table("subject_enrollments")
                .select("student_id,subject_id,class_id,status")
                .in_("subject_id", subject_ids)
            )
            enrollments = enrollment_query.execute().data or []
        except Exception as exc:
            _show_debug("Developer Debug", {"students_subject_enrollment_error": str(exc)})
            enrollments = []

        enrolled_ids = {
            str(row.get("student_id"))
            for row in enrollments
            if row.get("student_id")
            and str(row.get("status") or "active").strip().lower() in {"", "active"}
            and (
                not row.get("class_id")
                or not class_ids
                or str(row.get("class_id")) in set(class_ids)
            )
        }
        if enrolled_ids:
            try:
                query = supabase.table("students").select("*").in_("id", sorted(enrolled_ids))
                if institute_id:
                    query = query.eq("institute_id", institute_id)
                for row in query.execute().data or []:
                    if _student_visible_for_teacher(row):
                        key = str(row.get("id") or f"subject_enrollment:{len(students_by_id)}")
                        students_by_id.setdefault(key, row)
                        enrollment_matches.append(row)
            except Exception as exc:
                _show_debug("Developer Debug", {"students_by_subject_enrollment_error": str(exc)})

    students = sorted(
        students_by_id.values(),
        key=lambda row: (
            str(row.get("roll_no") or row.get("roll") or row.get("student_code") or ""),
            str(row.get("name") or row.get("full_name") or "").lower(),
        ),
    )
    return students, missing_class_id_matches + enrollment_matches


def _load_students_for_manual_class(
    supabase,
    selected_class: dict,
    institute_id: str = "",
    subject_id: str = "",
) -> tuple[list[dict], list[dict]]:
    selected_class_id = _class_id(selected_class)
    if not supabase or not selected_class_id:
        return [], []

    try:
        query = (
            supabase.table("students")
            .select("*")
            .eq("class_id", selected_class_id)
            .eq("status", "active")
        )
        students = [row for row in (query.execute().data or []) if _student_visible_for_teacher(row)]
    except Exception as exc:
        _show_debug("Developer Debug", {"manual_students_by_class_id_status_error": str(exc)})
        try:
            query = supabase.table("students").select("*").eq("class_id", selected_class_id)
            students = [row for row in query.execute().data or [] if _student_visible_for_teacher(row)]
        except Exception as fallback_exc:
            _show_debug("Developer Debug", {"manual_students_by_class_id_error": str(fallback_exc)})
            students = []

    if students:
        return students, []

    class_name = _class_name(selected_class)
    section = _section(selected_class)
    if not class_name:
        return [], []

    try:
        query = (
            supabase.table("students")
            .select("*")
            .eq("class_name", class_name)
            .eq("section", section)
            .eq("status", "active")
        )
        fallback_students = query.execute().data or []
    except Exception as exc:
        _show_debug("Developer Debug", {"manual_students_by_class_name_section_status_error": str(exc)})
        try:
            query = (
                supabase.table("students")
                .select("*")
                .eq("class_name", class_name)
                .eq("section", section)
            )
            fallback_students = [row for row in query.execute().data or [] if _student_visible_for_teacher(row)]
        except Exception as fallback_exc:
            _show_debug("Developer Debug", {"manual_students_by_class_name_section_error": str(fallback_exc)})
            fallback_students = []

    if not fallback_students and subject_id:
        try:
            enrollments = (
                supabase.table("subject_enrollments")
                .select("student_id,status")
                .eq("subject_id", str(subject_id))
                .execute()
                .data
                or []
            )
            enrolled_ids = sorted({
                str(row.get("student_id"))
                for row in enrollments
                if row.get("student_id")
                and str(row.get("status") or "active").strip().lower() in {"", "active"}
            })
            if enrolled_ids:
                query = supabase.table("students").select("*").in_("id", enrolled_ids)
                if institute_id:
                    query = query.eq("institute_id", institute_id)
                subject_students = [row for row in query.execute().data or [] if _student_visible_for_teacher(row)]
                if subject_students:
                    return subject_students, subject_students
        except Exception as exc:
            _show_debug("Developer Debug", {"manual_students_by_subject_enrollment_error": str(exc)})

    return fallback_students, fallback_students


def _date_value(row: dict | None) -> str:
    if not isinstance(row, dict):
        return ""
    raw = row.get("attendance_date") or row.get("date") or row.get("created_at") or row.get("marked_at")
    if isinstance(raw, date):
        return raw.isoformat()
    text = str(raw or "").strip()
    return text[:10] if len(text) >= 10 else text


def _rows_by_id(rows: list[dict]) -> dict[str, dict]:
    return {str(row.get("id")): row for row in rows if row.get("id")}


def _safe_in_query(supabase, table: str, ids: list[str]) -> list[dict]:
    clean = sorted({str(value) for value in ids if value})
    if not supabase or not clean:
        return []
    try:
        return supabase.table(table).select("*").in_("id", clean).execute().data or []
    except Exception:
        rows: list[dict] = []
        for row_id in clean:
            try:
                rows.extend(supabase.table(table).select("*").eq("id", row_id).execute().data or [])
            except Exception:
                continue
        return rows


def _load_teacher_sessions(supabase, ctx: dict[str, Any]) -> list[dict]:
    teacher_id = ctx.get("teacher_id")
    institute_id = str(ctx.get("institute_id") or "")
    class_ids = set(ctx.get("assigned_class_ids") or [])
    subject_ids = set(ctx.get("assigned_subject_ids") or [])
    if not supabase or not teacher_id or not class_ids:
        return []

    try:
        rows = supabase.table("attendance_sessions").select("*").eq("teacher_id", teacher_id).execute().data or []
    except Exception as exc:
        _show_debug("Developer Debug", {"attendance_sessions_error": str(exc)})
        rows = []

    rows = [
        row
        for row in rows
        if (not institute_id or str(row.get("institute_id") or "") == institute_id)
        and str(row.get("class_id") or "") in class_ids
        and (not subject_ids or str(row.get("subject_id") or "") in subject_ids)
    ]
    if rows:
        return rows

    try:
        all_rows = supabase.table("attendance_sessions").select("*").execute().data or []
    except Exception:
        return []
    return [
        row for row in all_rows
        if (not institute_id or str(row.get("institute_id") or "") == institute_id)
        and str(row.get("class_id") or "") in class_ids
        and (not subject_ids or str(row.get("subject_id") or "") in subject_ids)
    ]


def _load_teacher_attendance_records(supabase, sessions: list[dict], ctx: dict[str, Any]) -> list[dict]:
    session_ids = sorted({str(row.get("id")) for row in sessions if row.get("id")})
    class_ids = set(ctx.get("assigned_class_ids") or [])
    subject_ids = set(ctx.get("assigned_subject_ids") or [])
    if not supabase:
        return []

    if session_ids:
        try:
            rows = supabase.table("attendance_records").select("*").in_("session_id", session_ids).execute().data or []
            if rows:
                return rows
        except Exception as exc:
            _show_debug("Developer Debug", {"attendance_records_by_session_error": str(exc)})

    try:
        rows = supabase.table("attendance_records").select("*").execute().data or []
    except Exception:
        return []
    return [
        row for row in rows
        if (str(row.get("class_id") or "") in class_ids or str(row.get("subject_id") or "") in subject_ids)
    ]


def _live_teacher_data_uncached(supabase=None) -> dict[str, Any]:
    if not supabase:
        from src.database.client import get_supabase_client

        supabase = get_supabase_client()
    with time_block("Supabase queries: teacher context"):
        ctx = get_current_teacher_context(supabase)
    assignments = ctx.get("assignments") or []
    class_rows = _unique_assignment_classes(assignments)
    subjects_by_unique_id: dict[str, dict] = {}
    for subject in (_assignment_subject(row) for row in assignments):
        subject_id = _subject_id(subject)
        if subject and subject_id:
            subjects_by_unique_id.setdefault(subject_id, subject)
    subject_rows = list(subjects_by_unique_id.values())
    with time_block("Supabase queries: teacher students"):
        students, fallback_students = _load_assigned_students(
            supabase,
            str(ctx.get("institute_id") or ""),
            assignments,
        )
    with time_block("Supabase queries: teacher dashboard/reports"):
        sessions = _load_teacher_sessions(supabase, ctx)
        records = _load_teacher_attendance_records(supabase, sessions, ctx)
    classes_by_id = _rows_by_id(class_rows)
    subjects_by_id = _rows_by_id(subject_rows)
    students_by_id = _rows_by_id(students)
    sessions_by_id = _rows_by_id(sessions)
    return {
        "ctx": ctx,
        "classes": class_rows,
        "subjects": subject_rows,
        "students": students,
        "fallback_students": fallback_students,
        "sessions": sessions,
        "records": records,
        "classes_by_id": classes_by_id,
        "subjects_by_id": subjects_by_id,
        "students_by_id": students_by_id,
        "sessions_by_id": sessions_by_id,
    }


@st.cache_data(ttl=30, show_spinner=False)
def _live_teacher_data_cached(email: str, teacher_id: str, role: str, institute_id: str) -> dict[str, Any]:
    return _live_teacher_data_uncached()


def _live_teacher_data(supabase=None) -> dict[str, Any]:
    if supabase:
        return _live_teacher_data_uncached(supabase)
    email = (
        st.session_state.get("email")
        or st.session_state.get("user_email")
        or st.session_state.get("teacher_email")
        or ""
    )
    return _live_teacher_data_cached(
        str(email).strip().lower(),
        str(st.session_state.get("teacher_id") or ""),
        str(st.session_state.get("role") or ""),
        str(_get_current_institute_id() or ""),
    )


def _attendance_percent(records: list[dict]) -> float | None:
    if not records:
        return None
    total = len(records)
    present = sum(1 for row in records if str(row.get("status") or "").strip().lower() == "present")
    return round((present / total) * 100, 1) if total else None


def _current_teacher_email() -> str:
    email = (
        st.session_state.get("email")
        or st.session_state.get("user_email")
        or st.session_state.get("teacher_email")
    )
    for user in (
        st.session_state.get("current_user"),
        st.session_state.get("user"),
    ):
        if email:
            break
        if isinstance(user, dict):
            email = user.get("email")
        elif user is not None:
            email = getattr(user, "email", None)
    return str(email or "").strip().lower()


def _dashboard_teacher_by_email(supabase, email: str) -> dict:
    if not supabase or not email:
        return {}
    try:
        rows = (
            supabase.table("teachers")
            .select("*")
            .ilike("email", email)
            .limit(1)
            .execute()
            .data
            or []
        )
        if rows:
            return rows[0]
    except Exception:
        pass

    try:
        rows = supabase.table("teachers").select("*").execute().data or []
    except Exception:
        return {}
    return next(
        (row for row in rows if _norm_match(row.get("email")) == email),
        {},
    )


def _dashboard_assignments(supabase, teacher_id: str) -> list[dict]:
    if not supabase or not teacher_id:
        return []
    try:
        rows = (
            supabase.table("teacher_assignments")
            .select("*")
            .eq("teacher_id", teacher_id)
            .eq("status", "active")
            .execute()
            .data
            or []
        )
    except Exception:
        try:
            rows = (
                supabase.table("teacher_assignments")
                .select("*")
                .eq("teacher_id", teacher_id)
                .execute()
                .data
                or []
            )
        except Exception:
            return []
        rows = [
            row
            for row in rows
            if "status" not in row or _norm_match(row.get("status")) in {"", "active"}
        ]

    class_ids = sorted({str(row.get("class_id")) for row in rows if row.get("class_id")})
    subject_ids = sorted({str(row.get("subject_id")) for row in rows if row.get("subject_id")})
    classes_by_id = _rows_by_id(_safe_in_query(supabase, "classes", class_ids))
    subjects_by_id = _rows_by_id(_safe_in_query(supabase, "subjects", subject_ids))
    hydrated: list[dict] = []
    for row in rows:
        item = dict(row)
        class_id = str(item.get("class_id") or "")
        subject_id = str(item.get("subject_id") or "")
        item["classes"] = classes_by_id.get(class_id, {})
        item["subjects"] = subjects_by_id.get(subject_id, {})
        hydrated.append(item)
    return hydrated


def _dashboard_students(
    supabase,
    institute_id: str,
    class_ids: list[str],
    assignments: list[dict],
) -> tuple[list[dict], dict[str, Any]]:
    students_by_id: dict[str, dict] = {}
    debug: dict[str, Any] = {
        "direct_class_id_count": 0,
        "class_name_section_fallback_count": 0,
        "errors": [],
    }
    if not supabase or not institute_id or not class_ids:
        return [], debug

    try:
        rows = (
            supabase.table("students")
            .select("*")
            .eq("institute_id", institute_id)
            .in_("class_id", class_ids)
            .execute()
            .data
            or []
        )
        for row in rows:
            key = str(row.get("id") or f"direct:{len(students_by_id)}")
            students_by_id[key] = row
        debug["direct_class_id_count"] = len(rows)
    except Exception as exc:
        debug["errors"].append(f"students class_id query: {exc}")
        for class_id in class_ids:
            try:
                rows = (
                    supabase.table("students")
                    .select("*")
                    .eq("institute_id", institute_id)
                    .eq("class_id", class_id)
                    .execute()
                    .data
                    or []
                )
                for row in rows:
                    key = str(row.get("id") or f"direct:{class_id}:{len(students_by_id)}")
                    students_by_id[key] = row
            except Exception as item_exc:
                debug["errors"].append(f"students class_id {class_id}: {item_exc}")
        debug["direct_class_id_count"] = len(students_by_id)

    assigned_class_keys: set[tuple[str, str]] = set()
    for assignment in assignments:
        class_row = _assignment_class(assignment)
        assigned_class_keys.update(
            _class_section_keys(_class_name(class_row), _section(class_row))
        )

    if assigned_class_keys:
        try:
            institute_students = (
                supabase.table("students")
                .select("*")
                .eq("institute_id", institute_id)
                .execute()
                .data
                or []
            )
            fallback_count = 0
            for row in institute_students:
                if row.get("class_id"):
                    continue
                student_keys = _class_section_keys(
                    row.get("class_name"),
                    row.get("section"),
                )
                if not student_keys.intersection(assigned_class_keys):
                    continue
                key = str(row.get("id") or f"fallback:{len(students_by_id)}")
                if key not in students_by_id:
                    students_by_id[key] = row
                    fallback_count += 1
            debug["class_name_section_fallback_count"] = fallback_count
        except Exception as exc:
            debug["errors"].append(f"students class_name/section fallback: {exc}")

    return list(students_by_id.values()), debug


def _dashboard_sessions(
    supabase,
    class_ids: list[str],
    subject_ids: list[str],
) -> list[dict]:
    if not supabase or not class_ids or not subject_ids:
        return []
    try:
        rows = (
            supabase.table("attendance_sessions")
            .select("*")
            .in_("class_id", class_ids)
            .in_("subject_id", subject_ids)
            .execute()
            .data
            or []
        )
    except Exception:
        try:
            rows = supabase.table("attendance_sessions").select("*").execute().data or []
        except Exception:
            return []

    class_scope = set(class_ids)
    subject_scope = set(subject_ids)
    return [
        row
        for row in rows
        if str(row.get("class_id") or "") in class_scope
        and str(row.get("subject_id") or "") in subject_scope
    ]


def _dashboard_records(supabase, sessions: list[dict]) -> list[dict]:
    session_ids = sorted({str(row.get("id")) for row in sessions if row.get("id")})
    if not supabase or not session_ids:
        return []
    try:
        return (
            supabase.table("attendance_records")
            .select("*")
            .in_("session_id", session_ids)
            .execute()
            .data
            or []
        )
    except Exception:
        records: list[dict] = []
        for session_id in session_ids:
            try:
                records.extend(
                    supabase.table("attendance_records")
                    .select("*")
                    .eq("session_id", session_id)
                    .execute()
                    .data
                    or []
                )
            except Exception:
                continue
        return records


def _load_teacher_dashboard_metrics(supabase) -> dict[str, Any]:
    email = _current_teacher_email()
    teacher = _dashboard_teacher_by_email(supabase, email)
    teacher_id = str(teacher.get("id") or "")
    institute_id = str(teacher.get("institute_id") or "")
    assignments = _dashboard_assignments(supabase, teacher_id)
    class_ids = sorted({str(row.get("class_id")) for row in assignments if row.get("class_id")})
    subject_ids = sorted({str(row.get("subject_id")) for row in assignments if row.get("subject_id")})
    students, student_query_result = _dashboard_students(
        supabase,
        institute_id,
        class_ids,
        assignments,
    )
    sessions = _dashboard_sessions(supabase, class_ids, subject_ids)
    records = _dashboard_records(supabase, sessions)
    classes = [_assignment_class(row) for row in assignments if row.get("class_id")]
    subjects = [_assignment_subject(row) for row in assignments if row.get("subject_id")]
    classes_by_id = _rows_by_id(classes)
    subjects_by_id = _rows_by_id([row for row in subjects if row])

    return {
        "ctx": {
            "user_email": email,
            "teacher": teacher,
            "teacher_id": teacher_id,
            "institute_id": institute_id,
            "assignments": assignments,
            "assigned_class_ids": class_ids,
            "assigned_subject_ids": subject_ids,
        },
        "classes": classes,
        "subjects": [row for row in subjects if row],
        "students": students,
        "sessions": sessions,
        "records": records,
        "classes_by_id": classes_by_id,
        "subjects_by_id": subjects_by_id,
        "sessions_by_id": _rows_by_id(sessions),
        "student_query_result": {
            **student_query_result,
            "total": len(students),
        },
    }


def _render_metric_card(title: str, value: Any, icon: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card teacher-metric-card">
          <div class="icon">{html.escape(str(icon or ""))}</div>
          <h3>{html.escape(str(title))}</h3>
          <div class="value">{html.escape(str(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _email_configured() -> bool:
    try:
        return bool(os.getenv("RESEND_API_KEY") or st.secrets.get("RESEND_API_KEY", ""))
    except Exception:
        return bool(os.getenv("RESEND_API_KEY"))


def _verification_label(value: Any) -> str:
    method = str(value or "manual").strip().lower()
    if method == "manual_faceid":
        return "Manual + FaceID"
    if method == "faceid":
        return "FaceID"
    return "Manual"


def render_empty_state(message: str) -> None:
    st.info(message)


def get_teacher_students(teacher_id: str, data: dict[str, Any] | None = None) -> list[dict]:
    data = data or _live_teacher_data()
    students = []
    for student in data.get("students") or []:
        if _student_visible_for_teacher(student):
            students.append(student)
    return sorted(
        students,
        key=lambda row: (
            str(row.get("roll_no") or row.get("roll") or row.get("student_code") or ""),
            str(row.get("name") or row.get("full_name") or "").lower(),
        ),
    )


def get_teacher_report_records(teacher_id: str, data: dict[str, Any] | None = None) -> list[dict]:
    data = data or _live_teacher_data()
    ctx = data.get("ctx") or {}
    assigned_class_ids = {str(value) for value in ctx.get("assigned_class_ids", []) if value}
    assigned_subject_ids = {str(value) for value in ctx.get("assigned_subject_ids", []) if value}
    rows: list[dict] = []

    for record in data.get("records") or []:
        session_id = str(record.get("session_id") or "")
        session = (data.get("sessions_by_id") or {}).get(session_id, {})
        class_id = str(record.get("class_id") or session.get("class_id") or "")
        subject_id = str(record.get("subject_id") or session.get("subject_id") or "")
        if assigned_class_ids and class_id and class_id not in assigned_class_ids:
            continue
        if assigned_subject_ids and subject_id and subject_id not in assigned_subject_ids:
            continue

        class_row = (data.get("classes_by_id") or {}).get(class_id, {})
        subject_row = (data.get("subjects_by_id") or {}).get(subject_id, {})
        student = (data.get("students_by_id") or {}).get(str(record.get("student_id") or ""), {})
        rows.append(
            {
                "record": record,
                "session": session,
                "student": student,
                "class_id": class_id,
                "subject_id": subject_id,
                "class_name": class_row.get("class_name") or class_row.get("name") or record.get("class_name") or "Class",
                "section": class_row.get("section") or record.get("section") or "",
                "class_label": _format_class_label(class_row or {"class_name": record.get("class_name"), "section": record.get("section")}),
                "subject_name": subject_row.get("subject_name") or subject_row.get("name") or "Subject",
                "subject_code": subject_row.get("subject_code") or subject_row.get("code") or "",
                "attendance_date": _date_value(record) or _date_value(session),
                "student_name": (
                    student.get("name")
                    or student.get("full_name")
                    or record.get("student_name")
                    or record.get("name")
                    or ""
                ),
                "roll_no": (
                    student.get("roll_no")
                    or student.get("roll")
                    or student.get("student_code")
                    or record.get("roll_no")
                    or record.get("roll")
                    or record.get("student_code")
                    or ""
                ),
                "status": str(record.get("status") or "").title() or "Present",
                "verification": _verification_label(
                    record.get("attendance_verification") or record.get("verification_method")
                ),
            }
        )
    return rows


def render_student_card(student: dict) -> None:
    roll = student.get("roll_no") or student.get("roll") or student.get("student_code") or "-"
    st.markdown(
        f"""
        <div class="data-card">
          <b>{html.escape(str(student.get("name") or student.get("full_name") or "Unnamed Student"))}</b><br>
          Roll: {html.escape(str(roll))}<br>
          Email: {html.escape(str(student.get("email") or "-"))}
          <div style="margin-top:8px;color:#6b7280;font-size:.9rem;">
            Class: {html.escape(str(student.get("display_class") or "-"))} |
            Attendance: {html.escape(str(student.get("attendance_text") or "No records"))} |
            Joined Subjects: {html.escape(str(student.get("joined_subjects") or 0))}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_report_record(record: dict) -> None:
    subject = f"{record.get('subject_name', 'Subject')} {record.get('subject_code', '')}".strip()
    class_text = str(record.get("class_label") or "-")
    student_name = str(record.get("student_name") or "Unknown student")
    roll_text = str(record.get("roll_no") or "").strip()
    roll_html = f" | Roll: {html.escape(roll_text)}" if roll_text else ""
    verification = str(record.get("verification") or "Manual")
    st.markdown(
        (
            '<div class="data-card">'
            f"<b>{html.escape(subject)}</b><br>"
            f"Date: {html.escape(str(record.get('attendance_date') or '-'))} | "
            f"Class: {html.escape(class_text)} | "
            f"Status: {html.escape(str(record.get('status') or '-'))}"
            '<div style="margin-top:8px;color:#6b7280;font-size:.9rem;">'
            f"Student: {html.escape(student_name)}{roll_html} | "
            f"Verification: {html.escape(verification)}"
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def _clipboard_button(label: str, value: str, key: str) -> None:
    safe_label = html.escape(label)
    js_value = json.dumps(str(value or ""))
    components.html(
        f"""
        <button id="{html.escape(key)}" style="
            width:100%;border:1px solid #e5e7eb;border-radius:12px;
            padding:10px 12px;background:#ffffff;color:#111827;
            font-weight:700;cursor:pointer;">
            {safe_label}
        </button>
        <script>
        const btn = document.getElementById({json.dumps(key)});
        btn.addEventListener("click", async () => {{
            await navigator.clipboard.writeText({js_value});
            const oldText = btn.innerText;
            btn.innerText = "Copied";
            setTimeout(() => btn.innerText = oldText, 1200);
        }});
        </script>
        """,
        height=48,
    )


def _session_label(row: dict, classes_by_id: dict[str, dict], subjects_by_id: dict[str, dict]) -> dict[str, str]:
    class_row = _class_lookup(row, classes_by_id)
    subject_row = subjects_by_id.get(str(row.get("subject_id") or ""), {})
    return {
        "class": _format_class_label(class_row, fallback_id=str(row.get("class_id") or "")),
        "subject": _subject_label(subject_row) if subject_row else "Subject",
    }


def _load_teacher_classes(supabase):
    if not supabase:
        return []

    from src.services.teacher_service import get_teacher_assignments, resolve_teacher_identity

    teacher = resolve_teacher_identity(supabase, show_error=False)
    teacher_id = (teacher or {}).get("id")
    if not teacher_id:
        return []

    try:
        assignments = get_teacher_assignments(supabase, teacher_id)
        return _unique_assignment_classes(assignments)
    except Exception as e:
        _show_debug("Developer Debug", str(e))

    return []


def _load_subjects_for_class(supabase, class_id):
    from src.services.teacher_service import get_teacher_assignments, resolve_teacher_identity

    try:
        teacher = resolve_teacher_identity(supabase, show_error=False)
        teacher_id = (teacher or {}).get("id")
        assignments = get_teacher_assignments(supabase, teacher_id)
        nested_subjects = [
            row.get("subjects")
            for row in assignments
            if str(row.get("class_id")) == str(class_id) and isinstance(row.get("subjects"), dict)
        ]
        if nested_subjects:
            return nested_subjects

        subject_ids = [
            row.get("subject_id")
            for row in assignments
            if str(row.get("class_id")) == str(class_id) and row.get("subject_id")
        ]
        if not subject_ids:
            return []

        res = (
            supabase.table("subjects")
            .select("*")
            .in_("id", subject_ids)
            .order("created_at", desc=False)
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Could not load subjects: {e}")
        return []


def _add_subject(supabase, class_id, subject_name, subject_code):
    teacher_id = _get_current_teacher_id()
    institute_id = _get_current_institute_id()

    payload = {
        "class_id": class_id,
        "teacher_id": teacher_id,
        "institute_id": institute_id,
        "name": _safe_text(subject_name),
        "code": _safe_text(subject_code),
    }

    try:
        supabase.table("subjects").insert(payload).execute()
        return True, None
    except Exception as e:
        return False, str(e)


def _update_subject(supabase, subject_id, subject_name, subject_code):
    payload = {
        "name": _safe_text(subject_name),
        "code": _safe_text(subject_code),
        "updated_at": "now()",
    }

    try:
        supabase.table("subjects").update(payload).eq("id", subject_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)


def _dashboard():
    from src.database.client import get_supabase_client

    db_status_banner()
    name = (st.session_state.get("user_name", "") or "Teacher").replace(" Demo", "").strip()
    st.markdown(f"<h1>Welcome back, {html.escape(name)}!</h1>", unsafe_allow_html=True)

    st.markdown("<p style='color:#6B7280;margin-top:-8px;'>Teaching overview for today</p>",
                unsafe_allow_html=True)

    try:
        with st.spinner("Loading dashboard..."):
            data = _load_teacher_dashboard_metrics(get_supabase_client())
    except Exception as exc:
        st.error("Teacher dashboard could not be loaded.")
        _show_debug("Developer Debug", str(exc))
        return

    ctx = data["ctx"]
    _show_debug(
        "Developer Debug",
        {
            "current_user.email": ctx.get("user_email"),
            "teacher_id found": ctx.get("teacher_id"),
            "teacher institute_id": ctx.get("institute_id"),
            "assignment count": len(ctx.get("assignments") or []),
            "assigned class_ids": ctx.get("assigned_class_ids") or [],
            "assigned subject_ids": ctx.get("assigned_subject_ids") or [],
            "student count query result": data.get("student_query_result") or {},
        },
    )
    if not ctx.get("teacher_id"):
        st.warning(
            "Teacher profile not found. Ask admin to add this teacher using the same login email."
        )
        return
    if not ctx.get("assignments"):
        st.warning(
            "No classes assigned yet. Ask admin to assign this teacher to a class and subject."
        )
        return

    class_count = len(ctx.get("assigned_class_ids") or [])
    subject_count = len(ctx.get("assigned_subject_ids") or [])
    student_count = len(data["students"])
    avg_att = _attendance_percent(data["records"])
    today = date.today().isoformat()
    todays_sessions = [row for row in data["sessions"] if _date_value(row) == today]

    if avg_att is None:
        st.info("No live attendance records found yet. Start by taking attendance.")

    c1, c2, c3, c4, c5 = st.columns(5, gap="medium")
    for col, label, val, icon in [
        (c1, "Total Classes", class_count, "CL"),
        (c2, "Total Subjects", subject_count, "SB"),
        (c3, "Total Students", student_count, "ST"),
        (c4, "Avg Attendance", f"{avg_att}%" if avg_att is not None else "No data", "%"),
        (c5, "Sessions Today", len(todays_sessions), "TD"),
    ]:
        with col:
            _render_metric_card(label, val, icon)

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1.4, 1], gap="large")
    with col_l:
        st.markdown("#### Weekly Attendance")
        if data["records"]:
            import pandas as pd

            rows = []
            for record in data["records"]:
                session = data["sessions_by_id"].get(str(record.get("session_id") or ""), {})
                rows.append(
                    {
                        "date": _date_value(record) or _date_value(session),
                        "present": 1 if str(record.get("status") or "").lower() == "present" else 0,
                        "total": 1,
                    }
                )
            trend = pd.DataFrame(rows)
            trend = trend[trend["date"].astype(str) != ""]
            if not trend.empty:
                trend = trend.groupby("date", as_index=False).sum()
                trend["rate"] = (trend["present"] / trend["total"] * 100).round(1)
                with time_block("chart rendering: teacher dashboard trend"):
                    fig = px.bar(trend, x="date", y="rate", color_discrete_sequence=["#5B6CFF"])
                    fig.add_hline(y=75, line_dash="dash", line_color="#EF4444")
                    fig.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=0, r=0, t=0, b=0),
                        height=220,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No dated attendance records found yet.")
        else:
            st.info("No live attendance records found yet. Start by taking attendance.")
    with col_r:
        st.markdown("#### Today's Sessions")
        if not todays_sessions:
            st.info("No sessions today.")
        for session in todays_sessions:
            labels = _session_label(session, data["classes_by_id"], data["subjects_by_id"])
            status = str(session.get("status") or "completed").title()
            badge = "ok" if status.lower() == "completed" else "info"
            st.markdown(
                f"""<div class="sc-class-item">
              <div><div style="font-weight:600;font-size:.88rem;">{html.escape(labels["subject"])} - Class {html.escape(labels["class"])}</div>
              <div style="color:#6B7280;font-size:.78rem;">Date: {html.escape(_date_value(session))}</div></div>
              <span class="sc-badge {badge}">{html.escape(status)}</span>
            </div>""",
                unsafe_allow_html=True,
            )

    if _email_configured() and st.button("Send Weekly Report Email", key="send_weekly", use_container_width=False):
        try:
            from src.services.email_service import send_weekly_report

            r = send_weekly_report(
                st.session_state.get("user_email", ""),
                name,
                "All Classes",
                {
                    "total": len(data["records"]),
                    "avg": avg_att or 0,
                    "low": 0,
                },
            )
            st.success("Report sent!") if r.get("ok") else st.warning(r.get("message", ""))
        except:
            st.warning("Email not configured. Add RESEND_API_KEY to secrets.toml")


def _manual_att():
    from src.components.avatar import avatar_html
    from src.services.profile_photo_service import profile_photos_by_email

    st.markdown(
        """
        <style>
        .manual-attendance-hero {
          background:linear-gradient(135deg,#312E81 0%,#4F46E5 55%,#7C3AED 100%);
          border-radius:22px;padding:25px 28px;margin:2px 0 20px;
          box-shadow:0 18px 42px rgba(79,70,229,.17);
        }
        .manual-attendance-hero h2 {color:#fff!important;margin:0 0 6px;font-size:1.7rem;}
        .manual-attendance-hero p {color:#E0E7FF!important;margin:0;font-size:.92rem;}
        .manual-attendance-heading {
          color:#0F172A!important;font-size:1.02rem;font-weight:850;margin:18px 0 5px;
        }
        .manual-attendance-copy {color:#64748B!important;font-size:.84rem;margin-bottom:12px;}
        .manual-attendance-context {
          background:#F8FAFC;border:1px solid #E2E8F0;border-radius:16px;
          padding:14px 17px;margin:14px 0;color:#334155!important;
        }
        .manual-student-card {
          background:#fff;border:1px solid #E2E8F0;border-radius:15px;
          padding:13px 16px;margin:8px 0;box-shadow:0 4px 14px rgba(15,23,42,.04);
        }
        .manual-student-name {font-weight:850;color:#0F172A!important;font-size:.96rem;}
        .manual-student-meta {color:#64748B!important;font-size:.79rem;margin-top:3px;}
        .manual-empty-roster {
          background:#F8FAFC;border:1px dashed #CBD5E1;border-radius:16px;
          padding:28px 20px;text-align:center;color:#64748B!important;margin:10px 0 16px;
        }
        div[data-baseweb="select"] * {color:#111827!important;}
        div[data-baseweb="select"] input {color:#111827!important;}
        div[data-baseweb="popover"] * {color:#111827!important;background-color:#fff!important;}
        .stSelectbox label,.stDateInput label {color:#334155!important;font-weight:700!important;}
        @media (max-width:640px) {
          .manual-attendance-hero {padding:21px 19px;border-radius:18px;}
          .manual-attendance-hero h2 {font-size:1.45rem;}
        }
        </style>
        <div class="manual-attendance-hero">
          <h2>Manual Attendance</h2>
          <p>Select the class context, review the complete roster, and save attendance from one screen.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    from src.database.client import get_supabase_client
    from src.services.attendance_service import mark_manual_attendance
    from src.services.teacher_service import get_teacher_assignments, resolve_teacher_identity

    supabase = get_supabase_client()
    if not supabase:
        st.error("Supabase is not connected.")
        return

    teacher = resolve_teacher_identity(supabase, show_error=False)
    if not teacher:
        st.warning("Please login first.")
        st.stop()

    teacher_id = teacher["id"]

    assignments = get_teacher_assignments(supabase, teacher_id)
    if not assignments:
        st.info("No classes assigned to you yet.")
        return

    classes = _unique_assignment_classes(assignments)
    if not classes:
        st.info("No classes assigned to you yet.")
        return

    institute_id = str(_get_current_institute_id() or teacher.get("institute_id") or "")

    def class_label(c: dict | None) -> str:
        if not c:
            return "Class"
        name = c.get("class_name") or c.get("name") or c.get("grade") or ""
        section = c.get("section") or ""
        out = f"{name}-{section}".strip("-")
        return f"Class {out}" if out else "Class"

    # Use IDs directly for labels in the requested format.
    def subject_label(s: dict | None) -> str:
        if not s:
            return "Subject"
        name = s.get("subject_name") or s.get("name") or s.get("title") or ""
        code = s.get("subject_code") or s.get("code") or ""
        if name and code:
            return f"{name} ({code})"
        return name or "Subject"

    @st.cache_data(ttl=30, show_spinner=False)
    def _get_students_for_selected_class(selected_class_id: str, selected_subject_id: str) -> list[dict]:
        selected_class_row = next((c for c in classes if _class_id(c) == selected_class_id), None) or {
            "id": selected_class_id,
            "class_id": selected_class_id,
        }
        class_students, _fallback_students = _load_students_for_manual_class(
            supabase,
            selected_class_row,
            institute_id,
            selected_subject_id,
        )
        return class_students

    @st.cache_data(ttl=30, show_spinner=False)
    def _get_subjects_for_selected_class(selected_class_id: str) -> list[dict]:
        return _assignment_subjects_for_class(assignments, selected_class_id)

    st.markdown('<div class="manual-attendance-heading">Attendance setup</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="manual-attendance-copy">The first assigned class and subject are ready automatically. Change any field to refresh the roster.</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("manual_attendance_class_selectbox") not in classes:
        st.session_state.pop("manual_attendance_class_selectbox", None)

    setup_date, setup_class, setup_subject = st.columns([0.85, 1.15, 1.25], gap="medium")
    with setup_date:
        selected_date = st.date_input(
            "Attendance date",
            value=date.today(),
            key="manual_attendance_date_picker",
        )
    with setup_class:
        selected_class = st.selectbox(
            "Class",
            classes,
            key="manual_attendance_class_selectbox",
            format_func=class_label,
        )
    selected_class_id = _class_id(selected_class) if selected_class else ""

    subjects: list[dict] = []
    if selected_class_id:
        try:
            subjects = _get_subjects_for_selected_class(selected_class_id)
        except Exception as exc:
            _show_debug("Developer Debug", {"manual_subjects_error": str(exc)})
            subjects = []

    if st.session_state.get("manual_attendance_subject_selectbox") not in subjects:
        st.session_state.pop("manual_attendance_subject_selectbox", None)

    with setup_subject:
        if subjects:
            selected_subject = st.selectbox(
                "Subject",
                subjects,
                key="manual_attendance_subject_selectbox",
                format_func=subject_label,
            )
        else:
            st.selectbox(
                "Subject",
                ["No assigned subjects"],
                key="manual_attendance_subject_empty",
                disabled=True,
            )
            selected_subject = None

    selected_subject_id = _subject_id(selected_subject) if selected_subject else ""
    attendance_date_str = selected_date.strftime("%Y-%m-%d") if selected_date else ""
    selection_ready = bool(selected_class_id and selected_subject_id and attendance_date_str)
    selection_key = (
        f"{selected_class_id}:{selected_subject_id}:{attendance_date_str}"
        if selection_ready
        else "manual-attendance-unavailable"
    )

    selected_class_row = next((c for c in classes if _class_id(c) == selected_class_id), None)
    class_name = class_label(selected_class_row)
    subject_name = subject_label(selected_subject)
    context_text = (
        f"{subject_name} | {class_name} | {attendance_date_str}"
        if selection_ready
        else "Select a class with an assigned subject to prepare attendance."
    )
    st.markdown(
        f'<div class="manual-attendance-context"><strong>Current session:</strong> {html.escape(context_text)}</div>',
        unsafe_allow_html=True,
    )

    class_students: list[dict] = []
    roster_error = ""
    if selection_ready:
        try:
            class_students = _get_students_for_selected_class(selected_class_id, selected_subject_id)
        except Exception as exc:
            roster_error = "Could not load students. Check the class and subject mapping."
            _show_debug("Developer Debug", {"manual_students_error": str(exc)})
    roster_photo_by_email = profile_photos_by_email(
        supabase,
        [str(student.get("email") or "") for student in class_students],
    )

    st.markdown('<div class="manual-attendance-heading">Student roster</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="manual-attendance-copy">Everyone defaults to Present. Use bulk actions or update individual students.</div>',
        unsafe_allow_html=True,
    )

    statuses_by_selection = st.session_state.setdefault("manual_attendance_statuses_by_selection", {})
    attendance_statuses = statuses_by_selection.setdefault(selection_key, {})
    status_options = ["present", "absent", "late"]
    student_ids = [str(student.get("id") or "") for student in class_students if student.get("id")]
    for student_id in student_ids:
        if attendance_statuses.get(student_id) not in status_options:
            attendance_statuses[student_id] = "present"

    bulk1, bulk2, bulk3, bulk4 = st.columns([1, 1, 1, 1.2], gap="small")
    bulk_disabled = not bool(student_ids)
    if bulk1.button(
        "All Present",
        use_container_width=True,
        disabled=bulk_disabled,
        key=f"manual_all_present_{selection_key}",
    ):
        for student_id in student_ids:
            attendance_statuses[student_id] = "present"
            st.session_state[f"manual_status_{selection_key}_{student_id}"] = "present"
        st.rerun()
    if bulk2.button(
        "All Absent",
        use_container_width=True,
        disabled=bulk_disabled,
        key=f"manual_all_absent_{selection_key}",
    ):
        for student_id in student_ids:
            attendance_statuses[student_id] = "absent"
            st.session_state[f"manual_status_{selection_key}_{student_id}"] = "absent"
        st.rerun()
    if bulk3.button(
        "All Late",
        use_container_width=True,
        disabled=bulk_disabled,
        key=f"manual_all_late_{selection_key}",
    ):
        for student_id in student_ids:
            attendance_statuses[student_id] = "late"
            st.session_state[f"manual_status_{selection_key}_{student_id}"] = "late"
        st.rerun()
    if bulk4.button(
        "Refresh Roster",
        use_container_width=True,
        disabled=not selection_ready,
        key=f"manual_refresh_{selection_key}",
    ):
        st.cache_data.clear()
        st.rerun()

    attendance_records: list[dict] = []
    if roster_error:
        st.error(roster_error)
    elif not selection_ready:
        st.markdown(
            '<div class="manual-empty-roster">No subject is available for the selected class. Ask the institute admin to assign one.</div>',
            unsafe_allow_html=True,
        )
    elif not class_students:
        st.markdown(
            '<div class="manual-empty-roster">No students are linked to this class or subject yet.</div>',
            unsafe_allow_html=True,
        )
    else:
        for student in class_students:
            student_id = str(student.get("id") or "")
            if not student_id:
                continue
            roll = student.get("roll_no") or student.get("roll") or student.get("student_code") or "-"
            name = student.get("name") or student.get("full_name") or "Unnamed student"
            photo_url = (
                student.get("profile_photo_url")
                or roster_photo_by_email.get(str(student.get("email") or "").strip().lower(), "")
            )
            student_avatar = avatar_html(
                {"name": name, "profile_photo_url": photo_url},
                size=46,
            )
            student_col, status_col = st.columns([1.55, 1], gap="medium")
            with student_col:
                st.markdown(
                    f"""
                    <div class="manual-student-card" style="display:flex;align-items:center;gap:12px;">
                      {student_avatar}
                      <div>
                        <div class="manual-student-name">{html.escape(str(name))}</div>
                        <div class="manual-student-meta">Roll / Code: {html.escape(str(roll))}</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            radio_key = f"manual_status_{selection_key}_{student_id}"
            if st.session_state.get(radio_key) not in status_options:
                st.session_state[radio_key] = attendance_statuses.get(student_id, "present")
            with status_col:
                selected_status = st.radio(
                    f"Attendance status for {name}",
                    status_options,
                    horizontal=True,
                    key=radio_key,
                    label_visibility="collapsed",
                )
            attendance_statuses[student_id] = str(selected_status)
            attendance_records.append({"student_id": student_id, "status": str(selected_status)})

    present_count = sum(1 for record in attendance_records if record["status"] == "present")
    absent_count = sum(1 for record in attendance_records if record["status"] == "absent")
    late_count = sum(1 for record in attendance_records if record["status"] == "late")

    st.markdown('<div class="manual-attendance-heading">Attendance summary</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    c1.metric("Total Students", len(attendance_records))
    c2.metric("Present", present_count)
    c3.metric("Absent", absent_count)
    c4.metric("Late", late_count)

    st.markdown('<div class="manual-attendance-heading">Save attendance</div>', unsafe_allow_html=True)
    save_disabled = not bool(selection_ready and attendance_records)
    if st.button(
        "Save Attendance",
        type="primary",
        use_container_width=True,
        disabled=save_disabled,
        key=f"manual_save_{selection_key}",
    ):
        try:
            ok, message, saved_count, errors = mark_manual_attendance(
                supabase=supabase,
                teacher_id=teacher_id,
                class_id=selected_class_id,
                subject_id=selected_subject_id,
                attendance_date=attendance_date_str,
                institute_id=institute_id,
                records=attendance_records,
            )
            if ok:
                st.cache_data.clear()
                st.success(f"{saved_count} attendance records saved successfully.")
                if errors:
                    st.warning(f"{len(errors)} row(s) skipped: {', '.join(errors[:3])}")
            else:
                st.error(f"Attendance not saved: {message}")
                if errors:
                    st.caption("; ".join(errors[:5]))
        except Exception as exc:
            st.error("Attendance could not be saved. Please retry or contact support.")
            _show_debug("Developer Debug", {"manual_attendance_save_error": str(exc)})



def _ai_att():
    db_status_banner()
    st.markdown("### 🤖 AI Attendance")
    st.info("AI Attendance — upload a class photo or use live camera to match enrolled students.")

    # Prefer teacher assignment scope; do not populate synthetic class/subject options.
    try:
        from src.database.client import get_supabase_client
        from src.services.teacher_service import get_teacher_assignments, resolve_teacher_identity

        supabase = get_supabase_client()
        teacher = resolve_teacher_identity(supabase, show_error=False) if supabase else None
        assignments = get_teacher_assignments(supabase, (teacher or {}).get("id")) if teacher else []
        classes = _unique_assignment_classes(assignments)
    except Exception:
        supabase = None
        classes = []
        assignments = []

    if not classes:
        st.info("No assigned classes found for this teacher.")
        return

    def class_label(c: dict | None) -> str:
        if not c:
            return "Choose class"
        name = c.get("class_name") or c.get("name") or c.get("grade") or ""
        section = c.get("section") or ""
        out = f"{name}-{section}".strip("-")
        return out if out else "Class"

    def subject_label(s: dict | None) -> str:
        if not s:
            return "Choose subject"
        return _subject_label_plain(s)

    # Always render the full UI at once (Streamlit reruns on every interaction).
    # Validate only when clicking "Run AI Attendance".
    col_class, col_subject, col_date = st.columns([1.2, 1.2, 1.0], gap="medium")

    with col_class:
        selected_class = safe_selectbox(
            label="Class",
            options=classes,
            key="ai_class_selectbox",
            placeholder="Choose class",
            label_func=class_label,
        )

    selected_class_id = _class_id(selected_class) if selected_class else ""
    subjects: list[dict] = []
    if selected_class_id:
        subjects = _assignment_subjects_for_class(assignments, selected_class_id)

    with col_subject:
        if selected_class_id and not subjects:
            st.warning("No subjects assigned to this class yet.")
        selected_subject = safe_selectbox(
            label="Subject",
            options=subjects,
            key="ai_subject_selectbox",
            placeholder="Choose subject",
            label_func=subject_label,
            disabled=not bool(selected_class_id),
        )

    with col_date:
        d = st.date_input("Date", value=date.today(), key="ai_attendance_date")

    cls = _class_id(selected_class) if selected_class else ""
    subj = _subject_id(selected_subject) if selected_subject else ""

    st.session_state["_ai_selected_class_label"] = class_label(selected_class)
    st.session_state["_ai_selected_subject_label"] = subject_label(selected_subject)
    st.session_state["ai_selected_class_id"] = cls
    st.session_state["ai_selected_subject_id"] = subj
    st.session_state["ai_attendance_date"] = d.isoformat() if d else str(date.today())

    st.markdown("#### 📸 Upload Class Photo or Take Live Photo")
    t1, t2 = st.tabs(["📁 Upload Photo", "📷 Live Camera"])
    img_bytes = None

    with t1:
        up = st.file_uploader(
            "Upload group photo", type=["jpg", "jpeg", "png"], key="ai_up"
        )
        if up:
            img_bytes = up.getvalue()
            st.image(up, caption="Uploaded ✅", use_container_width=True)

    with t2:
        photo = st.camera_input("Take live photo", key="ai_live_camera")
        if photo:
            st.image(photo, width=420)
            img_bytes = photo.getvalue()

    btn_l = "Run AI Attendance"
    if st.button(btn_l, type="primary", key="ai_run"):
        # Validation only on click (no section hiding).
        if not cls:
            st.warning("Please select a class.")
            st.stop()
        if not subj:
            st.warning("Please select a subject.")
            st.stop()
        if not st.session_state.get("ai_attendance_date"):
            st.warning("Please select a date.")
            st.stop()
        if not img_bytes:
            st.warning("Please upload a photo or take a live camera photo.")
            st.stop()

        st.session_state.ai_step = "review"
        with st.spinner("🤖 Analysing…"):
            import time

            time.sleep(1.2)
        st.rerun()

    if st.session_state.get("ai_step") == "review":
        _ai_review()



def _ai_review():
    try:
        import pandas as pd
    except Exception:
        pd = None
        try:
            import streamlit as st
            st.warning("Optional dependency 'pandas' not available — some features may be disabled.")
        except Exception:
            pass

    # Keep existing AI review table logic; use labels stored during selection.
    subj = st.session_state.get("_ai_selected_subject_label", "Selected Subject")
    cls = st.session_state.get("_ai_selected_class_label", "Selected Class")
    d = st.session_state.get("ai_attendance_date", str(date.today()))
    selected_class_id = str(st.session_state.get("ai_selected_class_id") or "")
    selected_subject_id = str(st.session_state.get("ai_selected_subject_id") or "")

    st.markdown(f"#### Results - {subj} | {cls} | {d}")
    try:
        with st.spinner("Loading analytics..."):
            data = _live_teacher_data()
    except Exception as exc:
        st.error("Could not load live students for AI attendance review.")
        _show_debug("Developer Debug", str(exc))
        return

    selected_class = next((row for row in data["classes"] if _class_id(row) == selected_class_id), {})
    selected_class_keys = _class_section_keys(_class_name(selected_class), _section(selected_class))
    stu = [
        s for s in data["students"]
        if str(s.get("class_id") or "") == selected_class_id
        or (not s.get("class_id") and _class_section_keys(s.get("class_name"), s.get("section")).intersection(selected_class_keys))
    ]
    if not stu:
        st.warning("No students found for this class.")
        return

    rows = []
    for s in stu:
        rows.append(
            {
                "Student ID": s.get("id"),
                "Roll": s.get("roll_no") or s.get("roll") or "",
                "Name": s.get("name") or s.get("full_name") or "",
                "Present": False,
            }
        )

    df = pd.DataFrame(rows)
    nd = int(df["Present"].sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Detected", nd)
    c2.metric("Absent", len(df) - nd)
    c3.metric("Total Students", len(df))

    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Student ID": None,
            "Present": st.column_config.CheckboxColumn("Present", default=False),
        },
        key="ai_edit",
    )

    col1, col2, _ = st.columns([1, 1, 3])
    if col1.button("Confirm & Save", type="primary", key="ai_confirm"):
        from src.database.client import get_supabase_client
        from src.services.attendance_service import mark_manual_attendance

        supabase = get_supabase_client()
        ctx = get_current_teacher_context(supabase)
        records = []
        for _, r in edited.iterrows():
            student_id = r.get("Student ID")
            if not student_id:
                continue
            records.append(
                {
                    "student_id": student_id,
                    "status": "present" if bool(r.get("Present")) else "absent",
                }
            )

        ok, message, saved_count, errors = mark_manual_attendance(
            supabase=supabase,
            teacher_id=ctx.get("teacher_id"),
            class_id=selected_class_id,
            subject_id=selected_subject_id,
            attendance_date=str(d),
            institute_id=ctx.get("institute_id"),
            records=records,
        )
        if ok:
            st.cache_data.clear()
            st.success(f"{saved_count} records saved to Supabase.")
            if errors:
                st.warning(f"{len(errors)} row(s) skipped: {', '.join(errors[:3])}")
            st.session_state.pop("ai_step", None)
            st.rerun()
        else:
            st.error(f"Attendance not saved: {message}")

    if col2.button("Back", key="ai_back"):
        st.session_state.pop("ai_step", None)
        st.rerun()


def _classes():
    db_status_banner()
    st.markdown("### My Classes")
    st.caption("View your assigned classes, subjects, and attendance actions.")

    _show_debug(
        "Developer Debug",
        {
            "current_page": "teacher_classes",
            "auth_user_id": st.session_state.get("auth_user_id"),
            "teacher_id": st.session_state.get("teacher_id"),
            "institute_id": st.session_state.get("institute_id"),
            "role": st.session_state.get("role"),
            "user_email": st.session_state.get("user_email"),
        },
    )

    try:
        from src.database.client import get_supabase_client
        from src.services.subject_service import generate_subject_join_code, make_qr_image
        from src.services.teacher_service import get_teacher_assignments, resolve_teacher_identity
    except Exception as exc:
        st.error("Teacher classes could not be loaded.")
        _show_debug("Developer Debug", str(exc))
        return

    supabase = get_supabase_client()
    if not supabase:
        st.warning("Supabase is not configured. Add .streamlit/secrets.toml.")
        return

    teacher = resolve_teacher_identity(supabase, show_error=False)
    if not teacher:
        st.warning("Please login first.")
        return

    teacher_id = teacher.get("id") or st.session_state.get("teacher_id")
    assignments = get_teacher_assignments(supabase, teacher_id)
    if not assignments:
        st.info("Your account has no assigned classes yet. Ask institute admin to assign a class and subject.")
        return

    classes = _unique_assignment_classes(assignments)
    if not classes:
        st.info("Your account has no assigned classes yet. Ask institute admin to assign a class and subject.")
        return

    def _active_student_ids_from_rows(rows: list[dict]) -> set[str]:
        out: set[str] = set()
        for r in rows or []:
            sid = r.get("id")
            if sid:
                out.add(str(sid))
        return out

    def _student_ids_by_class_id(selected_class_id: str) -> set[str]:
        # Primary: students.class_id == class.id
        try:
            q = supabase.table("students").select("id").eq("class_id", selected_class_id)
            inst = str(_get_current_institute_id() or teacher.get("institute_id") or "")
            if inst:
                q = q.eq("institute_id", inst)
            rows = q.execute().data or []
            return _active_student_ids_from_rows([r for r in rows if _student_visible_for_teacher(r)])
        except Exception:
            return set()

    def _student_ids_by_class_name_section(selected_class: dict) -> set[str]:
        # Fallback: students.class_name/section matches class_name/section
        class_name = _class_name(selected_class)
        section = _section(selected_class)
        if not class_name:
            return set()
        try:
            q = supabase.table("students").select("id").eq("class_name", class_name).eq("section", section)
            inst = str(_get_current_institute_id() or teacher.get("institute_id") or "")
            if inst:
                q = q.eq("institute_id", inst)
            rows = q.execute().data or []
            return _active_student_ids_from_rows([r for r in rows if _student_visible_for_teacher(r)])
        except Exception:
            return set()

    def _student_ids_via_subject_enrollments(selected_class: dict, selected_subject_rows: list[dict]) -> set[str]:
        # If count still zero: count unique active students enrolled in any
        # subject assigned to this class.
        subject_ids = sorted({_subject_id(row) for row in selected_subject_rows if _subject_id(row)})
        selected_class_id = _class_id(selected_class)
        if not subject_ids:
            return set()

        try:
            enrollment_query = (
                supabase.table("subject_enrollments")
                .select("student_id,class_id,status")
                .in_("subject_id", subject_ids)
            )
            if selected_class_id:
                enrollment_query = enrollment_query.eq("class_id", selected_class_id)
            try:
                enrollments = enrollment_query.execute().data or []
            except Exception:
                enrollments = (
                    supabase.table("subject_enrollments")
                    .select("student_id,status")
                    .in_("subject_id", subject_ids)
                    .execute()
                    .data
                    or []
                )
            enrolled_ids = {
                str(r.get("student_id"))
                for r in enrollments
                if r.get("student_id")
                and str(r.get("status") or "active").strip().lower() in {"", "active"}
            }
            if not enrolled_ids:
                return set()

            try:
                students = supabase.table("students").select("*").in_("id", list(enrolled_ids)).execute().data or []
                inst = str(_get_current_institute_id() or teacher.get("institute_id") or "")
                return {
                    str(row.get("id"))
                    for row in students
                    if row.get("id")
                    and _student_visible_for_teacher(row)
                    and (not inst or str(row.get("institute_id") or "") == inst)
                }
            except Exception:
                return enrolled_ids
        except Exception:
            return set()


    all_assigned_students, fallback_students = _load_assigned_students(
        supabase,
        str(_get_current_institute_id() or teacher.get("institute_id") or ""),
        assignments,
    )

    # Precompute nothing by raw class_id, because some students may be missing class_id.
    # We'll compute count per class using the required 3-step fallback.


    for class_row in classes:
        class_id = _class_id(class_row)
        display_title = _class_title(class_row)
        assigned_subject_rows = _assignment_subjects_for_class(assignments, class_id)
        missing_subject = _assignments_missing_subject_for_class(assignments, class_id)

        logical_class_ids = {
            str(row.get("class_id") or "")
            for row in assignments
            if _assignment_matches_class(row, class_row) and row.get("class_id")
        }
        logical_class_keys = _class_section_keys(
            _class_name(class_row),
            _section(class_row),
        )
        students_count_set = {
            str(student.get("id"))
            for student in all_assigned_students
            if student.get("id")
            and (
                str(student.get("class_id") or "") in logical_class_ids
                or _class_section_keys(
                    student.get("class_name"),
                    student.get("section"),
                ).intersection(logical_class_keys)
            )
        }
        students_count = len(students_count_set)

        first_subject_id = _subject_id(assigned_subject_rows[0]) if assigned_subject_rows else ""

        with st.container(border=True):
            head_left, head_right = st.columns([3, 1])
            with head_left:
                st.markdown(
                    f"""
                    <div class="class-card-header">
                      <div>
                        <div class="class-title">Class {html.escape(display_title)}</div>
                        <div class="class-meta">
                          <span>Students: {students_count}</span>
                          <span>Subjects: {len(assigned_subject_rows)}</span>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if students_count == 0:
                    st.info(
                        "No students linked to this class yet. Ask admin to assign students or share subject join code."
                    )

            with head_right:
                if st.button(
                    "Take Attendance",
                    key=f"cls_{class_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state["selected_teacher_class_id"] = class_id
                    if first_subject_id:
                        st.session_state["selected_teacher_subject_id"] = first_subject_id
                    else:
                        st.session_state.pop("selected_teacher_subject_id", None)
                    nav_teacher("manual_att")
                    st.rerun()

            if not assigned_subject_rows:
                if missing_subject:
                    st.info("Teacher is assigned to this class but no subject is linked. Please assign a subject.")
                else:
                    st.info("No subjects assigned yet.")
                continue


            for subj in assigned_subject_rows:
                raw_name = str(subj.get("subject_name") or subj.get("name") or "Unnamed Subject")
                s_name = raw_name.title() if raw_name.islower() else raw_name
                s_code = subj.get("subject_code") or subj.get("code") or ""
                subj_id = _subject_id(subj)

                st.markdown(
                    f"""
                    <div class="subject-box">
                      <div class="subject-title">{html.escape(str(s_name))}</div>
                      <div class="subject-code">Code: {html.escape(str(s_code or "-"))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                action_cols = st.columns([1, 1, 3])
                if action_cols[0].button("Share Subject", key=f"share_{class_id}_{subj_id}", use_container_width=True):
                    st.session_state["teacher_share_subject_id"] = subj_id
                    st.session_state["teacher_share_class_id"] = class_id
                    st.rerun()

                if st.session_state.get("teacher_share_subject_id") == subj_id:
                    try:
                        app_base_url = (
                            os.getenv("APP_BASE_URL")
                            or st.secrets.get("APP_BASE_URL", "")
                            or st.secrets.get("APP_PUBLIC_URL", "")
                            or ""
                        ).strip().rstrip("/")
                        regen_key = f"regen_{class_id}_{subj_id}"
                        regenerate = st.button("Regenerate Code", key=regen_key, use_container_width=False)
                        data = generate_subject_join_code(
                            supabase,
                            subj_id,
                            teacher_id=teacher_id,
                            base_url=app_base_url or None,
                            regenerate=regenerate,
                        )
                        if not data:
                            st.error("Could not create join code. Check subject_join_codes schema/RLS.")
                        else:
                            join_code = str(data.get("join_code") or data.get("code") or "")
                            base = app_base_url or "http://localhost:8507"
                            join_url = str(data.get("join_url") or f"{base.rstrip('/')}/?join-code={join_code}")
                            if join_code:
                                join_url = f"{base.rstrip('/')}/?join-code={join_code}"
                            expires_at = data.get("expires_at")
                            qr_buf = make_qr_image(join_url)

                            st.markdown("#### Share Subject")
                            with st.container(border=True):
                                st.markdown(
                                    f"""
                                    <div class="subject-title">{html.escape(str(s_name))}</div>
                                    <div class="subject-code">Class: {html.escape(display_title)}</div>
                                    <div class="subject-code">Subject Code: {html.escape(str(s_code or "-"))}</div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                                st.text_input("Join Code", value=join_code, key=f"join_code_out_{subj_id}")
                                st.image(qr_buf, caption="Scan to join this subject", width=220)
                                st.text_input("Join Link", value=join_url, key=f"join_url_out_{subj_id}")
                                if expires_at:
                                    st.caption(f"Valid until {expires_at}")
                                st.markdown("Student instructions:")
                                st.markdown(
                                    "1. Open SnapClass AI.\n"
                                    "2. Scan this QR code.\n"
                                    "3. Login or create account.\n"
                                    "4. Click Join Subject.\n"
                                    "5. Subject will appear in My Subjects."
                                )
                                copy_cols = st.columns(2)
                                with copy_cols[0]:
                                    _clipboard_button("Copy Join Code", join_code, f"copy_code_{subj_id}")
                                with copy_cols[1]:
                                    _clipboard_button("Copy Join Link", join_url, f"copy_link_{subj_id}")
                    except Exception as exc:
                        st.error("Could not create join code. Check subject_join_codes schema/RLS.")
                        _show_debug("Developer Debug", str(exc))

                if action_cols[1].button("Edit Subject", key=f"edit_{class_id}_{subj_id}", use_container_width=True):
                    st.info("Edit Subject is available under the existing Subjects section.")


def _students():
    import pandas as pd

    st.markdown("## Students")

    from src.database.client import get_supabase_client
    from src.services.teacher_service import get_teacher_assignments, resolve_teacher_identity

    supabase = get_supabase_client()
    if not supabase:
        st.error("Supabase is not connected.")
        return

    # Resolve teacher_id from logged-in teacher email.
    teacher = resolve_teacher_identity(supabase, show_error=False)
    teacher_id = (teacher or {}).get("id")
    if not teacher_id:
        st.warning("Please login first.")
        return

    # Search box
    search = st.text_input(
        "🔍 Search",
        placeholder="Name, email, roll, or student code...",
        key="teacher_students_search",
    )

    assignments = get_teacher_assignments(supabase, teacher_id)
    assigned_classes = _unique_assignment_classes(assignments)
    if not assigned_classes:
        st.info("No students found. Ask admin to add students to your assigned class.")
        return

    institute_id = str(_get_current_institute_id() or (teacher or {}).get("institute_id") or "")
    students_by_id: dict[str, dict] = {}
    fallback_students_by_id: dict[str, dict] = {}
    roster_errors: list[dict[str, str]] = []

    with st.spinner("Loading students..."):
        for class_row in assigned_classes:
            class_id = _class_id(class_row)
            try:
                class_students, fallback_students = _load_students_for_manual_class(
                    supabase,
                    class_row,
                    institute_id,
                )
            except Exception as exc:
                roster_errors.append({"class_id": class_id, "error": str(exc)})
                continue

            for student in class_students:
                student_id = str(student.get("id") or "")
                if student_id:
                    students_by_id[student_id] = student
            for student in fallback_students:
                student_id = str(student.get("id") or "")
                if student_id:
                    fallback_students_by_id[student_id] = student

        data = _live_teacher_data()

    students = sorted(
        students_by_id.values(),
        key=lambda row: (
            str(row.get("roll_no") or row.get("roll") or row.get("student_code") or ""),
            str(row.get("name") or row.get("full_name") or "").lower(),
        ),
    )
    fallback_students = list(fallback_students_by_id.values())
    classes_by_id = {
        _class_id(class_row): class_row
        for class_row in assigned_classes
        if _class_id(class_row)
    }
    classes_by_id.update(data.get("classes_by_id") or {})

    _show_debug(
        "Developer Debug",
        {
            "teacher_email": st.session_state.get("user_email") or st.session_state.get("teacher_email"),
            "teacher_id": teacher_id,
            "assigned_class_ids": sorted(classes_by_id),
            "number_of_students_found": len(students),
            "roster_errors": roster_errors,
            "demo_data_enabled": _demo_data_enabled(),
        },
    )
    if fallback_students:
        _show_debug(
            "Developer Debug",
            {
                "warning": "Included students by class_name/section because students.class_id is missing.",
                "count": len(fallback_students),
                "students": [
                    {
                        "id": s.get("id"),
                        "name": s.get("name"),
                        "roll_no": s.get("roll_no") or s.get("roll"),
                        "class_name": s.get("class_name"),
                        "section": s.get("section"),
                    }
                    for s in fallback_students
                ],
            },
        )

    if not students:
        render_empty_state("No students found for your assigned classes.")
        return

    records_by_student: dict[str, list[dict]] = {}
    for record in data.get("records") or []:
        sid = str(record.get("student_id") or "")
        if sid:
            records_by_student.setdefault(sid, []).append(record)

    joined_subjects_by_student: dict[str, int] = {}
    student_ids = sorted({str(student.get("id")) for student in students if student.get("id")})
    if student_ids:
        try:
            enrollments = (
                supabase.table("subject_enrollments")
                .select("student_id,subject_id,status")
                .in_("student_id", student_ids)
                .execute()
                .data
                or []
            )
            for row in enrollments:
                if not _student_is_active(row):
                    continue
                sid = str(row.get("student_id") or "")
                if sid:
                    joined_subjects_by_student[sid] = joined_subjects_by_student.get(sid, 0) + 1
        except Exception as exc:
            _show_debug("Developer Debug", {"student_subject_enrollments_error": str(exc)})

    card_students: list[dict] = []
    for s in students:
        sid = str(s.get("id") or "")
        class_row = classes_by_id.get(str(s.get("class_id") or ""), {})
        class_label = _format_class_label(
            class_row
            or {
                "class_name": s.get("class_name"),
                "name": s.get("class_name"),
                "section": s.get("section"),
            }
        )
        attendance_pct = _attendance_percent(records_by_student.get(sid, []))
        card_students.append(
            {
                **s,
                "Name": s.get("name") or s.get("full_name") or "",
                "Roll No": s.get("roll_no") or s.get("roll") or "",
                "Student Code": s.get("student_code") or "",
                "Class": class_label,
                "Email": s.get("email") or "",
                "Attendance %": f"{attendance_pct}%" if attendance_pct is not None else "No records",
                "Joined Subjects": joined_subjects_by_student.get(sid, 0),
                "display_class": class_label,
                "attendance_text": f"{attendance_pct}%" if attendance_pct is not None else "No records",
                "joined_subjects": joined_subjects_by_student.get(sid, 0),
            }
        )

    df = pd.DataFrame(card_students)

    if search:
        search_lower = search.lower()
        df = df[
            df["Name"].astype(str).str.lower().str.contains(search_lower, na=False)
            | df["Roll No"].astype(str).str.lower().str.contains(search_lower, na=False)
            | df["Student Code"].astype(str).str.lower().str.contains(search_lower, na=False)
            | df["Email"].astype(str).str.lower().str.contains(search_lower, na=False)
            | df["Class"].astype(str).str.lower().str.contains(search_lower, na=False)
        ]

    if df.empty:
        st.warning("No students matched your search.")
        return

    for student in df.to_dict("records"):
        render_student_card(student)




def _analytics():
    db_status_banner()
    st.markdown("## Analytics & Insights")
    st.caption("Detailed attendance analytics across all your classes")

    try:
        import pandas as pd

        data = _live_teacher_data()
    except Exception as exc:
        st.error("Analytics could not be loaded.")
        _show_debug("Developer Debug", str(exc))
        return

    records = data["records"]
    if not records:
        if data["ctx"].get("invalid_assignments"):
            st.warning(
                "Your class and subject assignment do not match. "
                "Ask the institute admin to assign a subject from your institute and selected class."
            )
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Assigned Classes", len(data["classes"]))
            c2.metric("Assigned Students", len(data["students"]))
            c3.metric("Attendance Sessions", len(data["sessions"]))
            c4.metric("Overall Attendance", "0%")
            st.info(
                "Your classes and students are ready. Save attendance once to generate trends and performance charts."
            )
        return

    rows = []
    for record in records:
        session = data["sessions_by_id"].get(str(record.get("session_id") or ""), {})
        class_id = str(record.get("class_id") or session.get("class_id") or "")
        labels = _session_label(session or {"class_id": class_id, "subject_id": record.get("subject_id")}, data["classes_by_id"], data["subjects_by_id"])
        rows.append(
            {
                "date": _date_value(record) or _date_value(session),
                "month": (_date_value(record) or _date_value(session))[:7],
                "class": labels["class"] or class_id,
                "present": 1 if str(record.get("status") or "").lower() == "present" else 0,
                "total": 1,
            }
        )
    df = pd.DataFrame(rows)
    avg = round((df["present"].sum() / df["total"].sum()) * 100, 1)
    class_perf = df.groupby("class", as_index=False).sum(numeric_only=True)
    class_perf["attendance"] = (class_perf["present"] / class_perf["total"] * 100).round(1)
    best_cls = class_perf.sort_values("attendance", ascending=False).iloc[0]["class"] if not class_perf.empty else "-"

    active_student_ids = {
        str(record.get("student_id"))
        for record in records
        if record.get("student_id")
    }
    active_student_count = max(len(data["students"]), len(active_student_ids))
    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, sub, color in [
        (c1, "Overall Average", f"{avg}%", "Live attendance", "#10B981"),
        (c2, "Best Class", best_cls, "Highest live average", "#10B981"),
        (c3, "Total Sessions", len(data["sessions"]), "Live sessions", "#6B7280"),
        (c4, "Active Students", active_student_count, "Assigned students", "#6B7280"),
    ]:
        with col:
            st.markdown(
                f"""<div style="background:white;border-radius:16px;padding:22px;
              border:1px solid #E5E7EB;box-shadow:0 4px 12px rgba(0,0,0,.06);">
              <div style="color:#6B7280;font-size:.82rem;margin-bottom:8px;">{label}</div>
              <div style="font-size:2rem;font-weight:800;font-family:Poppins,sans-serif;">{val}</div>
              <div style="color:{color};font-size:.82rem;margin-top:6px;">{sub}</div>
            </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        trend = df[df["date"].astype(str) != ""].groupby("date", as_index=False).sum(numeric_only=True)
        trend["rate"] = (trend["present"] / trend["total"] * 100).round(1)
        if not trend.empty:
            with time_block("chart rendering: teacher analytics trend"):
                fig1 = px.line(
                    trend,
                    x="date",
                    y="rate",
                    markers=True,
                    title="Weekly Attendance Trend",
                    color_discrete_sequence=["#FF4FA3"],
                )
                fig1.add_hline(y=75, line_dash="dash", line_color="#EF4444")
                fig1.update_layout(
                    plot_bgcolor="#FFFFFF",
                    paper_bgcolor="#FFFFFF",
                    margin=dict(l=20, r=20, t=50, b=20),
                    height=300,
                    font=dict(color="#111827", size=12),
                    title=dict(font=dict(color="#111827", size=17), x=0.02),
                    xaxis=dict(type="category", title="", tickfont=dict(color="#374151")),
                    yaxis=dict(
                        title=dict(text="Attendance %", font=dict(color="#374151")),
                        range=[0, 105],
                        tickfont=dict(color="#374151"),
                        gridcolor="#E5E7EB",
                    ),
                    showlegend=False,
                )
                fig1.update_traces(line_width=3, marker_size=8)
                st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
    with col2:
        if not class_perf.empty:
            with time_block("chart rendering: teacher analytics class"):
                fig2 = px.bar(
                    class_perf,
                    x="class",
                    y="attendance",
                    title="Class Performance",
                    color_discrete_sequence=["#5B6CFF"],
                )
                fig2.add_hline(y=75, line_dash="dash", line_color="#EF4444")
                fig2.update_layout(
                    plot_bgcolor="#FFFFFF",
                    paper_bgcolor="#FFFFFF",
                    margin=dict(l=20, r=20, t=50, b=20),
                    height=300,
                    font=dict(color="#111827", size=12),
                    title=dict(font=dict(color="#111827", size=17), x=0.02),
                    xaxis=dict(title="", tickfont=dict(color="#374151")),
                    yaxis=dict(
                        title=dict(text="Attendance %", font=dict(color="#374151")),
                        range=[0, 105],
                        tickfont=dict(color="#374151"),
                        gridcolor="#E5E7EB",
                    ),
                    showlegend=False,
                )
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("#### Monthly Breakdown")
    monthly = df[df["month"].astype(str) != ""].groupby("month", as_index=False).sum(numeric_only=True)
    monthly["attendance"] = (monthly["present"] / monthly["total"] * 100).round(1)
    for _, row in monthly.iterrows():
        month = str(row["month"])
        pct = float(row["attendance"])
        color = "#5B6CFF" if pct >= 85 else "#FF4FA3"
        st.markdown(
            f"""<div style="display:flex;align-items:center;padding:10px 0;
          border-bottom:1px solid #F3F4F6;">
          <span style="font-weight:600;width:80px;">{html.escape(month)}</span>
          <div style="flex:1;margin:0 16px;background:#F3F4F6;border-radius:999px;
            height:10px;overflow:hidden;">
            <div style="width:{pct}%;background:linear-gradient(90deg,{color},#818cf8);
              height:10px;border-radius:999px;"></div></div>
          <span style="font-weight:700;color:{color};width:48px;text-align:right;">{pct:.1f}%</span>
        </div>""",
            unsafe_allow_html=True,
        )


def _reports():
    db_status_banner()
    st.markdown("### Reports")

    try:
        import pandas as pd

        with st.spinner("Loading reports..."):
            data = _live_teacher_data()
    except Exception as exc:
        st.error("Reports could not be loaded.")
        _show_debug("Developer Debug", str(exc))
        return

    report_records = get_teacher_report_records(str((data.get("ctx") or {}).get("teacher_id") or ""), data)
    if not report_records:
        st.info("No live attendance records found yet. Take attendance first to generate reports.")
        return

    ctx = data.get("ctx") or {}
    teacher_assignments = ctx.get("assignments") or []

    # Build teacher-assigned class dropdown options with required label style.
    def _class_dropdown_label(class_row: dict) -> str:
        label = _format_class_label(class_row)
        return f"Class {label}" if label != "Class" else "Class"

    assigned_classes = _unique_assignment_classes(teacher_assignments)
    if not assigned_classes:
        class_options: list[dict] = []
    else:
        class_options = assigned_classes

    if not class_options:
        class_placeholder = "No assigned classes found."
        # Render a clean empty-state if there are no assignments to filter by.
        st.warning(class_placeholder)

    # Map label -> class_id (for filtering sessions/records)
    label_to_class_id: dict[str, str] = {}
    dropdown_labels: list[str] = ["All"]
    for c in class_options:
        cid = _class_id(c)
        if not cid:
            continue
        lbl = _class_dropdown_label(c)
        label_to_class_id[lbl] = cid
        dropdown_labels.append(lbl)

    # Per-session counts for attendance %
    session_record_counts: dict[str, dict[str, int]] = {}
    for item in report_records:
        record = item["record"]
        session_id = str(record.get("session_id") or "")
        bucket = session_record_counts.setdefault(session_id, {"present": 0, "total": 0})
        bucket["total"] += 1
        if str(record.get("status") or "").lower() == "present":
            bucket["present"] += 1

    def _status_label(v: Any) -> str:
        s = str(v or "").strip().lower()
        if not s:
            return "present"
        return s.title()

    rows: list[dict] = []
    for item in report_records:
        record = item["record"]
        session_id = str(record.get("session_id") or "")
        counts = session_record_counts.get(session_id, {"present": 0, "total": 0})
        pct = round(counts["present"] / counts["total"] * 100, 1) if counts["total"] else 0
        rows.append(
            {
                **item,
                "Class ID": item.get("class_id") or "",
                "Class": item.get("class_label") or "-",
                "Subject": f"{item.get('subject_name', 'Subject')} {item.get('subject_code', '')}".strip(),
                "Date": item.get("attendance_date") or "",
                "Student Name": item.get("student_name") or "",
                "Roll No": item.get("roll_no") or "",
                "Status": _status_label(record.get("status")),
                "Verification": item.get("verification") or "Manual",
                "Attendance %": pct,
            }
        )

    display = pd.DataFrame(rows)

    # Filter by teacher-assigned class and date.
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        f = st.selectbox("Filter by Class", dropdown_labels, key="r_cls")
    date_options = ["All"] + sorted([value for value in display["Date"].dropna().astype(str).unique().tolist() if value], reverse=True)
    with filter_col2:
        date_filter = st.selectbox("Filter by Date", date_options, key="r_date")

    if f != "All":
        class_id = label_to_class_id.get(f)
        if class_id:
            display = display[display["Class ID"].astype(str) == str(class_id)]

    if date_filter != "All" and not display.empty:
        display = display[display["Date"].astype(str) == str(date_filter)]

    if display.empty:
        render_empty_state("No attendance records found for selected filters.")
        return

    total_rows = len(display)
    present_rows = sum(1 for value in display["Status"].astype(str).str.lower() if value == "present")
    absent_rows = sum(1 for value in display["Status"].astype(str).str.lower() if value == "absent")
    attendance_pct = round((present_rows / total_rows) * 100, 1) if total_rows else 0

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    c1.metric("Total Records", total_rows)
    c2.metric("Present", present_rows)
    c3.metric("Absent", absent_rows)
    c4.metric("Overall Attendance %", f"{attendance_pct}%")

    for record in display.to_dict("records"):
        render_report_record(record)

    export_columns = ["Class", "Subject", "Date", "Student Name", "Roll No", "Status", "Verification", "Attendance %"]
    csv = display[export_columns].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export CSV",
        csv,
        "teacher_attendance_report.csv",
        "text/csv",
        use_container_width=True,
    )


def _profile():
    from src.components.avatar import render_profile_photo_section
    from src.database.client import get_supabase_client
    from src.services.profile_photo_service import fetch_user_profile
    from src.services.teacher_service import resolve_teacher_identity

    st.markdown("### My Profile")
    supabase = get_supabase_client()
    if not supabase:
        st.error("Supabase is not connected.")
        return

    teacher = resolve_teacher_identity(supabase, show_error=False) or {}
    email = str(
        teacher.get("email")
        or st.session_state.get("user_email")
        or st.session_state.get("teacher_email")
        or ""
    ).strip().lower()
    profile = fetch_user_profile(supabase, email)
    name = (
        profile.get("full_name")
        or teacher.get("name")
        or st.session_state.get("user_name")
        or "Teacher"
    )
    user = {
        **teacher,
        **profile,
        "name": name,
        "full_name": name,
        "email": profile.get("email") or email,
        "role": "teacher",
        "profile_photo_url": profile.get("profile_photo_url") or teacher.get("profile_photo_url") or "",
    }
    render_profile_photo_section(supabase, user, key_prefix="teacher_profile")

    st.markdown("#### Account Details")
    details = {
        "Full Name": user.get("full_name") or "Not set",
        "Email": user.get("email") or "Not set",
        "Teacher Code": teacher.get("teacher_code") or teacher.get("invite_code") or "Not set",
        "Institute ID": teacher.get("institute_id") or "Not assigned",
    }
    for label, value in details.items():
        st.markdown(f"**{label}:** {html.escape(str(value))}")
