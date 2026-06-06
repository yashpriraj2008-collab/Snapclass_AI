"""Existing institute-admin login."""

from __future__ import annotations

import streamlit as st

from src.components.navigation import go_to, render_back_to_home
from src.components.public_nav import render_public_nav
from src.services.institute_admin_service import authenticate_existing_admin
from src.services.auth_service import reset_password
from src.services.institute_service import init_institute_state, set_active_institute


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
    render_public_nav(show_links=False)

    render_back_to_home(key="admin_login_back_home")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## Admin Login")
        st.caption("Sign in, register with an institute code, or create a new institute account.")

        with st.form("existing_admin_login_form"):
            email = st.text_input("Admin Email", placeholder="admin@institute.com", key="admin_login_email")
            password = st.text_input("Admin Password", type="password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            result = authenticate_existing_admin(email=email, password=password)
            if not result.get("ok"):
                st.error(result.get("message") or "Invalid email or password.")
                if result.get("debug"):
                    with st.expander("Developer Debug", expanded=False):
                        st.info(result.get("debug"))
                return

            _set_admin_session(result)
            if result.get("needs_setup"):
                st.session_state.page = "institute_setup"
            else:
                st.session_state.page = "institute_dashboard"
                st.session_state.institute_page = "institute_dashboard"
            st.rerun()

        st.markdown("---")
        c1, c2 = st.columns(2)
        if c1.button("Forgot Password", key="admin_forgot_password", use_container_width=True):
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
        if c2.button("Join Institute with Code", key="admin_join_with_code", use_container_width=True):
            go_to("institute_join")

        if st.button("Create New Institute", key="admin_create_new_institute", use_container_width=True):
            st.session_state.return_to = "pricing"
            go_to("demo_signup")
