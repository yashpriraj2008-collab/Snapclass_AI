"""SnapClass HQ access-codes page."""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.components.form_controls import format_institute_option, safe_selectbox
from src.services.institute_service import (
    count_codes,
    create_access_code,
    init_institute_state,
    list_codes,
    list_institutes,
)
from src.utils.session import nav_founder


def _format_expiry(expires_raw: object) -> str:
    """Return a compact display date while tolerating stored string formats."""
    try:
        return datetime.fromisoformat(str(expires_raw).replace("+00:00", "")).strftime("%d %b %Y")
    except Exception:
        try:
            return str(expires_raw)[:10]
        except Exception:
            return "-"


def _render_status(status: object) -> None:
    status_label = str(status or "unused").strip().lower()
    if status_label == "used":
        st.success("Used")
    elif status_label == "expired":
        st.error("Expired")
    else:
        st.warning("Unused")


def _invite_message(access_code: object) -> str:
    return (
        f"Hi, your SnapClass AI institute access code is {access_code}. "
        "Use this code to join your institute admin portal."
    )


def render_founder_generate_code() -> None:
    """Render the dedicated founder page for generating one access code."""
    init_institute_state()

    st.markdown("## Generate Access Code")
    st.caption("Create a new institute admin invite code.")

    institutes = list_institutes()
    if not institutes:
        st.info("No institutes found. Add an institute first.")
        if st.button("Add Institute", use_container_width=True):
            nav_founder("founder_institutes")
        return

    with st.form("founder_generate_access_code_form"):
        institute = safe_selectbox(
            "Institute",
            institutes,
            key="founder_generate_access_code_institute",
            format_func=format_institute_option,
            index=None,
            placeholder="Choose an institute",
            show_selected=False,
        )
        if institute:
            st.success(f"Selected Institute: {institute.get('name', 'Unnamed Institute')}")
        else:
            st.info("Select an institute to generate an access code.")
        admin_email = st.text_input(
            "Admin Email for Code",
            value=str((institute or {}).get("admin_email") or "").strip(),
            placeholder="admin@example.com",
        )
        expires_days = st.number_input("Code expiry days", min_value=1, max_value=365, value=30)
        submitted = st.form_submit_button("Generate Access Code", type="primary", use_container_width=True)

    if submitted:
        if not institute:
            st.warning("Select an institute to generate an access code.")
            return

        result = create_access_code(
            institute.get("id", ""),
            admin_email=admin_email,
            expires_days=int(expires_days),
        )
        if result.get("ok"):
            access_code = (result.get("data") or {}).get("code", "")
            st.success("Access code generated.")
            if access_code:
                st.text_input("Access Code", value=access_code, key="generated_access_code_copy")
                st.text_area(
                    "Copy Invite Message",
                    value=_invite_message(access_code),
                    height=88,
                    key="generated_invite_message_copy",
                )
        else:
            st.error(result.get("message", "Unable to generate access code. Please retry."))
            if result.get("error") or result.get("debug"):
                with st.expander("Developer Debug", expanded=False):
                    st.code(str(result.get("debug") or result.get("error")))

    st.divider()
    st.subheader("Recent Codes")
    recent_codes = list_codes()[:5]
    if not recent_codes:
        st.info("No codes found.")
    else:
        institutes_by_id = {item.get("id", ""): item.get("name", "Unknown Institute") for item in institutes}
        for code in recent_codes:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.markdown(f"**{code.get('code', '-')}**")
                c2.write(institutes_by_id.get(code.get("institute_id", ""), "Unknown Institute"))
                with c3:
                    _render_status(code.get("status", "unused"))


def render_founder_codes() -> None:
    """Render the founder view for all generated institute access codes."""
    init_institute_state()

    st.markdown("## Founder - Codes")
    st.caption("Review all generated institute access codes.")

    codes = list_codes()
    total_codes = count_codes()
    unused_codes = sum(1 for item in codes if item.get("status", "unused") == "unused")
    used_codes = sum(1 for item in codes if item.get("status", "unused") == "used")
    expired_codes = sum(1 for item in codes if item.get("status", "unused") == "expired")

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

    if not codes:
        st.info("No codes found.")
    else:
        for item in codes:
            access_code = item.get("code", "-")
            institute_name = institute_name_map.get(item.get("institute_id", ""), "Unknown Institute")
            admin_email = item.get("admin_email", "-")
            expires = _format_expiry(item.get("expires_at", "-"))
            invite_message = (
                _invite_message(access_code)
            )

            with st.container(border=True):
                top_left, top_right = st.columns([3, 1])
                with top_left:
                    st.markdown(f"#### {access_code}")
                    st.caption("Access Code")
                with top_right:
                    st.caption("Status")
                    _render_status(item.get("status", "unused"))

                d1, d2, d3 = st.columns(3)
                d1.markdown(f"**Institute**  \n{institute_name}")
                d2.markdown(f"**Admin Email**  \n{admin_email}")
                d3.markdown(f"**Expires**  \n{expires}")

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Copy Code", key=f"copy_founder_code_{access_code}"):
                        st.text_input(
                            "Copy code",
                            value=access_code,
                            key=f"copy_founder_code_text_{access_code}",
                        )
                        st.caption("Select the code above and copy it.")
                with b2:
                    if st.button("Copy Invite Message", key=f"copy_founder_invite_{access_code}"):
                        st.text_area(
                            "Copy invite message",
                            value=invite_message,
                            height=88,
                            key=f"copy_founder_invite_text_{access_code}",
                        )
                        st.caption("Select the invite message above and copy it.")

    st.markdown("")
    if st.button("<- Back to Dashboard"):
        nav_founder("founder_dashboard")
