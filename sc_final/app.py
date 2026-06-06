"""SnapClass AI — Main router. Fully fixed."""
import os
import sys
import traceback
import streamlit as st

from src.components.ui import load_css
from src.components.keyboard import enable_enter_to_next_input
from src.database.client import preflight_supabase_secrets
from src.utils.session import init_session
from src.utils.responsive_ui import inject_responsive_css
from src.components.snapbot import render_snapbot_floating
from src.utils.perf import perf_enabled, time_block





root_dir = os.path.abspath(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

favicon_path = os.path.join(root_dir, "static", "favicon.png")
st.set_page_config(
    page_title="SnapClass AI",
    page_icon=favicon_path if os.path.isfile(favicon_path) else "🎓",
    layout="wide",
    initial_sidebar_state="auto",
)
with time_block("app startup"):
    load_css()

st.markdown(
    """
<style>

.stTextInput input,
.stDateInput input {
    background-color: #ffffff !important;
    color: #111827 !important;
}

.stFileUploader,
.stCameraInput {
    background-color: transparent !important;
    color: #111827 !important;
}

.stFileUploader * {
    color: #111827 !important;
}

.snap-hidden-debug {
    display: none;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
}

/* MAIN PAGE */
.main {
    background: #f5f7fb;
}

/* CARDS */
.block-container {
    padding-top: 1rem;
}

/* SUCCESS BOX */
.stSuccess {
    border-radius: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)
inject_responsive_css()

with time_block("auth context load"):
    init_session()

if st.query_params.get("reset") == "1":
    st.session_state.clear()

join_code_from_url = str(
    st.query_params.get("join_code")
    or st.query_params.get("join-code")
    or ""
).strip().upper()
if join_code_from_url:
    st.session_state["pending_join_code"] = join_code_from_url
    if not st.session_state.get("role"):
        st.session_state["page"] = "student_auth"
    elif st.session_state.get("role") == "student":
        st.session_state["student_page"] = "subjects"

supabase_ready, _supabase_message = preflight_supabase_secrets(show_notice=True)
if not supabase_ready:
    st.stop()

if "page" not in st.session_state:
    st.session_state.page = "landing"

page = st.session_state.get("page", "landing")
role = st.session_state.get("role")
if st.query_params.get("razorpay_payment_id") and st.query_params.get("razorpay_signature"):
    page = "payment_success"
    st.session_state.page = page


def _go_home() -> None:
    st.session_state.page = "landing"
    st.rerun()


def _snapbot_page_key() -> str:
    if role == "founder":
        return st.session_state.get("founder_page", "founder_dashboard")
    if role in {"institute_admin", "admin"}:
        institute_page = st.session_state.get("institute_page", "institute_dashboard")
        admin_map = {
            "institute_dashboard": "admin_dashboard",
            "my_institute": "admin_dashboard",
            "teachers": "admin_teachers",
            "students": "admin_students",
            "classes_subjects": "admin_classes",
            "attendance": "teacher_attendance",
            "analytics": "admin_dashboard",
            "reports": "admin_dashboard",
            "settings": "founder_settings",
        }
        return admin_map.get(institute_page, "admin_dashboard")
    if role == "student":
        student_page = st.session_state.get("student_page", "dashboard")
        student_map = {
            "dashboard": "student_dashboard",
            "subjects": "student_subjects",
            "history": "student_history",
            "analytics": "student_reports",
            "reports": "student_reports",
            "faceid": "student_faceid",
            "profile": "student_dashboard",
        }
        return student_map.get(student_page, "student_dashboard")
    if role == "teacher":
        teacher_page = st.session_state.get("teacher_page", "dashboard")
        teacher_map = {
            "dashboard": "teacher_dashboard",
            "manual_att": "teacher_attendance",
            "ai_att": "teacher_attendance",
            "classes": "admin_classes",
            "students": "admin_students",
            "analytics": "teacher_reports",
            "reports": "teacher_reports",
        }
        return teacher_map.get(teacher_page, "teacher_dashboard")
    return page


_page_timer = time_block(f"current page render: app/{role or 'public'}/{page}")
_page_timer.__enter__()
try:
    # Supabase detection is handled lazily by src.database.client.
    # Do not touch st.secrets directly here so demo mode stays clean when
    # no secrets.toml is present.
    pass


    # ── PUBLIC
    if page == "landing":
        from src.screens.landing import show_landing

        show_landing()
    elif page == "about":
        from src.screens.about import show_about

        show_about()
    elif page == "features":
        from src.screens.features import show_features

        show_features()
    elif page == "pricing":
        from src.screens.pricing import show_pricing

        show_pricing()
    elif page == "demo_signup":
        from src.screens.demo_signup import show_demo_signup

        show_demo_signup()
    elif page == "payment_success":
        from src.screens.payment_success import show_payment_success

        show_payment_success()
    elif page == "payment_failed":
        from src.screens.payment_failed import show_payment_failed

        show_payment_failed()
    elif page == "payment":
        if role in {"institute_admin", "admin"}:
            from src.components.sidebar import institute_sidebar

            institute_sidebar()
        from src.screens.payment import show_payment

        show_payment()
    elif page == "admin_billing":
        from src.screens.admin_billing import show_admin_billing

        show_admin_billing()
    elif page == "contact":
        from src.screens.contact import show_contact

        show_contact()

    # ── AUTH
    elif page == "student_auth":
        enable_enter_to_next_input()
        from src.screens.auth import show_student_auth

        show_student_auth()
    elif page == "teacher_auth":
        enable_enter_to_next_input()
        from src.screens.auth import show_teacher_auth

        show_teacher_auth()
    elif page == "institute_login":
        enable_enter_to_next_input()
        from src.screens.institute_login import show_institute_login

        show_institute_login()
    elif page == "institute_join":
        enable_enter_to_next_input()
        from src.screens.institute_join import show_institute_join

        show_institute_join()
    elif page == "founder_auth":
        enable_enter_to_next_input()
        from src.screens.founder_auth import show_founder_auth

        show_founder_auth()

    # ── FOUNDER
    elif role == "founder":
        from src.components.sidebar import founder_sidebar
        founder_sidebar()
        fp = st.session_state.get("founder_page", "founder_dashboard")
        if fp == "founder_institutes":
            from src.screens.founder_institutes import render_founder_institutes

            render_founder_institutes()
        elif fp == "founder_codes":
            from src.screens.founder_codes import render_founder_generate_code

            render_founder_generate_code()
        elif fp == "founder_allcodes":
            from src.screens.founder_codes import render_founder_codes

            render_founder_codes()
        elif fp == "founder_plans":
            from src.screens.founder_plans import render_founder_plans

            render_founder_plans()
        elif fp == "founder_leads":
            from src.screens.founder_leads import render_founder_leads

            render_founder_leads()
        elif fp == "founder_reports":
            from src.screens.founder_reports import render_founder_reports

            render_founder_reports()
        elif fp == "founder_settings":
            from src.screens.founder_settings import render_founder_settings

            render_founder_settings()
        else:
            from src.screens.founder_dashboard import render_founder_dashboard

            render_founder_dashboard()


    # ── INSTITUTE SETUP (before dashboard)
    elif page == "institute_setup":
        from src.screens.institute_setup import show_institute_setup

        show_institute_setup()

    # ── INSTITUTE ADMIN
    elif role in {"institute_admin", "admin"}:
        from src.components.sidebar import institute_sidebar
        institute_sidebar()
        ip = st.session_state.get("institute_page", "institute_dashboard")
        from src.services.admin_context import get_current_institute_id
        from src.services.institute_service import get_institute_by_id
        from src.services.subscription_access import (
            can_access_admin_portal,
            get_current_subscription,
            render_billing_workspace,
            render_subscription_activation_popup,
        )

        institute_id = str(get_current_institute_id() or st.session_state.get("institute_id") or "")
        institute = st.session_state.get("current_institute") or {}
        if institute_id and (not institute or not institute.get("name")):
            loaded_institute = get_institute_by_id(institute_id)
            if loaded_institute:
                institute = loaded_institute
                st.session_state.current_institute = loaded_institute
        subscription = get_current_subscription(institute_id)
        pending_payment_locked = bool(institute_id and not can_access_admin_portal(institute, subscription))
        if pending_payment_locked:
            st.session_state.page = "payment"
            st.session_state.institute_page = "institute_dashboard"
            render_billing_workspace(institute, subscription)
        else:
            render_subscription_activation_popup()

        if ip == "my_institute":
            from src.screens.my_institute import show_my_institute

            show_my_institute()
        elif ip == "teachers":
            from src.screens.institute_teachers import show_teachers

            show_teachers()
        elif ip == "students":
            from src.screens.institute_students import show_students

            show_students()
        elif ip == "classes_subjects":
            from src.screens.institute_classes import show_classes_subjects

            show_classes_subjects()
        elif ip == "attendance":
            from src.screens.attendance import show_attendance

            show_attendance()
        elif ip == "analytics":
            from src.screens.analytics import show_analytics

            show_analytics()
        elif ip == "reports":
            st.markdown("### 📄 Reports")
            from src.screens.institute_reports import show_reports

            show_reports()
        elif ip == "settings":
            from src.screens.settings import show_settings

            show_settings()
        else:
            from src.screens.institute_dashboard import show_institute_dashboard

            show_institute_dashboard()

    # ── STUDENT
    elif role == "student":
        from src.screens.student_dashboard import show_student_portal

        show_student_portal()

    # ── TEACHER
    elif role == "teacher":
        from src.screens.teacher_dashboard import show_teacher_portal

        show_teacher_portal()

    # ── FALLBACK
    else:
        st.warning("Please login first.")
        if st.button("Go to Login", key="app_go_login"):
            st.session_state.page = "landing"
            st.rerun()
        st.stop()

except Exception as e:
    _page_timer.__exit__(type(e), e, e.__traceback__)
    st.error("The app hit an unexpected error. Please retry or contact support.")
    if perf_enabled():
        with st.expander("Developer Debug", expanded=False):
            st.code(traceback.format_exc(), language="python")
    st.stop()
else:
    _page_timer.__exit__(None, None, None)



# Render SnapBot globally on every page (must be outside all page conditions)
render_snapbot_floating(
    {
        "current_role": st.session_state.get("role") or st.session_state.get("user_role") or "public",
        "current_page": _snapbot_page_key(),
        "current_user_name": st.session_state.get("user_name") or st.session_state.get("name"),
        "last_error": st.session_state.get("last_error", ""),
    }
)
