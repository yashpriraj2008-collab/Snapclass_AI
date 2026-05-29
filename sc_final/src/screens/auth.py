"""Auth screens — Student, Teacher login/register."""
import streamlit as st
from src.components.ui import navbar
from src.services.auth_service import verify_student, verify_teacher, register_user, login_user
from src.utils.session import login, go

def _back():
    if st.button("← Back to Home", key="back_home"): go("landing")

def _supabase_note():
    from src.database.client import get_supabase
    if get_supabase() is None:
        st.markdown('''<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;
            padding:8px 14px;margin-bottom:14px;font-size:.82rem;color:#1D4ED8;">
          🔵 <strong>Supabase unavailable</strong> — running in local demo mode.
        </div>''', unsafe_allow_html=True)

def show_auth(role_hint: str = "student"):
    """Compatibility wrapper called by old app.py."""
    if role_hint == "teacher":
        show_teacher_auth()
    else:
        show_student_auth()

def show_student_auth():
    navbar(show_links=False); _back(); _supabase_note()
    st.markdown("<div style='max-width:480px;margin:0 auto;'>", unsafe_allow_html=True)
    st.markdown('''<div class="sc-card" style="text-align:center;padding:32px;margin-bottom:20px;">
      <div style="font-size:3rem;margin-bottom:10px;">👨‍🎓</div>
      <h2 style="margin:0 0 4px;">Student Portal</h2>
      <p style="color:#6B7280;margin:0;">Sign in or create your account</p>
    </div>''', unsafe_allow_html=True)

    tab_in, tab_reg = st.tabs(["🔑 Sign In","📝 Register"])

    with tab_in:
        email = st.text_input("Email",    key="sl_email", placeholder="you@email.com")
        pwd   = st.text_input("Password", key="sl_pass",  type="password", placeholder="••••••••")
        if st.button("Sign In", key="sl_submit", type="primary", use_container_width=True):
            if not email or not pwd:
                st.error("Please enter email and password.")
            else:
                from src.database.client import get_supabase
                if get_supabase() is None:
                    # Demo fallback
                    login("student", email.split("@")[0].title(), email,
                          user_roll="SC001", page="dashboard")
                else:
                    user = verify_student(email, pwd)
                    if user:
                        if user.get("student_id"):
                            st.session_state["student_id"] = str(user.get("student_id"))
                        if user.get("roll"):
                            st.session_state["roll_no"] = str(user.get("roll"))
                        login("student",
                              user.get("name", email.split("@")[0].title()),
                              user.get("email", email),
                              user_roll=user.get("roll", ""),
                              page="dashboard")
                    else:
                        st.error("Login failed. Check email/password and make sure this account is a student.")

    with tab_reg:
        full_name = st.text_input("Full Name *", key="sr_full_name", placeholder="Your Name")
        email = st.text_input("Email *", key="sr_email", placeholder="you@email.com")
        roll = st.text_input("Roll Number *", key="sr_roll", placeholder="SC001")
        pwd = st.text_input("Password *", key="sr_password", type="password", placeholder="Min 6 chars")

        if st.button("Create Account", key="sr_submit", type="primary", use_container_width=True):
            full_name = (full_name or "").strip()
            email = (email or "").strip()
            roll = (roll or "").strip()
            pwd = (pwd or "").strip()

            missing = []
            if not full_name:
                missing.append("Full Name")
            if not email:
                missing.append("Email")
            if not pwd:
                missing.append("Password")
            if not roll:
                missing.append("Roll Number")

            if missing:
                st.error("Please fill: " + ", ".join(missing))
                return

            if len(pwd) < 6:
                st.error("Password must be at least 6 characters.")
                return

            from src.database.client import get_supabase
            if get_supabase() is None:
                st.info("🟢 Supabase unavailable — running in local demo mode. No user was saved.")
            else:
                r = register_user(
                    email=email,
                    password=pwd,
                    name=full_name,
                    role="student",
                    extra_profile={"roll": roll, "class_name": ""},
                )
                if r.get("ok"):
                    st.success("✅ Account created! Please sign in.")
                else:
                    st.error(r.get("message", "Registration failed."))
    st.markdown("</div>", unsafe_allow_html=True)


def show_teacher_auth():
    navbar(show_links=False); _back(); _supabase_note()
    st.markdown("<div style='max-width:480px;margin:0 auto;'>", unsafe_allow_html=True)
    st.markdown('''<div class="sc-card" style="text-align:center;padding:32px;margin-bottom:20px;">
      <div style="font-size:3rem;margin-bottom:10px;">👩‍🏫</div>
      <h2 style="margin:0 0 4px;">Teacher Portal</h2>
      <p style="color:#6B7280;margin:0;">Sign in or create your account</p>
    </div>''', unsafe_allow_html=True)

    tab_in, tab_reg = st.tabs(["🔑 Sign In","📝 Register"])

    with tab_in:
        email = st.text_input("Email",    key="tl_email", placeholder="teacher@school.com")
        pwd   = st.text_input("Password", key="tl_pass",  type="password", placeholder="••••••••")
        if st.button("Sign In", key="tl_submit", type="primary", use_container_width=True):
            if not email or not pwd:
                st.error("Please enter email and password.")
            else:
                from src.database.client import get_supabase
                if get_supabase() is None:
                    login("teacher", email.split("@")[0].title(), email, page="dashboard")
                else:
                    user = verify_teacher(email, pwd)
                    if user:
                        if user.get("user_id"):
                            st.session_state["user_id"] = str(user.get("user_id"))
                            st.session_state["teacher_id"] = str(user.get("user_id"))
                        login("teacher",
                              user.get("name", email.split("@")[0].title()),
                              user.get("email", email), page="dashboard")
                    else:
                        st.error("Login failed. Check email/password and make sure this account is a teacher.")

    with tab_reg:
        full_name = st.text_input("Full Name *", key="tr_full_name", placeholder="Dr. Sharma")
        email = st.text_input("Email *", key="tr_email", placeholder="teacher@school.com")
        subject = st.text_input("Subject", key="tr_subject", placeholder="Mathematics")
        pwd = st.text_input("Password *", key="tr_password", type="password")

        if st.button("Create Account", key="tr_submit", type="primary", use_container_width=True):
            full_name = (full_name or "").strip()
            email = (email or "").strip()
            pwd = (pwd or "").strip()

            missing = []
            if not full_name:
                missing.append("Full Name")
            if not email:
                missing.append("Email")
            if not pwd:
                missing.append("Password")

            if missing:
                st.error("Please fill: " + ", ".join(missing))
                return

            if len(pwd) < 6:
                st.error("Min 6 characters.")
                return

            from src.database.client import get_supabase
            if get_supabase() is None:
                st.info("🟢 Supabase unavailable — running in local demo mode. No user was saved.")
            else:
                r = register_user(
                    email=email,
                    password=pwd,
                    name=full_name,
                    role="teacher",
                    extra_profile={"subject": subject},
                )
                if r.get("ok"):
                    st.success("✅ Account created! Please sign in.")
                else:
                    st.error(r.get("message", "Registration failed."))
    st.markdown("</div>", unsafe_allow_html=True)


def show_admin_auth():
    from src.screens.institute_login import show_institute_login
    show_institute_login()
