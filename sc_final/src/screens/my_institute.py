"""My Institute — view/edit own institute profile only."""

import html
import streamlit as st

from src.services.admin_context import get_current_institute_id
from src.services.institute_service import _db, get_institute_by_id, init_institute_state, update_institute
from src.services.profile_photo_service import upload_institute_logo, validate_profile_photo


def show_my_institute() -> None:
    init_institute_state()

    inst = st.session_state.get("current_institute") or {}
    inst_id = get_current_institute_id()
    if inst_id and (not inst or not inst.get("name")):
        loaded = get_institute_by_id(inst_id)
        if loaded:
            inst = loaded
            st.session_state["current_institute"] = loaded

    st.markdown("### 🏫 My Institute")
    st.caption("View and edit your institute profile. You can only manage your own institute.")

    if not inst and not inst_id:
        st.warning("No institute data found. Please log in again with your access code.")
        if st.button("← Go to Login"):
            st.session_state.page = "institute_login"
            st.rerun()
        return

    if not inst:
        st.info("Institute profile not found. Please create or complete your institute profile first.")
        return

    st.markdown(
        """
        <style>
        .institute-logo-preview {
            width: 100%;
            min-height: 170px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 18px;
            border: 1px solid #E5E7EB;
            border-radius: 18px;
            background: #FFFFFF;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }
        .institute-logo-preview img,
        .institute-logo-fallback {
            width: 120px;
            height: 120px;
            border-radius: 24px;
        }
        .institute-logo-preview img {
            display: block;
            object-fit: contain;
        }
        .institute-logo-fallback {
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #4F46E5, #06B6D4);
            color: #FFFFFF;
            font-size: 38px;
            font-weight: 900;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    edit = st.toggle(":material/edit: Edit Mode", key="inst_edit_toggle")

    st.markdown("#### Institute Logo")
    logo_col, upload_col = st.columns([0.35, 1], gap="large")
    with logo_col:
        if inst.get("logo_url"):
            logo_url = html.escape(str(inst.get("logo_url")), quote=True)
            logo_markup = f'<img src="{logo_url}" alt="Institute logo">'
        else:
            initial = html.escape(str(inst.get("name") or "I")[:1].upper())
            logo_markup = f'<div class="institute-logo-fallback">{initial}</div>'
        st.markdown(
            f'<div class="institute-logo-preview">{logo_markup}</div>',
            unsafe_allow_html=True,
        )
    with upload_col:
        st.caption("Upload a JPG or PNG logo up to 2 MB.")
        logo_file = st.file_uploader(
            "Upload institute logo",
            type=["png", "jpg", "jpeg"],
            key="institute_logo_upload",
        )
        if st.button("Update Institute Logo", type="primary", key="institute_logo_update"):
            valid, message = validate_profile_photo(logo_file)
            if not valid:
                st.warning(message)
            else:
                try:
                    db = _db()
                    logo_url = upload_institute_logo(db, logo_file, str(inst_id))
                    if not logo_url:
                        raise RuntimeError("No public logo URL returned.")
                    db.table("institutes").update({"logo_url": logo_url}).eq("id", inst_id).execute()
                    inst = {**inst, "logo_url": logo_url}
                    st.session_state["current_institute"] = inst
                    st.success("Institute logo updated.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception:
                    st.error(
                        "Logo upload failed. Confirm the profile-photos bucket and database migration are configured."
                    )

    if not edit:
        rows = [
            ("Institute Name", inst.get("name", "—")),
            ("Type", inst.get("institute_type", "—")),
            ("City", inst.get("city", "—")),
            ("State", inst.get("state", "—")),
            ("Address", inst.get("address", "—")),
            ("Admin Name", inst.get("admin_name", "—")),
            ("Admin Email", inst.get("admin_email", "—")),
            ("Admin Phone", inst.get("admin_phone", "—")),
            ("Academic Year", inst.get("academic_year", "—")),
            ("Att. Threshold", f"{inst.get('attendance_threshold', 75)}%"),
            ("Plan", inst.get("plan", "Demo")),
            ("Status", inst.get("status", "active")),
        ]

        if any(str(val or "").strip() not in {"", "-", "â€”"} for _, val in rows):
            row_markup = "".join(
                (
                    '<div style="display:flex;justify-content:space-between;gap:24px;'
                    'padding:10px 0;border-bottom:1px solid #F3F4F6;">'
                    f'<span style="color:#6B7280;font-size:.88rem;">{html.escape(label)}</span>'
                    f'<strong style="font-size:.9rem;text-align:right;">'
                    f'{html.escape(str(val if val is not None else "—"))}</strong>'
                    "</div>"
                )
                for label, val in rows
            )
            st.markdown(
                f'<div class="sc-card">{row_markup}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Institute profile not found. Please switch to Edit Mode and complete the profile.")
    else:
        with st.form("edit_inst_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Institute Name", value=inst.get("name", ""))
            itype = c2.selectbox(
                "Type",
                ["School", "Coaching", "Tuition", "College"],
                index=["School", "Coaching", "Tuition", "College"].index(
                    inst.get("institute_type", "School")
                ),
            )

            c3, c4 = st.columns(2)
            city = c3.text_input("City", value=inst.get("city", ""))
            state = c4.text_input("State", value=inst.get("state", ""))

            address = st.text_area(
                "Address", value=inst.get("address", ""), height=70
            )

            c5, c6 = st.columns(2)
            phone = c5.text_input("Admin Phone", value=inst.get("admin_phone", ""))
            acyr = c6.text_input("Academic Year", value=inst.get("academic_year", ""))

            thr = st.slider(
                "Attendance Threshold (%)",
                50,
                100,
                int(inst.get("attendance_threshold", 75)),
                1,
            )

            if st.form_submit_button("💾 Save Changes", type="primary"):
                updates = {
                    "name": name,
                    "institute_type": itype,
                    "city": city,
                    "state": state,
                    "address": address,
                    "admin_phone": phone,
                    "academic_year": acyr,
                    "attendance_threshold": thr,
                }

                inst_id = (
                    get_current_institute_id()
                    or (st.session_state.get("current_institute") or {}).get("id")
                    or ""
                )

                if not inst_id:
                    st.error(
                        "❌ No institute_id found in session. Log out and log in again with your access code."
                    )
                    return

                result = update_institute(inst_id, updates)
                if result.get("ok"):
                    st.success(result["message"])
                    if result.get("demo"):
                        st.warning(
                            "⚠️ This was saved to session only, NOT Supabase. See message above."
                        )
                else:
                    st.error(result["message"])
