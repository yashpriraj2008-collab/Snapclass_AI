"""Navigation helpers — used by all public pages."""
import streamlit as st

def go_to(page: str, role: str = None):
    st.session_state.page = page
    if role:
        st.session_state.role = role
    st.rerun()

def back_to_home():
    st.session_state.page = "landing"
    st.rerun()
