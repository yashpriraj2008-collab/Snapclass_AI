"""SnapClass HQ institutes management page."""
from __future__ import annotations

import streamlit as st

from src.services.institute_service import (
    activate_institute,
    count_codes,
    count_institutes,
    create_access_code,
    create_institute_with_code,
    deactivate_institute,
    init_institute_state,
    list_institutes,
)



from src.utils.session import nav_founder


def render_founder_institutes() -> None:
    """Render the institute management page for SnapClass HQ."""
    init_institute_state()

    st.markdown("## Founder • Institutes")
    st.caption("Create institutes, manage status, and generate access codes.")

    total_institutes = count_institutes()
    total_codes = count_codes()
    active_institutes = sum(1 for item in list_institutes() if item.get("status", "active") == "active")
    disabled_institutes = max(total_institutes - active_institutes, 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Institutes", total_institutes)
    c2.metric("Active", active_institutes)
    c3.metric("Disabled", disabled_institutes)
    c4.metric("Codes", total_codes)

    st.divider()

    if st.button("← Back to Dashboard", use_container_width=True, key="founder_institutes_back"):
        nav_founder("founder_dashboard")

    st.divider()

    with st.expander("➕ Add New Institute", expanded=True):
        institute_types = ["School", "Coaching", "Tuition", "College"]
        plans = ["Free Demo", "Starter", "Pro", "Enterprise"]

        with st.form("founder_add_institute_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Institute Name", placeholder="Sunrise Academy")
            city = col2.text_input("City", placeholder="Mumbai")
            col3, col4 = st.columns(2)
            state = col3.text_input("State", placeholder="Maharashtra")
            institute_type = col4.selectbox(
                "Institute Type",
                options=institute_types,
                index=0,
                key="hq_institute_type",
                label_visibility="visible",
            )
            st.caption(f"Selected institute type: {institute_type}")
            address = st.text_area("Full Address", height=90, placeholder="Address line")
            col5, col6 = st.columns(2)
            admin_name = col5.text_input("Admin Name", placeholder="Priya Sharma")
            admin_email = col6.text_input("Admin Email", placeholder="admin@example.com")
            col7, col8 = st.columns(2)
            admin_phone = col7.text_input("Admin Phone", placeholder="+91 98765 43210")
            plan = col8.selectbox(
                "Plan",
                options=plans,
                index=0,
                key="hq_plan",
                label_visibility="visible",
            )
            st.caption(f"Selected plan: {plan}")

            col9, col10 = st.columns(2)
            academic_year = col9.text_input("Academic Year", placeholder="2026-27")
            threshold = col10.number_input("Attendance Threshold (%)", min_value=50, max_value=100, value=75)

            submitted = st.form_submit_button(
                "✅ Create Institute & Generate Code",
                type="primary",
                use_container_width=True,
            )

            if submitted:
                if not name or not city:
                    st.error("Institute name and city are required.")
                else:
                    # Optional: help user understand why the form might not persist.
                    # (We handle schema-cache errors gracefully without crashing.)
                    form_data = {
                        "name": name,
                        "city": city,
                        "state": state,
                        "address": address,
                        "institute_type": institute_type,
                        "admin_name": admin_name,
                        "admin_email": admin_email,
                        "admin_phone": admin_phone,
                        "plan": plan,
                        "status": "active",
                        "attendance_threshold": int(threshold),
                        "academic_year": academic_year,
                        "expires_days": 30,
                    }

                    result = create_institute_with_code(form_data)
                    if result.get("ok"):
                        st.success(result.get("message", "Institute created."))
                        st.rerun()
                    else:
                        msg = result.get("message", "Failed to create institute.")
                        st.exception(Exception(msg))

    st.divider()

    st.subheader("Generate Access Code")
    institutes = list_institutes()
    if not institutes:
        st.info("Create an institute first.")
    else:
        with st.form("generate_code_form"):
            institute_label_map = {
                f"{item.get('name', 'Unnamed')} • {item.get('city', '')}": item for item in institutes
            }
            selected_label = st.selectbox("Institute", list(institute_label_map.keys()))
            admin_email = st.text_input("Admin Email for Code", placeholder="admin@example.com")
            expires_days = st.number_input("Code expiry (days)", min_value=1, max_value=365, value=30)

            submitted = st.form_submit_button("Generate Code")
            if submitted:
                institute = institute_label_map[selected_label]
                result = create_access_code(
                    institute.get("id", ""),
                    admin_email=admin_email,
                    expires_days=int(expires_days),
                )
                if result.get("ok"):
                    code_value = (result.get("data") or {}).get("code", "")
                    if code_value:
                        st.success("✅ Institute Access Code generated.")
                        st.code(code_value)
                    else:
                        st.success(result.get("message", "Access code generated."))
                    st.rerun()
                else:
                    msg = result.get("message", "Failed to generate access code.")
                    if "PGRST205" in msg or "schema cache" in msg or "Could not find the table" in msg:
                        st.warning("Supabase schema cache not ready. Code saved locally for now.")
                    else:
                        st.error(msg)

    st.divider()
    st.subheader("All Institutes")

    if not institutes:
        st.info("No institutes found.")
        return

    for institute in institutes:
        status = institute.get("status", "active")
        badge_class = "ok" if status == "active" else "danger"
        left, right = st.columns([4, 1])
        with left:
            st.markdown(
                f"""
                <div class="sc-subject-card">
                  <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;">
                    <div>
                      <h4 style="margin:0 0 4px;">{institute.get("name", "Unnamed Institute")}</h4>
                      <p style="margin:0;">{institute.get("city", "")} {institute.get("state", "")}</p>
                      <p style="margin:6px 0 0;">Admin: {institute.get("admin_name", "—")} ({institute.get("admin_email", "—")})</p>
                      <p style="margin:6px 0 0;">Plan: {institute.get("plan", "Demo")} • Type: {institute.get("institute_type", "School")}</p>
                    </div>
                    <span class="sc-badge {badge_class}">{status.title()}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            if status == "active":
                if st.button("Deactivate", key=f"founder_deactivate_{institute.get('id')}"):
                    result = deactivate_institute(institute.get("id", ""))
                    if result["ok"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
            else:
                if st.button("Activate", key=f"founder_activate_{institute.get('id')}"):
                    result = activate_institute(institute.get("id", ""))
                    if result["ok"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
