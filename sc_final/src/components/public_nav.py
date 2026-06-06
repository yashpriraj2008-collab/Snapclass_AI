"""Public navigation bar used on all public-facing pages."""
import streamlit as st

from src.components.branding import render_brand_lockup
from src.components.navigation import go_to

def render_public_nav(show_links: bool = True) -> None:
    nav = st.columns([1.35, 0.7, 0.7, 0.7, 0.7], gap="small")
    with nav[0]:
        render_brand_lockup()
    if show_links:
        with nav[1]:
            if st.button("About",    key="pn_about",    use_container_width=True): go_to("about")
        with nav[2]:
            if st.button("Features", key="pn_features",  use_container_width=True): go_to("features")
        with nav[3]:
            if st.button("Pricing",  key="pn_pricing",   use_container_width=True): go_to("pricing")
        with nav[4]:
            if st.button("Contact",  key="pn_contact",   use_container_width=True): go_to("contact")
