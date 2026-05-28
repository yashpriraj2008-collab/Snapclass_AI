"""Contact page."""
import streamlit as st
from src.components.public_nav import render_public_nav
from src.components.navigation import go_to

def show_contact():
    render_public_nav(show_links=False)
    if st.button("← Back to Home", key="contact_back"): go_to("landing")
    st.markdown("""
    <div style="max-width:600px;margin:40px auto;text-align:center;">
      <h1 style="font-family:Poppins,sans-serif;">Contact Us</h1>
      <p style="color:#6B7280;">We'd love to hear from you. Reach out for demos, pricing, or support.</p>
    </div>""", unsafe_allow_html=True)

    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        name    = st.text_input("Your Name",    placeholder="Yashraj Mehta")
        email   = st.text_input("Email",         placeholder="you@school.com")
        subject = st.text_input("Subject",       placeholder="I want to know about SnapClass AI")
        message = st.text_area("Message",        placeholder="Tell us about your institute…", height=120)
        if st.button("Send Message", type="primary", use_container_width=True, key="contact_send"):
            if name and email and message:
                st.success("✅ Message sent! We'll get back to you within 24 hours.")
            else:
                st.error("Please fill Name, Email, and Message.")

        st.markdown("""
        <div style="text-align:center;margin-top:24px;color:#6B7280;">
          📧 hello@snapclass.ai &nbsp;|&nbsp; 📞 +91 98765 43210
        </div>""", unsafe_allow_html=True)
