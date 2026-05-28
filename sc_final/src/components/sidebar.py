"""Sidebars for all portals."""
import streamlit as st
from src.utils.session import logout, nav_student, nav_teacher, nav_institute, nav_founder

def _brand(label="SnapClass AI", icon="S", gradient="linear-gradient(135deg,#5B6CFF,#FF4FA3)"):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:4px 0 20px;">
      <div style="width:36px;height:36px;border-radius:11px;background:{gradient};
        display:flex;align-items:center;justify-content:center;
        color:white;font-weight:900;font-size:.95rem;flex-shrink:0;">{icon}</div>
      <span style="font-weight:850;font-size:1.1rem;font-family:Poppins,sans-serif;">{label}</span>
    </div>""", unsafe_allow_html=True)

def _user_chip(name, role_label, initial=None):
    ini = (initial or name[:1] or "U").upper()
    st.markdown(f"""
    <div style="background:#F5F7FF;border-radius:12px;padding:10px 14px;
      margin-bottom:18px;display:flex;align-items:center;gap:10px;">
      <div style="width:36px;height:36px;border-radius:999px;
        background:linear-gradient(135deg,#5B6CFF,#FF4FA3);color:white;
        display:flex;align-items:center;justify-content:center;
        font-weight:900;font-size:.9rem;flex-shrink:0;">{ini}</div>
      <div style="overflow:hidden;">
        <div style="font-weight:700;font-size:.88rem;white-space:nowrap;
          overflow:hidden;text-overflow:ellipsis;">{name}</div>
        <div style="color:#6B7280;font-size:.75rem;">{role_label}</div>
      </div>
    </div>""", unsafe_allow_html=True)

def _section(title):
    st.markdown(f"""<div style="font-size:.7rem;font-weight:700;color:#9CA3AF;
      text-transform:uppercase;letter-spacing:.08em;padding:4px 6px;margin:10px 0 4px;">
      {title}</div>""", unsafe_allow_html=True)

def _nav_btn(label, key):
    return st.button(label, key=key, use_container_width=True)

# ── STUDENT ────────────────────────────────────────────────────────────────
def student_sidebar():
    with st.sidebar:
        _brand()
        name = st.session_state.get("user_name","") or "Student"
        name = name.replace(" Demo","").strip() or "Student"
        _user_chip(name, "Student")
        _section("MAIN")
        if _nav_btn("🏠  Dashboard",          "snav_dashboard"):  nav_student("dashboard")
        if _nav_btn("🪪  FaceID Attendance",  "snav_faceid"):     nav_student("faceid")
        if _nav_btn("📚  My Subjects",        "snav_subjects"):   nav_student("subjects")
        if _nav_btn("📋  Attendance History", "snav_history"):    nav_student("history")
        _section("INSIGHTS")
        if _nav_btn("📊  Analytics",  "snav_analytics"):  nav_student("analytics")
        if _nav_btn("📄  Reports",    "snav_reports"):    nav_student("reports")

        _section("ACCOUNT")
        if _nav_btn("👤  Profile",    "snav_profile"):    nav_student("profile")
        st.divider()
        if _nav_btn("🚪  Logout",     "student_logout"):  logout()

# ── TEACHER ────────────────────────────────────────────────────────────────
def teacher_sidebar():
    with st.sidebar:
        _brand()
        name = st.session_state.get("user_name","") or "Teacher"
        name = name.replace(" Demo","").strip() or "Teacher"
        _user_chip(name, "Teacher")
        _section("MAIN")
        if _nav_btn("🏠  Dashboard",        "tnav_dashboard"):  nav_teacher("dashboard")
        if _nav_btn("✏️  Manual Attendance", "tnav_manual"):    nav_teacher("manual_att")
        if _nav_btn("🤖  AI Attendance",    "tnav_ai"):         nav_teacher("ai_att")
        if _nav_btn("🏫  My Classes",       "tnav_classes"):    nav_teacher("classes")
        if _nav_btn("👥  Students",         "tnav_students"):   nav_teacher("students")
        _section("INSIGHTS")
        if _nav_btn("📊  Analytics", "tnav_analytics"): nav_teacher("analytics")
        if _nav_btn("📄  Reports",   "tnav_reports"):   nav_teacher("reports")
        st.divider()
        if _nav_btn("🚪  Logout", "teacher_logout"): logout()

# ── INSTITUTE ADMIN ────────────────────────────────────────────────────────
def institute_sidebar():
    with st.sidebar:
        _brand()
        name    = st.session_state.get("admin_name","") or st.session_state.get("user_name","Admin")
        inst_nm = st.session_state.get("active_institute_name","My Institute")
        _user_chip(name, inst_nm)
        _section("MAIN")
        if _nav_btn("🏠  Dashboard",           "inav_dash"):    nav_institute("institute_dashboard")
        if _nav_btn("🏫  My Institute",        "inav_myinst"):  nav_institute("my_institute")
        if _nav_btn("👩‍🏫  Teachers",          "inav_teach"):   nav_institute("teachers")
        if _nav_btn("👨‍🎓  Students",          "inav_stud"):    nav_institute("students")
        if _nav_btn("📚  Classes & Subjects",  "inav_cls"):     nav_institute("classes_subjects")
        if _nav_btn("✅  Attendance",          "inav_att"):     nav_institute("attendance")
        _section("INSIGHTS")
        if _nav_btn("📊  Analytics", "inav_analytics"): nav_institute("analytics")
        if _nav_btn("📄  Reports",   "inav_reports"):   nav_institute("reports")
        _section("SYSTEM")
        if _nav_btn("⚙️  Settings",  "inav_settings"):  nav_institute("settings")
        st.divider()
        if _nav_btn("🚪  Logout",    "inst_logout"):    logout()

# ── FOUNDER ────────────────────────────────────────────────────────────────
def founder_sidebar():
    with st.sidebar:
        _brand("SnapClass HQ","⚡","linear-gradient(135deg,#06B6D4,#3B82F6)")
        _user_chip("Founder","Super Admin","F")
        _section("SNAPCLASS HQ")
        if _nav_btn("🏠  Dashboard",    "fnav_dash"):   nav_founder("founder_dashboard")
        if _nav_btn("🏫  Institutes",   "fnav_inst"):   nav_founder("founder_institutes")
        if _nav_btn("🔑  Generate Code","fnav_codes"):  nav_founder("founder_codes")
        if _nav_btn("📋  All Codes",    "fnav_acodes"): nav_founder("founder_allcodes")
        if _nav_btn("💳  Plans",        "fnav_plans"):  nav_founder("founder_plans")
        if _nav_btn("📄  Reports",      "fnav_reps"):   nav_founder("founder_reports")
        if _nav_btn("⚙️  Settings",     "fnav_set"):    nav_founder("founder_settings")
        st.divider()
        if _nav_btn("🚪  Logout",       "founder_logout"): logout()

# SnapBot sidebar chat intentionally removed.
# Floating chatbot is rendered globally from app.py via render_floating_chatbot().

