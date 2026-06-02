"""Founder view for website contact messages and leads."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from src.services.contact_service import list_contact_messages, update_contact_status


def _date(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "-"
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%d %b %Y %H:%M")
    except Exception:
        return raw[:16] or "-"


def _status(status: Any) -> None:
    label = str(status or "new").strip().lower()
    if label == "new":
        st.warning("New")
    elif label == "contacted":
        st.info("Contacted")
    elif label == "closed":
        st.success("Closed")
    elif label == "spam":
        st.error("Spam")
    else:
        st.write(label.title())


def render_founder_leads() -> None:
    st.markdown("## Leads")
    st.caption("Contact messages, demo requests, pricing questions, and support inquiries.")

    result = list_contact_messages()
    if not result.get("ok"):
        st.warning(result.get("message", "Unable to load data. Please retry."))
        if result.get("debug"):
            with st.expander("Developer Debug", expanded=False):
                st.code(str(result.get("debug")))
        return

    messages = result.get("data") or []
    if not messages:
        st.info("No contact messages found.")
        return

    new_count = sum(1 for item in messages if str(item.get("status") or "new").lower() == "new")
    contacted_count = sum(1 for item in messages if str(item.get("status") or "").lower() == "contacted")
    closed_count = sum(1 for item in messages if str(item.get("status") or "").lower() == "closed")
    spam_count = sum(1 for item in messages if str(item.get("status") or "").lower() == "spam")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("New", new_count)
    c2.metric("Contacted", contacted_count)
    c3.metric("Closed", closed_count)
    c4.metric("Spam", spam_count)

    st.divider()

    for item in messages:
        message_id = str(item.get("id") or "")
        with st.container(border=True):
            top_left, top_right = st.columns([3, 1])
            with top_left:
                st.markdown(f"#### {item.get('name') or 'Unnamed lead'}")
                st.caption(_date(item.get("created_at")))
            with top_right:
                _status(item.get("status"))

            d1, d2, d3 = st.columns(3)
            d1.markdown(f"**Institute**  \n{item.get('institute_name') or '-'}")
            d2.markdown(f"**Inquiry type**  \n{item.get('inquiry_type') or '-'}")
            d3.markdown(f"**Students**  \n{item.get('student_count') or '-'}")

            c1, c2 = st.columns(2)
            c1.markdown(f"**Email**  \n{item.get('email') or '-'}")
            c2.markdown(f"**Phone / WhatsApp**  \n{item.get('phone') or '-'}")

            st.markdown(f"**Subject**  \n{item.get('subject') or '-'}")
            st.text_area(
                "Message",
                value=str(item.get("message") or ""),
                height=110,
                key=f"lead_message_{message_id}",
                disabled=True,
            )

            a1, a2, a3 = st.columns(3)
            if a1.button("Mark Contacted", key=f"lead_contacted_{message_id}", use_container_width=True):
                res = update_contact_status(message_id, "contacted")
                st.success(res["message"]) if res.get("ok") else st.warning(res.get("message", "Unable to update."))
                st.rerun()
            if a2.button("Mark Closed", key=f"lead_closed_{message_id}", use_container_width=True):
                res = update_contact_status(message_id, "closed")
                st.success(res["message"]) if res.get("ok") else st.warning(res.get("message", "Unable to update."))
                st.rerun()
            if a3.button("Mark Spam", key=f"lead_spam_{message_id}", use_container_width=True):
                res = update_contact_status(message_id, "spam")
                st.success(res["message"]) if res.get("ok") else st.warning(res.get("message", "Unable to update."))
                st.rerun()

