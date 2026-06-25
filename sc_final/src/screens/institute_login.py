"""Existing institute-admin login."""
from __future__ import annotations

import streamlit as st

from src.components.navigation import go_to
from src.services.institute_admin_service import authenticate_existing_admin
from src.services.auth_service import google_login, reset_password
from src.services.institute_service import init_institute_state, set_active_institute
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


def _set_admin_session(result: dict) -> None:
    institute = result.get("institute") or {}
    profile = result.get("profile") or {}
    institute_id = result.get("institute_id") or profile.get("institute_id") or institute.get("id") or ""
    user_email = result.get("email", "")
    user_name = result.get("name") or profile.get("full_name") or user_email
    auth_user_id = result.get("auth_user_id", "")

    if institute:
        set_active_institute(institute)
    else:
        st.session_state.current_institute = {
            "id": institute_id,
            "name": "",
            "admin_name": user_name,
            "admin_email": user_email,
            "onboarding_completed": False,
        }
        st.session_state.active_institute_id = institute_id
        st.session_state.current_institute_id = institute_id
        st.session_state.active_institute_name = ""

    st.session_state.logged_in = True
    st.session_state.portal = "admin"
    st.session_state.role = "admin"
    st.session_state.admin_name = user_name
    st.session_state.admin_email = user_email
    st.session_state.user_name = user_name
    st.session_state.user_email = user_email
    st.session_state.email = user_email
    st.session_state.auth_user_id = auth_user_id
    st.session_state.user_id = auth_user_id
    st.session_state.institute_id = institute_id
    st.session_state.active_institute_id = institute_id
    st.session_state.current_institute_id = institute_id
    st.session_state.admin_onboarding_completed = bool(
        institute.get("onboarding_completed", False)
    )


def show_institute_login() -> None:
    init_institute_state()

    AuthCard()
    AuthBackButton(key="admin_login_back_home")
    AuthHeader(
        title="Admin Portal",
        subtitle="Sign in to manage your institute",
        brand_text="AD",
    )

    # Email + password (no st.form wrapper — causes width overflow in card)
    email = AuthInput("Admin Email", key="admin_login_email", placeholder="admin@institute.com")
    password = AuthInput("Admin Password", key="admin_login_password", placeholder="Enter your password", type="password")

    if AuthButton("Login", key="admin_login_submit"):
        result = authenticate_existing_admin(email=email, password=password)
        if not result.get("ok"):
            st.error(result.get("message") or "Invalid email or password.")
            if result.get("debug"):
                with st.expander("Developer Debug", expanded=False):
                    st.info(result.get("debug"))
        else:
            _set_admin_session(result)
            if result.get("needs_setup"):
                st.session_state.page = "institute_setup"
            else:
                st.session_state.page = "institute_dashboard"
                st.session_state.institute_page = "institute_dashboard"
            st.rerun()

    AuthDivider()

    google_auth = google_login()
    google_url = google_auth.get("url") if isinstance(google_auth, dict) and google_auth.get("ok") else None
    GoogleButton(google_url)

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Forgot Password", key="admin_forgot_password", use_container_width=True):
            email_value = st.session_state.get("admin_login_email", "")
            if not email_value:
                st.warning("Enter your admin email first.")
            else:
                result = reset_password(email_value)
                if result.get("ok"):
                    st.success("Password reset email sent.")
                else:
                    st.error(result.get("message") or "Could not send password reset email.")
                    if result.get("debug"):
                        with st.expander("Developer Debug", expanded=False):
                            st.info(result.get("debug"))
    with c2:
        if st.button("Join with Code", key="admin_join_with_code", use_container_width=True):
            go_to("institute_join")

    if st.button("Create New Institute", key="admin_create_new_institute", use_container_width=True):
        st.session_state.return_to = "pricing"
        go_to("demo_signup")

    AuthCardEnd()
