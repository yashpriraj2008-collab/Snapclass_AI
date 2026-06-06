"""Contact, support, and demo request page."""
from __future__ import annotations

import os

import streamlit as st

from src.components.navigation import go_to
from src.components.public_nav import render_public_nav
from src.database.client import read_app_secrets
from src.services.contact_service import INQUIRY_TYPES, STUDENT_COUNTS, submit_contact_message


def _init_contact_state() -> None:
    st.session_state.setdefault("show_contact_success", False)
    st.session_state.setdefault("contact_success_toast_pending", False)
    st.session_state.setdefault("contact_success_note", "")
    st.session_state.setdefault("contact_form_instance", 0)


def _debug_enabled() -> bool:
    if bool(st.session_state.get("debug_mode")):
        return True
    app_env = str(os.getenv("APP_ENV") or read_app_secrets().get("APP_ENV") or "production").strip().lower()
    return app_env == "development"


def _submitted_recently(email: str, subject: str) -> bool:
    last = st.session_state.get("last_contact_submit") or {}
    return (
        str(last.get("email") or "").lower() == email.lower()
        and str(last.get("subject") or "") == subject
    )


def _render_contact_header() -> None:
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


def _inject_contact_css() -> None:
    st.markdown(
        """
        <style>
        .stTextInput input,
        .stTextArea textarea,
        [data-baseweb="select"] div,
        [data-baseweb="select"] span {
            color: #111827 !important;
        }

        [data-baseweb="select"] svg {
            color: #111827 !important;
            fill: #111827 !important;
        }

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: #9ca3af !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_contact_success_card() -> None:
    st.html(
        """
        <div style="
            max-width: 720px;
            margin: 28px auto 20px auto;
            background: #ffffff;
            border: 1px solid #d1fae5;
            border-radius: 24px;
            padding: 32px;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            text-align: center;
        ">
            <div style="
                width: 64px;
                height: 64px;
                margin: 0 auto 16px auto;
                border-radius: 20px;
                background: #dcfce7;
                color: #16a34a;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 34px;
                font-weight: 900;
            ">&#10003;</div>

            <h2 style="
                font-size: 30px;
                font-weight: 800;
                color: #111827;
                margin: 0 0 10px 0;
            ">Message Sent Successfully</h2>

            <p style="
                font-size: 17px;
                color: #4b5563;
                line-height: 1.6;
                margin: 0 0 18px 0;
            ">
                Thanks for contacting SnapClass AI. We will get back to you within 24 hours.
            </p>

            <div style="
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                padding: 16px;
                color: #374151;
                font-size: 15px;
            ">
                Your enquiry has been saved. Our team can contact you by email or phone.
            </div>
        </div>
        """
    )


def _render_success_actions() -> None:
    note = str(st.session_state.get("contact_success_note") or "").strip()
    if note:
        st.caption(note)

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        if st.button("Back to Home", key="contact_success_home", use_container_width=True):
            st.session_state.show_contact_success = False
            st.session_state.page = "landing"
            st.rerun()
    with c2:
        if st.button("View Plans", key="contact_success_pricing", type="primary", use_container_width=True):
            st.session_state.show_contact_success = False
            st.session_state.page = "pricing"
            st.rerun()
    with c3:
        if st.button("Send Another Message", key="contact_success_another", use_container_width=True):
            st.session_state.show_contact_success = False
            st.session_state.contact_success_note = ""
            st.session_state.contact_form_instance = int(st.session_state.get("contact_form_instance", 0)) + 1
            st.rerun()


def _render_contact_form() -> None:
    form_id = int(st.session_state.get("contact_form_instance", 0))
    with st.form(f"contact_lead_form_{form_id}", clear_on_submit=False):
        name = st.text_input("Full Name *", placeholder="Naresh Kumar", key=f"contact_name_{form_id}")
        institute_name = st.text_input(
            "Institute / School / Coaching Name",
            placeholder="Sunrise Coaching Centre",
            key=f"contact_institute_{form_id}",
        )
        c1, c2 = st.columns(2)
        email = c1.text_input("Email *", placeholder="you@school.com", key=f"contact_email_{form_id}")
        phone = c2.text_input("Phone / WhatsApp *", placeholder="+91 98765 43210", key=f"contact_phone_{form_id}")

        inquiry_type = st.selectbox("Inquiry Type *", INQUIRY_TYPES, index=0, key=f"contact_inquiry_{form_id}")
        student_count = st.selectbox(
            "Number of students",
            ["Not sure"] + STUDENT_COUNTS,
            index=0,
            key=f"contact_students_{form_id}",
        )
        preferred_contact = st.selectbox(
            "Preferred contact",
            ["WhatsApp", "Phone call", "Email"],
            index=0,
            key=f"contact_preferred_{form_id}",
        )
        subject = st.text_input(
            "Subject *",
            placeholder="I want to know about SnapClass AI",
            key=f"contact_subject_{form_id}",
        )
        message = st.text_area(
            "Message *",
            placeholder="Tell us what you want to do with SnapClass AI.",
            height=130,
            key=f"contact_message_{form_id}",
        )
        submitted = st.form_submit_button("Send Message", type="primary", use_container_width=True)

    if not submitted:
        return

    email_norm = email.strip().lower()
    subject_norm = subject.strip()
    if _submitted_recently(email_norm, subject_norm):
        st.session_state.show_contact_success = True
        st.session_state.contact_success_note = "We already received this message. We'll get back to you within 24 hours."
        st.session_state.contact_success_toast_pending = True
        st.rerun()

    payload = {
        "full_name": name,
        "institute_name": institute_name,
        "email": email_norm,
        "phone": phone,
        "role": "Other",
        "preferred_contact": preferred_contact,
        "inquiry_type": inquiry_type,
        "student_count": student_count if student_count != "Not sure" else "",
        "subject": subject_norm,
        "message": message.strip(),
        "website": "",
        "status": "new",
        "source": "landing_contact_form",
    }

    result = submit_contact_message(payload)
    if result.get("ok"):
        st.session_state["last_contact_submit"] = {
            "email": email_norm,
            "subject": subject_norm,
        }
        email_status = result.get("email_notification") or {}
        st.session_state.contact_success_note = (
            "Your message was saved. Email notification is not configured in this environment."
            if email_status and not email_status.get("ok")
            else ""
        )
        st.session_state.show_contact_success = True
        st.session_state.contact_success_toast_pending = True
        st.rerun()

    st.error(result.get("message", "Message could not be saved. Please email hello@snapclass.ai."))
    if _debug_enabled() and result.get("debug"):
        with st.expander("Developer Debug", expanded=False):
            st.code(str(result.get("debug")))


def show_contact() -> None:
    _init_contact_state()
    render_public_nav(show_links=False)
    if st.button("<- Back to Home", key="contact_back"):
        go_to("landing")

    if st.session_state.get("contact_success_toast_pending"):
        st.toast("Message sent successfully!", icon="✅")
        st.session_state.contact_success_toast_pending = False

    _render_contact_header()
    _inject_contact_css()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.get("show_contact_success"):
            render_contact_success_card()
            _render_success_actions()
        else:
            _render_contact_form()

        st.markdown(
            """
            <div style="text-align:center;margin-top:24px;color:#6B7280;">
              hello@snapclass.ai | +91 98765 43210
            </div>
            """,
            unsafe_allow_html=True,
        )
