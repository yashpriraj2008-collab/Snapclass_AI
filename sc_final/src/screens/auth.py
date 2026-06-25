"""Auth screens - Student, Teacher login/register."""
from __future__ import annotations

import streamlit as st

from src.services.auth_service import handle_google_post_login, google_login, verify_student, verify_teacher
from src.services.user_onboarding_service import (
    register_student_with_code,
    register_teacher_with_invite,
)
from src.utils.session import login
from src.database.client import supabase_secrets_ready
from src.components.auth_components import (
    AuthCard,
    AuthCardEnd,
    AuthBackButton,
    AuthHeader,
    AuthInput,
    AuthButton,
    GoogleButton,
    AuthDivider,
)


def _supabase_ready() -> bool:
    return supabase_secrets_ready()


def _show_debug(result: dict) -> None:
    if result.get("debug"):
        with st.expander("Developer Debug", expanded=False):
            st.code(str(result.get("debug")))


def show_auth(role_hint: str = "student") -> None:
    """Compatibility wrapper called by old app.py."""
    if role_hint == "teacher":
        show_teacher_auth()
    else:
        show_student_auth()


def show_student_auth() -> None:
    if not _supabase_ready():
        return

    AuthCard()
    AuthBackButton(key="auth_student_back")
    AuthHeader(
        title="Student Portal",
        subtitle="Sign in or create your account",
        brand_text="ST",
    )

    tab_in, tab_reg = st.tabs(["Sign In", "Register"])

    with tab_in:
        google_auth = google_login()
        google_url = google_auth.get("url") if isinstance(google_auth, dict) and google_auth.get("ok") else None
        GoogleButton(google_url)

        AuthDivider()

        email = AuthInput("Email", key="sl_email", placeholder="you@email.com")
        pwd = AuthInput("Password", key="sl_pass", placeholder="Password", type="password")

        if AuthButton("Sign In", key="sl_submit"):
            if not email or not pwd:
                st.error("Please enter email and password.")
            else:
                user = verify_student(email, pwd)
                if isinstance(user, dict) and user.get("ok"):
                    if user.get("student_id"):
                        st.session_state["student_id"] = str(user.get("student_id"))
                    if user.get("roll"):
                        st.session_state["roll_no"] = str(user.get("roll"))
                    target_student_page = "subjects" if st.session_state.get("pending_join_code") else "dashboard"
                    st.session_state["student_page"] = target_student_page
                    login(
                        "student",
                        user.get("name", email.split("@")[0].title()),
                        user.get("email", email),
                        user_roll=user.get("roll", ""),
                        page="dashboard",
                    )
                elif isinstance(user, dict) and user.get("message"):
                    st.error(user.get("message"))
                    if user.get("debug"):
                        with st.expander("Developer Debug", expanded=False):
                            st.info(user.get("debug"))
                else:
                    st.error("Invalid email or password.")

    with tab_reg:
        full_name = AuthInput("Full Name *", key="sr_full_name", placeholder="Your Name")
        email = AuthInput("Email *", key="sr_email", placeholder="you@email.com")
        code = AuthInput("Roll Number or Student Code *", key="sr_roll", placeholder="STU-AB12CD34")
        st.caption(
            "Get this code from your class teacher or institute admin. "
            "It may be shared on WhatsApp, email, or your student ID slip."
        )

        if st.button("I don't have a code", key="sr_no_code", use_container_width=False):
            st.session_state["student_no_code_help"] = True
        if st.session_state.get("student_no_code_help"):
            st.info(
                "You need a student code to register. Ask your teacher or institute admin to add you first."
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Back to Login", key="sr_back_login", use_container_width=True):
                    st.session_state["student_no_code_help"] = False
                    st.info("Open the Sign In tab to log in if you already have an account.")
            with c2:
                if st.button("Contact Institute", key="sr_contact_institute", use_container_width=True):
                    st.info("Please contact your school/coaching admin.")

        pwd = AuthInput("Password *", key="sr_password", placeholder="Min 8 chars", type="password")

        if AuthButton("Create Account", key="sr_submit"):
            full_name = (full_name or "").strip()
            email = (email or "").strip().lower()
            code = (code or "").strip()
            pwd = (pwd or "").strip()

            missing = []
            if not full_name:
                missing.append("Full Name")
            if not email:
                missing.append("Email")
            if not pwd:
                missing.append("Password")
            if not code:
                missing.append("Roll Number or Student Code")

            if missing:
                if "Roll Number or Student Code" in missing:
                    st.error(
                        "You need a student code to register. Ask your teacher or institute admin to add you first."
                    )
                    return
                st.error("Please fill: " + ", ".join(missing))
                return
            if len(pwd) < 8:
                st.error("Password must be at least 8 characters.")
                return
            if not _supabase_ready():
                return

            result = register_student_with_code(email=email, password=pwd, student_code_or_roll_no=code)
            if result.get("ok"):
                student = result.get("student") or {}
                auth_user_id = str(result.get("auth_user_id") or "")
                st.session_state["auth_user_id"] = auth_user_id
                st.session_state["user_id"] = auth_user_id
                st.session_state["student_id"] = str(student.get("id") or "")
                st.session_state["institute_id"] = student.get("institute_id")
                st.session_state["class_id"] = student.get("class_id")
                st.session_state["role"] = "student"
                st.session_state["portal"] = "student"
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email
                st.session_state["email"] = email
                st.session_state["user_name"] = student.get("name") or full_name
                st.session_state["student_page"] = "subjects" if st.session_state.get("pending_join_code") else "dashboard"
                st.session_state["page"] = "dashboard"
                st.rerun()
            else:
                msg = (result.get("message") or "Registration failed.").strip()
                if "Invalid student code" in msg or "Invalid student code/roll number" in msg:
                    st.error("Invalid student code. Please ask your teacher/admin.")
                elif "Student account already exists" in msg or "already exists" in msg:
                    st.error("Student account already exists. Please login.")
                elif "No student record found" in msg or ("student record" in msg and "not found" in msg.lower()):
                    st.error("No student record found. Ask your teacher/admin to add you first.")
                else:
                    st.error(msg)
                _show_debug(result)

    AuthCardEnd()


def show_teacher_auth() -> None:
    if not _supabase_ready():
        return

    AuthCard()
    AuthBackButton(key="auth_teacher_back")
    AuthHeader(
        title="Teacher Portal",
        subtitle="Sign in or create your account",
        brand_text="TC",
    )

    # If OAuth completed recently, attempt to handle/route.
    handle_google_post_login()

    tab_in, tab_reg = st.tabs(["Sign In", "Register"])

    with tab_in:
        google_auth = google_login()
        google_url = google_auth.get("url") if isinstance(google_auth, dict) and google_auth.get("ok") else None
        GoogleButton(google_url)

        AuthDivider()

        email = AuthInput("Email", key="tl_email", placeholder="teacher@school.com")
        pwd = AuthInput("Password", key="tl_pass", placeholder="Password", type="password")

        if AuthButton("Sign In", key="tl_submit"):
            if not email or not pwd:
                st.error("Please enter email and password.")
            else:
                user = verify_teacher(email, pwd)
                if user.get("ok"):
                    if user.get("auth_user_id"):
                        st.session_state["auth_user_id"] = str(user.get("auth_user_id"))
                    if user.get("user_id"):
                        st.session_state["user_id"] = str(user.get("user_id"))
                    if user.get("teacher_id"):
                        st.session_state["teacher_id"] = str(user.get("teacher_id"))
                    if user.get("institute_id"):
                        st.session_state["institute_id"] = user.get("institute_id")
                        st.session_state["active_institute_id"] = user.get("institute_id")
                    login(
                        "teacher",
                        user.get("name", email.split("@")[0].title()),
                        user.get("email", email),
                        institute_id=user.get("institute_id"),
                        page="dashboard",
                    )
                else:
                    st.error(user.get("message", "Invalid email or password."))
                    if user.get("debug"):
                        with st.expander("Developer Debug", expanded=False):
                            st.info(user.get("debug"))

    with tab_reg:
        st.markdown("### Create Teacher Account")
        st.caption("Use the invite code shared by your institute admin.")

        full_name = AuthInput("Full Name *", key="tr_full_name", placeholder="Dr. Sharma")
        email = AuthInput("Email *", key="tr_email", placeholder="teacher@school.com")
        invite_code = AuthInput("Teacher Invite Code *", key="tr_invite_code", placeholder="TCH-AB12CD34")
        st.caption(
            "Get this invite code from your institute admin or SnapClass school coordinator."
        )

        if st.button("I don't have an invite code", key="tr_no_invite_code", use_container_width=False):
            st.info(
                "Ask your institute admin to add you as a teacher first. "
                "You cannot register without an invite code."
            )

        pwd = AuthInput("Password *", key="tr_password", placeholder="Min 8 chars", type="password")

        if AuthButton("Create Account", key="tr_submit"):
            full_name = (full_name or "").strip()
            email = (email or "").strip().lower()
            invite_code = (invite_code or "").strip()
            pwd = (pwd or "").strip()

            missing = []
            if not full_name:
                missing.append("Full Name")
            if not email:
                missing.append("Email")
            if not invite_code:
                missing.append("Teacher Invite Code")
            if not pwd:
                missing.append("Password")

            if missing:
                st.error("Please fill: " + ", ".join(missing))
                return
            if len(pwd) < 8:
                st.error("Password must be at least 8 characters.")
                return
            if not _supabase_ready():
                return

            result = register_teacher_with_invite(email=email, password=pwd, invite_code=invite_code)
            if result.get("ok"):
                teacher = result.get("teacher") or {}
                auth_user_id = str(result.get("auth_user_id") or "")
                st.session_state["auth_user_id"] = auth_user_id
                st.session_state["user_id"] = auth_user_id
                st.session_state["teacher_id"] = str(teacher.get("id") or "")
                st.session_state["institute_id"] = teacher.get("institute_id")
                st.session_state["active_institute_id"] = teacher.get("institute_id")
                st.session_state["role"] = "teacher"
                st.session_state["portal"] = "teacher"
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email
                st.session_state["email"] = email
                st.session_state["user_name"] = teacher.get("name") or full_name
                st.session_state["teacher_page"] = "dashboard"
                st.session_state["page"] = "dashboard"
                st.rerun()
            else:
                msg = (result.get("message") or "Registration failed.").strip()
                if "Database schema missing teachers.invite_code" in msg:
                    st.error(
                        "Database schema missing teachers.invite_code. "
                        "Run database/fix_teacher_invite_code.sql."
                    )
                elif "Invalid teacher email or invite code" in msg or "Invalid teacher invite code" in msg:
                    st.error("Invalid teacher email or invite code.")
                elif "not assigned to this email" in msg:
                    st.error("This invite code is not assigned to this email.")
                elif "already exists" in msg:
                    st.error("Teacher account already exists. Please sign in.")
                elif "expired" in msg:
                    st.error("This invite code has expired. Ask admin to generate a new one.")
                elif "rate limit" in msg.lower() or "too many signup" in msg.lower():
                    st.error(
                        "Too many signup attempts. Please wait a few minutes, "
                        "or sign in if this account already exists."
                    )
                elif "Supabase unavailable" in msg:
                    st.error("Supabase unavailable. Please try again.")
                else:
                    st.error(msg)
                _show_debug(result)

    AuthCardEnd()


def show_admin_auth() -> None:
    from src.screens.institute_login import show_institute_login

    show_institute_login()
