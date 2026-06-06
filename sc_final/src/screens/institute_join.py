"""Invited institute-admin join flow using an institute access code."""

import streamlit as st

from src.components.navigation import go_to
from src.components.public_nav import render_public_nav
from src.services.institute_service import (
    init_institute_state,
    mark_code_used,
    set_active_institute,
    validate_access_code,
)


def _debug_enabled() -> bool:
    import os

    return str(os.getenv("APP_ENV", "")).strip().lower() == "development" or bool(st.session_state.get("debug_mode"))


def show_institute_join() -> None:
    init_institute_state()
    render_public_nav(show_links=False)

    st.markdown(
        """
        <style>
        .auth-logo-card {
            max-width: 720px;
            margin: 20px auto 24px auto;
            background: #ffffff;
            border-radius: 18px;
            padding: 18px 22px;
            display: flex;
            gap: 14px;
            align-items: center;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
            border: 1px solid #e5e7eb;
        }
        .logo-box {
            width: 52px;
            height: 52px;
            border-radius: 14px;
            background: linear-gradient(135deg, #6366f1, #ec4899);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 22px;
        }
        .auth-logo-card h3 {
            margin: 0;
            font-size: 22px;
            font-weight: 800;
            color: #111827;
        }
        .auth-logo-card p {
            margin: 2px 0 0 0;
            color: #6b7280;
            font-size: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div class="auth-logo-card">
                <div class="logo-box">S</div>
                <div>
                    <h3>SnapClass AI</h3>
                    <p>Institute Admin Access</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav1, nav2 = st.columns(2)
        if nav1.button("Back", key="join_back_login", use_container_width=True):
            go_to("institute_login")
        if nav2.button("Try Demo", key="join_try_demo_top", use_container_width=True):
            st.session_state.return_to = "pricing"
            go_to("demo_signup")

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

            mark_result = mark_code_used(
                code_record.get("code", code),
                admin_email=admin_email,
                institute_id=institute.get("id", ""),
            )
            if not mark_result.get("ok"):
                st.warning("Admin access is ready, but the access code status was not updated.")
                if _debug_enabled():
                    with st.expander("Developer Debug", expanded=False):
                        st.code(str(mark_result.get("debug") or mark_result.get("message") or mark_result))

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
            st.session_state.current_institute_id = institute.get("id", "")
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
        if c2.button("Try Demo", key="join_try_demo_bottom", use_container_width=True):
            st.session_state.return_to = "pricing"
            go_to("demo_signup")
