"""Institute Admin — Settings."""

from __future__ import annotations

import streamlit as st

from src.components.avatar import render_profile_photo_section
from src.services.admin_context import get_current_institute_id
from src.services.institute_service import init_institute_state, _db
from src.services.profile_photo_service import fetch_user_profile


def _db_safe():
    try:
        return _db()
    except Exception:
        return None


def show_settings():
    init_institute_state()
    st.markdown("### ⚙️ Settings")

    inst_id = get_current_institute_id()
    db = _db_safe()

    if not inst_id:
        st.warning("Please log in again with your institute admin account.")
        return

    inst = st.session_state.get("current_institute") or {}

    # If current_institute isn't populated, fetch minimal fields from DB.
    if db and not inst:
        try:
            rows = db.table("institutes").select("*").eq("id", inst_id).limit(1).execute().data or []
            if rows:
                inst = rows[0]
        except Exception:
            pass

    email_value = str(
        st.session_state.get("user_email")
        or st.session_state.get("email")
        or inst.get("admin_email")
        or ""
    ).strip().lower()
    profile = fetch_user_profile(db, email_value)
    admin_name = (
        profile.get("full_name")
        or inst.get("admin_name")
        or st.session_state.get("admin_name")
        or "Admin"
    )
    admin_user = {
        **profile,
        "name": admin_name,
        "full_name": admin_name,
        "email": profile.get("email") or email_value,
        "role": profile.get("role") or "institute_admin",
        "profile_photo_url": profile.get("profile_photo_url") or "",
    }
    if db:
        render_profile_photo_section(db, admin_user, key_prefix="admin_profile")

    name = st.text_input("Institute Name", value=inst.get("name", ""))
    thr = st.slider(
        "Attendance threshold (%)", 50, 100, int(inst.get("attendance_threshold", 75)), 1
    )
    acyr = st.text_input("Academic year", value=str(inst.get("academic_year", "")))
    phone = st.text_input("Admin phone", value=inst.get("admin_phone", ""))
    email = st.text_input("Admin email", value=inst.get("admin_email", ""))

    if st.button("💾 Save settings", type="primary", use_container_width=True):
        updates = {
            "name": name.strip(),
            "attendance_threshold": thr,
            "academic_year": acyr.strip(),
            "admin_phone": phone.strip(),
            "admin_email": email.strip(),
        }

        if not db:
            st.warning("Supabase not connected. Settings not saved.")
            return

        try:
            db.table("institutes").update(updates).eq("id", inst_id).execute()
            st.success("Settings saved.")

            # keep session in sync
            st.session_state.current_institute = {**inst, **updates}
            st.session_state.active_institute_name = updates.get(
                "name", st.session_state.active_institute_name
            )
        except Exception as e:
            st.warning(f"Supabase update failed. Settings not saved. Details: {e}")
