from __future__ import annotations

from collections.abc import Sized
from typing import Any

import streamlit as st

from src.utils.perf import perf_enabled


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if hasattr(value, "empty"):
        try:
            return bool(value.empty)
        except Exception:
            pass
    if isinstance(value, Sized) and not isinstance(value, (str, bytes)):
        return len(value) == 0
    return False


def require_login(required_role: str | None = None) -> bool:
    role = st.session_state.get("role")
    if not role:
        st.warning("Please login first.")
        if st.button("Go to Login", key=f"go_login_{required_role or 'home'}"):
            if required_role == "teacher":
                st.session_state.page = "teacher_auth"
            elif required_role == "student":
                st.session_state.page = "student_auth"
            elif required_role in {"founder", "admin", "institute_admin"}:
                st.session_state.page = "founder_auth" if required_role == "founder" else "institute_login"
            else:
                st.session_state.page = "landing"
            st.rerun()
        return False

    if required_role:
        allowed = {required_role}
        if required_role == "teacher":
            allowed = {"teacher", "subject_teacher", "class_teacher"}
        if role not in allowed:
            st.warning("You do not have access to this page.")
            return False

    return True


def require_teacher_assignment(assignments: Any) -> bool:
    if _is_empty(assignments):
        st.info("No class assigned yet. Contact admin.")
        return False
    return True


def require_student_class(student: Any) -> bool:
    if not student:
        st.info("Your class is not assigned yet. Contact admin.")
        return False
    if isinstance(student, dict) and not student.get("class_id"):
        st.info("Your class is not assigned yet. Contact admin.")
        return False
    return True


def show_no_subjects() -> None:
    st.info("No subjects enrolled yet. Enter subject join code or contact your teacher.")


def show_no_students() -> None:
    st.info("No students found in this class. Add students first.")


def show_no_attendance_records() -> None:
    st.info("No attendance records yet.")


def show_no_reports() -> None:
    st.info("No report data available yet. Attendance must be marked first.")


def show_faceid_unavailable() -> None:
    st.warning("FaceID is currently unavailable. Use manual attendance.")


def show_faceid_not_enrolled() -> None:
    st.warning("FaceID not enrolled yet. Please enroll your face first.")


def show_payment_not_configured() -> None:
    st.warning("Payment setup is not configured yet.")


def show_email_not_configured() -> None:
    st.warning("Email service is not configured yet.")


def show_supabase_not_configured() -> None:
    st.warning("Supabase is not configured. Add .streamlit/secrets.toml.")


def show_clean_error(message: str, debug: Any | None = None) -> None:
    st.error(message)
    if debug and perf_enabled():
        with st.expander("Developer Debug", expanded=False):
            st.code(str(debug))
