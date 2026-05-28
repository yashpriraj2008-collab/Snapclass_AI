"""Founder / SnapClass HQ auth screen."""
import streamlit as st
from src.components.public_nav import render_public_nav
from src.components.navigation import go_to

FOUNDER_EMAIL    = "founder@snapclass.ai"
FOUNDER_PASSWORD = "founder@123"

def show_founder_auth():
    render_public_nav(show_links=False)
    if st.button("← Back to Home", key="fa_back"): go_to("landing")
    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
        <div class="sc-card" style="text-align:center;padding:36px;margin-bottom:20px;">
          <div style="font-size:3rem;margin-bottom:12px;">⚡</div>
          <h2 style="margin:0 0 4px;">SnapClass HQ</h2>
          <p style="color:#6B7280;margin:0;">Founder / Super Admin access only</p>
        </div>""", unsafe_allow_html=True)
        email = st.text_input("Email",    placeholder="founder@snapclass.ai", key="fl_email")
        pwd   = st.text_input("Password", placeholder="••••••••", key="fl_pwd", type="password")
        st.caption("Default: founder@snapclass.ai / founder@123")
        if st.button("Access SnapClass HQ", type="primary", use_container_width=True, key="founder_go"):
            if email.strip() == FOUNDER_EMAIL and pwd == FOUNDER_PASSWORD:
                st.session_state.role             = "founder"
                st.session_state.user_name        = "Founder"
                st.session_state.founder_logged_in= True
                st.session_state.founder_page     = "founder_dashboard"
                st.session_state.page             = "founder_dashboard"
                st.rerun()
            else:
                st.error("Invalid credentials. Use: founder@snapclass.ai / founder@123")
