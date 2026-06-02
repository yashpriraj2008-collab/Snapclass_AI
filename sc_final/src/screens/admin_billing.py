"""Admin Billing page (Phase 5 Part A)

Shows active plan/usage and provides upgrade navigation.

Phase 5 Razorpay test flow:
- reads public.subscriptions (status='active')
- displays the active plan name

UI theme/sidebar/chatbot/attendance are intentionally untouched.
"""

from __future__ import annotations

import streamlit as st

from src.components.navigation import go_to
from src.database.client import get_supabase_client


def show_admin_billing() -> None:
    st.title("💳 Billing & Plan")
    st.info(
        "Phase 5 Part A UI is ready. Active plan + usage will be shown once "
        "subscription activation services are fully wired."
    )

    st.subheader("Current plan")

    db = get_supabase_client()
    if db is None:
        st.warning("Supabase not connected.")
    else:
        try:
            # public.subscriptions has institute_id unique; display any active row.
            institute_id = st.session_state.get("institute_id")
            if not institute_id:
                st.warning("Missing institute_id in session_state.")
            else:
                res = (
                    db.table("subscriptions")
                    .select("plan_id,status,billing_cycle")
                    .eq("institute_id", institute_id)
                    .eq("status", "active")
                    .limit(1)
                    .execute()
                )
                rows = res.data or []
                if not rows:
                    st.write("No active subscription.")
                else:
                    sub = rows[0]
                    plan_id = sub.get("plan_id")
                    # Resolve plan display name
                    plan_res = (
                        db.table("plans")
                        .select("display_name,plan_code")
                        .eq("id", plan_id)
                        .limit(1)
                        .execute()
                    )
                    plan_rows = plan_res.data or []
                    plan = plan_rows[0] if plan_rows else {}
                    name = plan.get("display_name") or plan.get("plan_code") or str(plan_id)
                    st.write(f"{name} ({sub.get('billing_cycle')})")
        except Exception:
            st.write("—")

    st.subheader("Usage")
    st.write("students: —")
    st.write("teachers: —")

    st.subheader("Upgrade")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        if st.button("Upgrade to Starter", use_container_width=True):
            st.session_state.selected_plan = "starter"
            st.session_state.page = "pricing"
            st.rerun()
    with c2:
        if st.button("Upgrade to Pro", use_container_width=True):
            st.session_state.selected_plan = "pro"
            st.session_state.page = "pricing"
            st.rerun()
    with c3:
        if st.button("Enterprise", use_container_width=True):
            st.session_state.selected_plan = "enterprise"
            st.session_state.page = "contact"
            st.rerun()

    if st.button("Back", key="admin_billing_back", use_container_width=True):
        go_to("admin_dashboard")

