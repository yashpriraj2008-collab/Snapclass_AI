"""Institute Admin login via institute access code."""
import streamlit as st
from src.services.institute_service import (
    init_institute_state, set_active_institute, validate_access_code,
)
from src.components.public_nav import render_public_nav
from src.components.navigation import go_to

def show_institute_login() -> None:
    init_institute_state()
    render_public_nav(show_links=False)
    if st.button("← Back to Home", key="il_back"): go_to("landing")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
        <div class="sc-card" style="text-align:center;padding:32px;margin-bottom:20px;">
          <div style="font-size:3rem;margin-bottom:10px;">🏫</div>
          <h2 style="margin:0 0 4px;">Institute Admin Access</h2>
          <p style="color:#6B7280;margin:0;">
            Enter your institute access code provided by SnapClass HQ
          </p>
        </div>""", unsafe_allow_html=True)

        with st.form("institute_admin_login_form"):
            admin_name  = st.text_input("Admin Name *",          placeholder="Priya Sharma")
            admin_email = st.text_input("Admin Email *",         placeholder="admin@institute.com")
            access_code = st.text_input("Institute Access Code *", placeholder="SC-SUNRISE-AB12")
            st.caption("Get this code from SnapClass HQ (Founder Panel)")
            submitted = st.form_submit_button("Continue →", type="primary", use_container_width=True)

            if submitted:
                if not admin_name or not admin_email or not access_code:
                    st.error("Please fill all fields.")
                    return
                # Normalize input code for matching.
                code = access_code.strip().upper().replace(" ", "")
                result = validate_access_code(code)

                if not result["ok"]:
                    st.error(result["message"])
                    return

                institute   = result["institute"]
                code_record = result["code"]
                set_active_institute(institute, code_value=code_record.get("code",""))

                st.session_state.admin_name  = admin_name
                st.session_state.admin_email = admin_email
                st.session_state.role        = "institute_admin"
                st.session_state.user_name   = admin_name
                st.session_state.user_email  = admin_email
                st.session_state.active_institute_id   = institute.get("id","")
                st.session_state.active_institute_name = institute.get("name","")
                st.session_state.current_institute     = institute
                st.session_state.admin_onboarding_completed = bool(
                    institute.get("onboarding_completed", False))

                if st.session_state.admin_onboarding_completed:
                    st.session_state.page          = "institute_dashboard"
                    st.session_state.institute_page= "institute_dashboard"
                else:
                    st.session_state.page = "institute_setup"
                st.rerun()

        st.markdown("---")
        st.caption("Are you the SnapClass Founder?")
        if st.button("→ SnapClass HQ Login", key="goto_founder"):
            go_to("founder_auth")
