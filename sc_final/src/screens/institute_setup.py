"""First-time institute setup/onboarding."""
import os

import streamlit as st

from src.services.institute_service import init_institute_state, mark_code_used, update_institute


def _debug_enabled() -> bool:
    return str(os.getenv("APP_ENV", "")).strip().lower() == "development" or bool(st.session_state.get("debug_mode"))


def show_institute_setup() -> None:
    init_institute_state()
    institute = st.session_state.get("current_institute")
    if not institute:
        st.warning("Your institute session is missing. Please start your demo again or login.")
        c1, c2, c3 = st.columns(3)
        if c1.button("Start Demo Again", use_container_width=True):
            st.session_state.return_to = "pricing"
            st.session_state.page = "demo_signup"
            st.rerun()
        if c2.button("Back to Pricing", use_container_width=True):
            st.session_state.page = "pricing"
            st.rerun()
        if c3.button("Admin Login", use_container_width=True):
            st.session_state.page = "institute_login"
            st.rerun()
        return

    # Progress indicator
    st.markdown(
        """
    <div style="display:flex;justify-content:center;gap:0;margin-bottom:28px;">
      <div style="text-align:center;"><div style="width:32px;height:32px;border-radius:999px;
        background:#10B981;color:white;display:flex;align-items:center;justify-content:center;
        font-weight:700;margin:0 auto 4px;">✓</div>
        <span style="font-size:.75rem;color:#10B981;">Code Validated</span></div>
      <div style="flex:1;height:2px;background:#5B6CFF;margin:16px 12px 0;max-width:60px;"></div>
      <div style="text-align:center;"><div style="width:32px;height:32px;border-radius:999px;
        background:#5B6CFF;color:white;display:flex;align-items:center;justify-content:center;
        font-weight:700;margin:0 auto 4px;">2</div>
        <span style="font-size:.75rem;color:#5B6CFF;font-weight:600;">Setup</span></div>
      <div style="flex:1;height:2px;background:#E5E7EB;margin:16px 12px 0;max-width:60px;"></div>
      <div style="text-align:center;"><div style="width:32px;height:32px;border-radius:999px;
        background:#E5E7EB;color:#6B7280;display:flex;align-items:center;justify-content:center;
        font-weight:700;margin:0 auto 4px;">3</div>
        <span style="font-size:.75rem;color:#6B7280;">Dashboard</span></div>
    </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("## 🏫 Institute Setup")
    st.caption("Complete your institute profile to start using SnapClass AI.")

    allowed_plans = ["Demo", "Starter", "Pro", "Enterprise"]
    raw_plan = st.session_state.get("selected_plan") or institute.get("plan", "Demo")
    normalized_plan = str(raw_plan).strip().lower()
    plan_map = {plan.lower(): plan for plan in allowed_plans}
    selected_plan = plan_map.get(normalized_plan, "Demo")

    with st.form("institute_setup_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Institute Name *", value=institute.get("name", ""))

        allowed_types = ["School", "Coaching", "Tuition Centre", "College"]
        raw_type = institute.get("institute_type", "School")
        normalized = str(raw_type).strip().lower()
        type_map = {t.lower(): t for t in allowed_types}
        default_type = "School"
        if normalized in type_map:
            default_type = type_map[normalized]
        elif normalized in ("tuition", "tuition center", "tuition centre"):
            default_type = "Tuition Centre"
        inst_type = c2.selectbox(
            "Institute Type *",
            allowed_types,
            index=allowed_types.index(default_type),
        )

        plan_choice = st.selectbox(
            "Plan",
            allowed_plans,
            index=allowed_plans.index(selected_plan),
        )

        c3, c4 = st.columns(2)
        city = c3.text_input("City *", value=institute.get("city", ""))
        state = c4.text_input("State *", value=institute.get("state", ""))
        address = st.text_area("Full Address", value=institute.get("address", ""), height=70)

        c5, c6 = st.columns(2)
        principal = c5.text_input(
            "Principal / Owner Name *",
            value=institute.get("admin_name", st.session_state.get("admin_name", "")),
        )
        phone = c6.text_input("Phone", value=institute.get("admin_phone", ""))

        c7, c8 = st.columns(2)
        ACADEMIC_YEARS = ["2025-26", "2026-27", "2027-28", "2028-29"]
        DEFAULT_ACYR = "2026-27"
        current_acyr = str(institute.get("academic_year", "")).strip() or DEFAULT_ACYR
        acyr_index = ACADEMIC_YEARS.index(current_acyr) if current_acyr in ACADEMIC_YEARS else 1
        acyr = c7.selectbox(
            "Academic Year *",
            ACADEMIC_YEARS,
            index=acyr_index,
        )
        thr = c8.slider("Attendance Threshold (%)", 50, 100, int(institute.get("attendance_threshold", 75)), 1)

        submitted = st.form_submit_button(
            "✅ Complete Setup & Go to Dashboard", type="primary", use_container_width=True
        )
        if submitted:
            if not name or not city or not principal:
                st.error("Please fill all required (*) fields.")
            else:
                updates = {
                    "name": name,
                    "institute_type": inst_type,
                    "plan": plan_choice,
                    "city": city,
                    "state": state,
                    "address": address,
                    "admin_name": principal,
                    "admin_phone": phone,
                    "academic_year": acyr,
                    "attendance_threshold": thr,
                    "onboarding_completed": True,
                }
                inst_id = st.session_state.get("active_institute_id", "")
                result = update_institute(inst_id, updates) if inst_id else {"ok": True, "demo": True, "message": "✅ Saved locally (no institute_id in session — demo mode)."}
                if not result.get("ok"):
                    st.error("Institute setup could not be saved. Please check your access and try again.")
                    return

                institute.update(updates)
                st.session_state.current_institute = institute
                st.session_state.selected_plan = plan_choice
                st.session_state.active_institute_name = name
                st.session_state.user_name = principal
                st.session_state.admin_name = principal
                st.session_state.admin_onboarding_completed = True
                code_value = st.session_state.get("active_institute_code", "")
                if code_value:
                    mark_result = mark_code_used(
                        code_value,
                        admin_email=st.session_state.get("admin_email") or institute.get("admin_email") or "",
                        institute_id=inst_id,
                    )
                    if not mark_result.get("ok") and _debug_enabled():
                        with st.expander("Developer Debug", expanded=False):
                            st.code(str(mark_result.get("debug") or mark_result.get("message") or mark_result))
                st.session_state.page = "institute_dashboard"
                st.session_state.institute_page = "institute_dashboard"
                st.success(f"✅ Welcome to SnapClass AI, {principal}!")
                st.rerun()
