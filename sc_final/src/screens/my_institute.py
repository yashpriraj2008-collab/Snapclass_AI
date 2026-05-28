"""My Institute — view/edit own institute profile only."""

import streamlit as st

from src.services.institute_service import init_institute_state, update_institute


def show_my_institute() -> None:
    init_institute_state()

    inst = st.session_state.get("current_institute") or {}
    inst_id = st.session_state.get("active_institute_id", "")

    st.markdown("### 🏫 My Institute")
    st.caption("View and edit your institute profile. You can only manage your own institute.")

    if not inst and not inst_id:
        st.warning("No institute data found. Please log in again with your access code.")
        if st.button("← Go to Login"):
            st.session_state.page = "institute_login"
            st.rerun()
        return

    edit = st.toggle("✏️ Edit Mode", key="inst_edit_toggle")

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

        st.markdown('<div class="sc-card">', unsafe_allow_html=True)
        for label, val in rows:
            st.markdown(
                f"""
                <div style="display:flex;justify-content:space-between;padding:10px 0;
                        border-bottom:1px solid #F3F4F6;">
                  <span style="color:#6B7280;font-size:.88rem;">{label}</span>
                  <strong style="font-size:.9rem;">{val}</strong>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
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
                    st.session_state.get("active_institute_id")
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

