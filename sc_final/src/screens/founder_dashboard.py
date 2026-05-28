"""SnapClass HQ founder dashboard."""
from __future__ import annotations

import streamlit as st

from src.services.institute_service import (
    count_active_institutes,
    count_codes,
    count_institutes,
    init_institute_state,
)
from src.utils.session import nav_founder


def render_founder_dashboard() -> None:
    """Render the SnapClass HQ overview screen."""
    init_institute_state()

    st.markdown("## SnapClass HQ")
    st.caption("Founder control center for institutes and access codes.")

    total_institutes = count_institutes()
    active_institutes = count_active_institutes()
    total_codes = count_codes()
    pending_codes = sum(
        1 for code in st.session_state.codes if code.get("status", "unused") == "unused"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Institutes", total_institutes)
    c2.metric("Active", active_institutes)
    c3.metric("Codes", total_codes)
    c4.metric("Pending Codes", pending_codes)

    st.divider()

    quick_left, quick_right = st.columns(2)
    with quick_left:
        if st.button("➕ Add Institute", use_container_width=True):
            nav_founder("founder_institutes")
    with quick_right:
        if st.button("🔑 View Codes", use_container_width=True):
            nav_founder("founder_codes")

    st.divider()
    st.subheader("Recent Institutes")

    def _get_founder_institutes():
        from src.database.client import get_supabase

        db = get_supabase()
        if db is None:
            return st.session_state.get("sc_institutes", [])

        try:
            # Try institutes table first
            data = db.table("institutes").select("*").execute().data or []
            if data:
                return data

            # Fallback to schools table (where the dashboard metrics come from)
            data = db.table("schools").select("*").execute().data or []
            return data
        except Exception:
            return st.session_state.get("sc_institutes", [])

    institutes = list(reversed(_get_founder_institutes()[-5:]))
    if not institutes:
        st.info("No institutes created yet.")
    for institute in institutes:
        st.markdown(
            f"""
            <div class="sc-subject-card">
              <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;">
                <div>
                  <h4 style="margin:0 0 4px;">{institute.get("name", "Unnamed Institute")}</h4>
                  <p style="margin:0;">{institute.get("city", "")} {institute.get("state", "")}</p>
                  <p style="margin:6px 0 0;">Admin: {institute.get("admin_name", "—")} ({institute.get("admin_email", "—")})</p>
                </div>
                <span class="sc-badge {'ok' if institute.get('status', 'active') == 'active' else 'danger'}">
                  {institute.get('status', 'active').title()}
                </span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    st.subheader("Recent Access Codes")
    codes = list(reversed(st.session_state.codes[-5:]))
    if not codes:
        st.info("No access codes generated yet.")
    for code in codes:
        institute = next(
            (item for item in st.session_state.institutes if item.get("id") == code.get("institute_id")),
            {},
        )
        st.markdown(
            f"""
            <div class="sc-subject-card">
              <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;">
                <div>
                  <h4 style="margin:0 0 4px;">{code.get("code", "—")}</h4>
                  <p style="margin:0;">Institute: {institute.get("name", "Unknown")}</p>
                  <p style="margin:6px 0 0;">Admin Email: {code.get("admin_email", "—")}</p>
                </div>
                <span class="sc-badge {'warn' if code.get('status', 'unused') == 'unused' else 'ok'}">
                  {code.get('status', 'unused').title()}
                </span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
