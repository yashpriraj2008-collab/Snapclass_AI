"""Contact, support, and demo request page."""
from __future__ import annotations

import streamlit as st

from src.components.navigation import go_to
from src.components.public_nav import render_public_nav
from src.services.contact_service import INQUIRY_TYPES, STUDENT_COUNTS, submit_contact_message


def _submitted_recently(email: str, subject: str) -> bool:
    last = st.session_state.get("last_contact_submit") or {}
    return (
        str(last.get("email") or "").lower() == email.lower()
        and str(last.get("subject") or "") == subject
    )


def show_contact() -> None:
    render_public_nav(show_links=False)
    if st.button("<- Back to Home", key="contact_back"):
        go_to("landing")

    st.markdown(
        """
        <div style="max-width:720px;margin:32px auto 20px;text-align:center;">
          <h1 style="font-family:Poppins,sans-serif;">Contact Us</h1>
          <p style="color:#6B7280;">
            Book a demo, ask about pricing, or get help from the SnapClass AI team.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("contact_lead_form", clear_on_submit=False):
            name = st.text_input("Full Name *", placeholder="Naresh Kumar")
            institute_name = st.text_input(
                "Institute / School / Coaching Name",
                placeholder="Sunrise Coaching Centre",
            )
            c1, c2 = st.columns(2)
            email = c1.text_input("Email *", placeholder="you@school.com")
            phone = c2.text_input("Phone / WhatsApp *", placeholder="+91 98765 43210")

            inquiry_type = st.selectbox("Inquiry Type *", INQUIRY_TYPES, index=0)
            student_count = st.selectbox(
                "Number of students",
                ["Not sure"] + STUDENT_COUNTS,
                index=0,
            )
            preferred_contact = st.selectbox(
                "Preferred contact",
                ["WhatsApp", "Phone call", "Email"],
                index=0,
            )
            subject = st.text_input("Subject *", placeholder="I want to know about SnapClass AI")
            message = st.text_area(
                "Message *",
                placeholder="Tell us what you want to do with SnapClass AI.",
                height=130,
            )
            submitted = st.form_submit_button("Send Message", type="primary", use_container_width=True)

        if submitted:
            email_norm = email.strip().lower()
            if _submitted_recently(email_norm, subject.strip()):
                st.info("We already received this message. We'll get back to you within 24 hours.")
                return

            payload = {
                "name": name,
                "institute_name": institute_name,
                "email": email_norm,
                "phone": phone,
                "inquiry_type": inquiry_type,
                "student_count": student_count if student_count != "Not sure" else "",
                "subject": subject,
                "message": f"{message.strip()}\n\nPreferred contact: {preferred_contact}",
                "website": "",
            }
            result = submit_contact_message(payload)
            if result.get("ok"):
                st.session_state["last_contact_submit"] = {
                    "email": email_norm,
                    "subject": subject.strip(),
                }
                st.success(result.get("message", "Message sent! We'll get back to you within 24 hours."))
                email_status = result.get("email_notification") or {}
                if email_status and not email_status.get("ok"):
                    st.caption("Your message was saved. Email notification is not configured in this environment.")
            else:
                st.error(result.get("message", "Message could not be saved. Please email hello@snapclass.ai."))
                if result.get("debug"):
                    with st.expander("Developer Debug", expanded=False):
                        st.code(str(result.get("debug")))

        st.markdown(
            """
            <div style="text-align:center;margin-top:24px;color:#6B7280;">
              hello@snapclass.ai | +91 98765 43210
            </div>
            """,
            unsafe_allow_html=True,
        )
