"""Public navigation bar used on all public-facing pages."""
import streamlit as st
from src.components.navigation import go_to

def render_public_nav(show_links: bool = True) -> None:
    nav = st.columns([4,1,1,1,1], gap="small")
    with nav[0]:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:12px;background:white;
          border:1px solid #E5E7EB;border-radius:22px;padding:13px 20px;
          box-shadow:0 8px 24px rgba(31,41,55,.06);margin-bottom:8px;">
          <div style="width:40px;height:40px;border-radius:12px;
            background:linear-gradient(135deg,#5B6CFF,#FF4FA3);color:white;
            display:flex;align-items:center;justify-content:center;
            font-size:18px;font-weight:900;">S</div>
          <div style="font-size:19px;font-weight:850;color:#1F2937;">SnapClass AI</div>
        </div>""", unsafe_allow_html=True)
    if show_links:
        with nav[1]:
            if st.button("About",    key="pn_about",    use_container_width=True): go_to("about")
        with nav[2]:
            if st.button("Features", key="pn_features",  use_container_width=True): go_to("features")
        with nav[3]:
            if st.button("Pricing",  key="pn_pricing",   use_container_width=True): go_to("pricing")
        with nav[4]:
            if st.button("Contact",  key="pn_contact",   use_container_width=True): go_to("contact")
