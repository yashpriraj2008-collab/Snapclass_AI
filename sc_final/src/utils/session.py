"""Session state management for all roles."""
import streamlit as st
from src.utils.user_guards import require_login

def init_session():
    defaults = {
        "page": "landing", "role": None,
        "user_name": "", "user_email": "", "user_roll": "",
        "institute_id": None, "active_institute_id": None,
        "active_institute_name": "", "active_school_code": "",
        "admin_onboarding_completed": False, "current_institute": None,
        "admin_name": "", "founder_logged_in": False,
        "student_page": "dashboard", "teacher_page": "dashboard",
        "institute_page": "institute_dashboard", "founder_page": "founder_dashboard",
        "attendance_saved": {}, "chat_history": [], "demo_mode": False,
        "snapbot_open": False, "snapbot_hist": [], "snapbot_msgs": [],
        "institutes": [], "school_codes": [], "teachers": [],
        "classes": [], "subjects": [], "students": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def go(page: str):
    st.session_state.page = page
    st.rerun()

def login(role: str, name: str, email: str = "",
          user_roll: str = "", institute_id=None, demo: bool = False, page: str = "dashboard"):
    st.session_state.role = role
    st.session_state.user_name = name.replace(" Demo","").strip()
    st.session_state.user_email = email
    st.session_state.user_roll = user_roll
    st.session_state.institute_id = institute_id
    st.session_state.active_institute_id = institute_id
    st.session_state.demo_mode = demo
    st.session_state.page = page
    st.rerun()

def logout():
    try:
        from src.database.client import get_supabase
        db = get_supabase()
        if db:
            try: db.auth.sign_out()
            except: pass
    except: pass
    # Clear ALL session state to prevent data leaking between users
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    # Re-init defaults
    init_session()
    st.session_state.page = "landing"
    st.rerun()

def nav_student(page: str):
    st.session_state.student_page = page
    st.rerun()

def nav_teacher(page: str):
    st.session_state.teacher_page = page
    st.rerun()

def nav_institute(page: str):
    st.session_state.institute_page = page
    st.rerun()

def nav_founder(page: str):
    st.session_state.founder_page = page
    st.rerun()

def check_route_access():
    if not st.session_state.get("role"):
        require_login()
        st.stop()
