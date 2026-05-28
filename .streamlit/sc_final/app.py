"""SnapClass AI — Main router. Fully fixed."""
import os
import sys
import streamlit as st

from src.components.ui import load_css
from src.components.keyboard import enable_enter_to_next_input
from src.utils.session import init_session
from src.components.snapbot import render_snapbot_floating





root_dir = os.path.abspath(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

st.set_page_config(
    page_title="SnapClass AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css()

st.markdown(
    """
<style>

/* INPUT TEXT */
input, textarea {
    color: black !important;
    background-color: white !important;
}

/* SELECTBOX */
.stSelectbox div[data-baseweb="select"] {
    background: white !important;
    color: black !important;
}

/* LABELS */
label, p, span, div {
    color: #111827 !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
}

/* BUTTON */
.stButton button {
    border-radius: 12px !important;
    font-weight: 600 !important;
}

/* MAIN PAGE */
.main {
    background: #f5f7fb;
}

/* CARDS */
.block-container {
    padding-top: 1rem;
}

/* REMOVE DARK INPUT BORDER */
input {
    border: 1px solid #d1d5db !important;
}

/* SUCCESS BOX */
.stSuccess {
    border-radius: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)

init_session()

if st.query_params.get("reset") == "1":
    st.session_state.clear()

if "page" not in st.session_state:
    st.session_state.page = "landing"

page = st.session_state.get("page", "landing")
role = st.session_state.get("role")


def _go_home() -> None:
    st.session_state.page = "landing"
    st.rerun()


try:
    # Ensure secrets are loaded (do not crash app if secrets.toml is missing)
    try:
        _ = dict(st.secrets)
    except FileNotFoundError:
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
            from src.screens.founder_codes import render_founder_codes

            render_founder_codes()
        elif fp == "founder_plans":
            from src.screens.founder_plans import render_founder_plans

            render_founder_plans()
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
    elif role == "institute_admin":
        from src.components.sidebar import institute_sidebar

        institute_sidebar()
        ip = st.session_state.get("institute_page", "institute_dashboard")
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
            st.info("Reports are not implemented yet.")
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
        _go_home()

except Exception as exc:
    st.error(f"⚠️ App error: {exc}")
    import traceback

    with st.expander("Error details (for developer)"):
        st.code(traceback.format_exc())
    if st.button("🏠 Go to Home", key="err_home"):
        _go_home()


# Render SnapBot globally on every page (must be outside all page conditions)
render_snapbot_floating({
    "role": st.session_state.get("role") or st.session_state.get("user_role") or "user",
    "screen": st.session_state.get("page") or st.session_state.get("current_page") or "home",
    "user_name": st.session_state.get("user_name") or st.session_state.get("name"),
})



