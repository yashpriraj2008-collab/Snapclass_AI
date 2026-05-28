"""SnapClass HQ access-codes page."""
from __future__ import annotations

import streamlit as st

from src.services.institute_service import count_codes, init_institute_state, list_codes, list_institutes
from src.utils.session import nav_founder


def render_founder_codes() -> None:
    """Render the founder view for all generated institute access codes."""
    init_institute_state()

    st.markdown("## Founder • Codes")
    st.caption("Review all generated institute access codes.")

    total_codes = count_codes()
    unused_codes = sum(1 for item in list_codes() if item.get("status", "unused") == "unused")
    used_codes = sum(1 for item in list_codes() if item.get("status", "unused") == "used")
    expired_codes = sum(1 for item in list_codes() if item.get("status", "unused") == "expired")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Codes", total_codes)
    c2.metric("Unused", unused_codes)
    c3.metric("Used", used_codes)
    c4.metric("Expired", expired_codes)

    st.divider()

    institutes = list_institutes()
    institute_name_map = {
        item.get("id", ""): item.get("name", "Unknown Institute")
        for item in institutes
    }

    codes = list_codes()
    if not codes:
        st.info("No access codes generated yet.")
    else:
        for code in codes:
            institute_name = institute_name_map.get(code.get("institute_id", ""), "Unknown Institute")
            status = code.get("status", "unused")
            badge_class = "warn" if status == "unused" else ("ok" if status == "used" else "danger")
            expires_raw = code.get("expires_at", "—")
            try:
                from datetime import datetime

                expires = datetime.fromisoformat(
                    str(expires_raw).replace("+00:00", "")
                ).strftime("%d %b %Y")
            except Exception:
                # Fallback: just take first 10 chars (YYYY-MM-DD)
                try:
                    expires = str(expires_raw)[:10]
                except Exception:
                    expires = "—"

            st.markdown(
                f"""
                <div class="sc-subject-card">
                  <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;">
                    <div>
                      <h4 style="margin:0 0 4px;">{code.get("code", "—")}</h4>
                      <p style="margin:0;">Institute: {institute_name}</p>
                      <p style="margin:6px 0 0;">Admin Email: {code.get("admin_email", "—")}</p>
                      <p style="margin:6px 0 0;">Expires: {expires}</p>

                    </div>
                    <span class="sc-badge {badge_class}">{status.title()}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Copy Code", key=f"copy_founder_code_{code.get('code')}"):
                # Render code block; users can select and copy (Ctrl+C).
                st.code(code.get("code", ""), language=None)
                st.caption("Select the code above and copy it (Ctrl+C)")

    st.markdown("")
    if st.button("← Back to Dashboard"):
        nav_founder("founder_dashboard")

