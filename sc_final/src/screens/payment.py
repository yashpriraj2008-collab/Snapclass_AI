"""Pending payment page for paid institute subscriptions."""
from __future__ import annotations

import streamlit as st

from src.services.admin_context import get_current_institute_id
from src.services.institute_service import get_institute_by_id
from src.services.subscription_access import (
    can_access_admin_portal,
    get_current_subscription,
    render_billing_workspace,
)


def show_payment() -> None:
    institute_id = str(get_current_institute_id() or st.session_state.get("institute_id") or "")
    institute = st.session_state.get("current_institute") or {}
    if institute_id and (not institute or not institute.get("name")):
        institute = get_institute_by_id(institute_id) or institute
        if institute:
            st.session_state.current_institute = institute

    subscription = get_current_subscription(institute_id)
    if can_access_admin_portal(institute, subscription):
        st.success("Subscription active. Your admin dashboard is unlocked.")
        if st.button("Open Admin Dashboard", type="primary", use_container_width=True):
            st.session_state.page = "institute_dashboard"
            st.session_state.institute_page = "institute_dashboard"
            st.rerun()
        return

    render_billing_workspace(institute, subscription)
