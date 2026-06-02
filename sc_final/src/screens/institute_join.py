"""Invited institute-admin join flow using an institute access code."""

import streamlit as st

from src.components.navigation import go_to
from src.components.public_nav import render_public_nav
from src.services.institute_service import (
    init_institute_state,
    set_active_institute,
    validate_access_code,
)


def show_institute_join() -> None:
    init_institute_state()
    render_public_nav(show_links=False)

    top1, top2 = st.columns(2)
    if top1.button("Back to Admin Login", key="join_back_login", use_container_width=True):
        go_to("institute_login")
    if top2.button("Start Free Demo", key="join_start_demo_top", use_container_width=True):
        st.session_state.return_to = "pricing"
        go_to("demo_signup")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## Institute Admin Access")
        st.caption("Use this only if you already received an institute access code.")

        with st.form("institute_admin_join_form"):
            admin_name = st.text_input("Admin Name *", placeholder="Priya Sharma")
            admin_email = st.text_input("Admin Email *", placeholder="admin@institute.com")
            admin_password = st.text_input(
                "Password *",
                placeholder="Enter your password",
                type="password",
            )
            access_code = st.text_input("Institute Access Code *", placeholder="SC-SUNRISE-AB12")
            submitted = st.form_submit_button("Continue", type="primary", use_container_width=True)

        if submitted:
            if not admin_name.strip() or not admin_email.strip() or not admin_password or not access_code.strip():
                st.error("Please fill all fields.")
                return

            code = access_code.strip().upper().replace(" ", "")
            result = validate_access_code(code)
            if not result.get("ok"):
                st.error(result.get("message") or "Invalid institute access code.")
                return

            institute = result["institute"]
            code_record = result["code"]
            set_active_institute(institute, code_value=code_record.get("code", ""))

            from src.services.auth_service import login_institute_admin

            ok, msg = login_institute_admin(
                email=admin_email,
                password=admin_password,
                name=admin_name,
                institute_id=institute.get("id"),
            )
            if not ok:
                st.error(msg or "Institute admin access failed.")
                return

            st.session_state.logged_in = True
            st.session_state.portal = "admin"
            st.session_state.role = "institute_admin"
            st.session_state.admin_name = admin_name.strip()
            st.session_state.admin_email = admin_email.strip().lower()
            st.session_state.user_name = admin_name.strip()
            st.session_state.user_email = admin_email.strip().lower()
            st.session_state.email = admin_email.strip().lower()
            st.session_state.institute_id = institute.get("id", "")
            st.session_state.active_institute_id = institute.get("id", "")
            st.session_state.active_institute_name = institute.get("name", "")
            st.session_state.current_institute = institute
            st.session_state.admin_onboarding_completed = bool(
                institute.get("onboarding_completed", False)
            )

            if st.session_state.admin_onboarding_completed:
                st.session_state.page = "institute_dashboard"
                st.session_state.institute_page = "institute_dashboard"
            else:
                st.session_state.page = "institute_setup"
            st.rerun()

        st.markdown("---")
        c1, c2 = st.columns(2)
        if c1.button("Admin Login", key="join_admin_login_bottom", use_container_width=True):
            go_to("institute_login")
        if c2.button("Start Free Demo", key="join_start_demo_bottom", use_container_width=True):
            st.session_state.return_to = "pricing"
            go_to("demo_signup")
