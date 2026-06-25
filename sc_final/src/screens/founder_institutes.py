"""SnapClass HQ institutes management page."""
from __future__ import annotations

import html
import streamlit as st

from src.components.avatar import avatar_html
from src.components.form_controls import format_institute_option, safe_selectbox
from src.database.client import get_supabase_client
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


def _rows(table: str) -> list[dict]:
    db = get_supabase_client()
    if not db:
        return []
    try:
        return db.table(table).select("*").execute().data or []
    except Exception:
        return []


def _institute_identity_data() -> tuple[dict[str, dict], dict[str, dict]]:
    admins: dict[str, dict] = {}
    for profile in _rows("user_profiles"):
        role = str(profile.get("role") or "").strip().lower()
        institute_id = str(profile.get("institute_id") or "")
        if role in {"admin", "institute_admin"} and institute_id:
            admins.setdefault(institute_id, profile)

    subscriptions: dict[str, dict] = {}
    for subscription in _rows("subscriptions"):
        institute_id = str(subscription.get("institute_id") or "")
        if institute_id:
            subscriptions[institute_id] = subscription
    return admins, subscriptions


def render_founder_institutes() -> None:
    """Render the institute management page for SnapClass HQ."""
    init_institute_state()

    st.markdown("## Founder - Institutes")
    st.caption("Create institutes, manage status, and generate access codes.")

    institutes = list_institutes()
    total_institutes = count_institutes()
    total_codes = count_codes()
    active_institutes = sum(1 for item in institutes if item.get("status", "active") == "active")
    disabled_institutes = max(total_institutes - active_institutes, 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Institutes", total_institutes)
    c2.metric("Active", active_institutes)
    c3.metric("Disabled", disabled_institutes)
    c4.metric("Codes", total_codes)

    st.divider()

    if st.button("<- Back to Dashboard", use_container_width=True, key="founder_institutes_back"):
        nav_founder("founder_dashboard")

    st.divider()

    with st.expander("Add New Institute", expanded=True):
        institute_types = ["School", "Coaching", "Tuition", "College"]
        plans = ["Free Demo", "Starter", "Pro", "Enterprise"]

        with st.form("founder_add_institute_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Institute Name", placeholder="Sunrise Academy")
            city = col2.text_input("City", placeholder="Mumbai")

            col3, col4 = st.columns(2)
            state = col3.text_input("State", placeholder="Maharashtra")
            with col4:
                institute_type = safe_selectbox(
                    "Institute Type",
                    institute_types,
                    key="founder_add_institute_type",
                )
            st.caption(f"Selected institute type: {institute_type}")

            address = st.text_area("Full Address", height=90, placeholder="Address line")

            col5, col6 = st.columns(2)
            admin_name = col5.text_input("Admin Name", placeholder="Priya Sharma")
            admin_email = col6.text_input("Admin Email", placeholder="admin@example.com")

            col7, col8 = st.columns(2)
            admin_phone = col7.text_input("Admin Phone", placeholder="+91 98765 43210")
            with col8:
                plan = safe_selectbox(
                    "Plan",
                    plans,
                    key="founder_add_institute_plan",
                )
            st.caption(f"Selected plan: {plan}")

            col9, col10 = st.columns(2)
            ACADEMIC_YEARS = ["2025-26", "2026-27", "2027-28", "2028-29"]
            academic_year = col9.selectbox(
                "Academic Year",
                ACADEMIC_YEARS,
                index=ACADEMIC_YEARS.index("2026-27"),
            )
            threshold = col10.number_input("Attendance Threshold (%)", min_value=50, max_value=100, value=75)

            submitted = st.form_submit_button(
                "Create Institute & Generate Code",
                type="primary",
                use_container_width=True,
            )

            if submitted:
                if not name or not city:
                    st.error("Institute name and city are required.")
                else:
                    form_data = {
                        "name": name,
                        "city": city,
                        "state": state,
                        "address": address,
                        "institute_type": institute_type or "School",
                        "admin_name": admin_name,
                        "admin_email": admin_email,
                        "admin_phone": admin_phone,
                        "plan": plan or "Free Demo",
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
                        st.error("Institute could not be created. Please check the database setup and try again.")
                        if result.get("debug") or result.get("error"):
                            with st.expander("Developer Debug", expanded=False):
                                st.code(str(result.get("debug") or result.get("error")))

    st.divider()

    st.subheader("Generate Access Code")
    institutes = list_institutes()
    if not institutes:
        st.info("No institutes found. Add an institute first.")
    else:
        with st.form("generate_code_form"):
            institute = safe_selectbox(
                "Institute",
                institutes,
                key="founder_generate_code_institute",
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
            expires_days = st.number_input("Code expiry (days)", min_value=1, max_value=365, value=30)

            submitted = st.form_submit_button("Generate Code")
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
                    code_value = (result.get("data") or {}).get("code", "")
                    if code_value:
                        st.success("Institute Access Code generated.")
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

    institutes = list_institutes()
    if not institutes:
        st.info("No institutes found.")
        return

    admins, subscriptions = _institute_identity_data()
    for institute in institutes:
        institute_id = str(institute.get("id") or "")
        admin = admins.get(institute_id) or {}
        subscription = subscriptions.get(institute_id) or {}
        status = institute.get("status", "active")
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                institute_logo = str(institute.get("logo_url") or "")
                admin_name = admin.get("full_name") or institute.get("admin_name") or "Institute Admin"
                identity_image = avatar_html(
                    {
                        "name": institute.get("name") or admin_name,
                        "profile_photo_url": institute_logo or admin.get("profile_photo_url") or "",
                    },
                    size=54,
                )
                st.markdown(
                    f"""
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                      {identity_image}
                      <div>
                        <h4 style="margin:0;">{html.escape(str(institute.get('name') or 'Unnamed Institute'))}</h4>
                        <div style="color:#6B7280;font-size:.85rem;">{html.escape(str(admin_name))}</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.write(f"{institute.get('city', '')} {institute.get('state', '')}".strip())
                st.write(
                    f"Admin: {admin.get('full_name') or institute.get('admin_name') or '-'} "
                    f"({admin.get('email') or institute.get('admin_email') or '-'})"
                )
                st.write(
                    f"Plan: {institute.get('plan', 'Demo')} | "
                    f"Payment: {str(subscription.get('status') or institute.get('subscription_status') or 'pending').replace('_', ' ').title()} | "
                    f"Status: {str(status).replace('_', ' ').title()}"
                )
            with right:
                if status == "active":
                    st.success("Active")
                    if st.button("Deactivate", key=f"founder_deactivate_{institute.get('id')}"):
                        result = deactivate_institute(institute.get("id", ""))
                        if result["ok"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])
                else:
                    st.error(str(status).title())
                    if st.button("Activate", key=f"founder_activate_{institute.get('id')}"):
                        result = activate_institute(institute.get("id", ""))
                        if result["ok"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])

                # Edit toggle (must not interfere with Activate/Deactivate)
                if not st.session_state.get(f"editing_{institute_id}", False):
                    if st.button("Edit", key=f"edit_{institute.get('id')}"):
                        st.session_state[f"editing_{institute_id}"] = True

            # Edit form (shown below the card content only when toggled)
            if st.session_state.get(f"editing_{institute_id}", False):
                # Pull available plans from Supabase for the dropdown
                plans_options: list[dict] = []
                db = get_supabase_client()
                if db:
                    try:
                        plans_options = db.table("plans").select("id,display_name,name,plan_code").execute().data or []
                    except Exception:
                        plans_options = []

                def _plan_display(p: dict) -> str:
                    return str(
                        p.get("display_name")
                        or p.get("name")
                        or p.get("plan_code")
                        or p.get("id")
                        or ""
                    ).strip()

                def _pick_plan_id_from_current(current_plan_label: str) -> str | None:
                    current_plan_label = str(current_plan_label or "").strip().lower()
                    if not current_plan_label:
                        return None
                    for p in plans_options:
                        if str(_plan_display(p)).strip().lower() == current_plan_label:
                            return str(p.get("id") or "") or None
                        if str(p.get("name") or "").strip().lower() == current_plan_label:
                            return str(p.get("id") or "") or None
                        if str(p.get("plan_code") or "").strip().lower() == current_plan_label:
                            return str(p.get("id") or "") or None
                    # If the institutes.plan column already stores plan_id in your DB,
                    # fall back to matching by id.
                    for p in plans_options:
                        if str(p.get("id") or "").strip() == str(current_plan_label).strip():
                            return str(p.get("id") or "") or None
                    return None

                current_plan_label = institute.get("plan", "Demo")
                # Kept for readability; saving logic remaps from selected plan label
                # to plan_id (if available).
                _ = _pick_plan_id_from_current(current_plan_label)


                plan_labels = [_plan_display(p) for p in plans_options if _plan_display(p)]
                if not plan_labels:
                    plan_labels = [str(current_plan_label or "Demo")]

                selected_plan_label = str(current_plan_label or "Demo")

                subscription_default = (
                    subscription.get("status")
                    or institute.get("subscription_status")
                    or "payment_pending"
                )
                subscription_default = str(subscription_default).strip().lower()

                subscription_status_options = [
                    "trial_active",
                    "active",
                    "payment_pending",
                    "expired",
                    "cancelled",
                ]

                if subscription_default not in subscription_status_options:
                    subscription_default = "payment_pending"

                with st.form(key=f"edit_institute_form_{institute_id}"):
                    new_name = st.text_input(
                        "Institute name",
                        value=str(institute.get("name") or ""),
                    )
                    new_location = st.text_input(
                        "Location / city",
                        value=str(institute.get("city") or ""),
                    )
                    new_admin_name = st.text_input(
                        "Admin name",
                        value=str(institute.get("admin_name") or ""),
                    )
                    new_admin_email = st.text_input(
                        "Admin email",
                        value=str(institute.get("admin_email") or ""),
                    )

                    new_plan_label = st.selectbox(
                        "Plan",
                        plan_labels,
                        index=plan_labels.index(selected_plan_label) if selected_plan_label in plan_labels else 0,
                    )

                    new_status = st.selectbox(
                        "Subscription status",
                        subscription_status_options,
                        index=subscription_status_options.index(subscription_default)
                        if subscription_default in subscription_status_options
                        else 2,
                    )

                    submitted_save = st.form_submit_button("Save Changes", type="primary")
                    submitted_cancel = st.form_submit_button("Cancel")

                    if submitted_save:
                        try:
                            # Map selected plan label -> plan id when saving.
                            new_plan_id = None
                            for p in plans_options:
                                if _plan_display(p) == str(new_plan_label):
                                    new_plan_id = str(p.get("id") or "") or None
                                    break

                            update_payload = {
                                "name": new_name,
                                "city": new_location,
                                "admin_name": new_admin_name,
                                "admin_email": new_admin_email,
                                "plan": (new_plan_id or new_plan_label),
                                "subscription_status": new_status,
                            }

                            result = (
                                get_supabase_client()
                                .table("institutes")
                                .update(update_payload)
                                .eq("id", institute.get("id", ""))
                                .execute()
                            )

                            st.success("Institute updated successfully.")
                            st.session_state[f"editing_{institute_id}"] = False
                            st.rerun()
                        except Exception:
                            st.error("Could not update institute. Please try again.")
                    elif submitted_cancel:
                        st.session_state[f"editing_{institute_id}"] = False
                        st.rerun()
