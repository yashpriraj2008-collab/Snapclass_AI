"""Founder plans and pricing management page."""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.components.ui import db_status_banner
from src.database.client import get_supabase


DEFAULT_PLANS: list[dict[str, Any]] = [
    {
        "Plan name": "Demo",
        "Price": "Free",
        "Student limit": 50,
        "Teacher limit": 1,
        "AI attendance": "No",
        "CSV/PDF export": "Basic",
        "Email alerts": "No",
        "Status": "Active",
    },
    {
        "Plan name": "Starter",
        "Price": "INR 499 per month",
        "Student limit": 200,
        "Teacher limit": 5,
        "AI attendance": "No",
        "CSV/PDF export": "Yes",
        "Email alerts": "Yes",
        "Status": "Active",
    },
    {
        "Plan name": "Pro",
        "Price": "INR 999 per month",
        "Student limit": 1000,
        "Teacher limit": 20,
        "AI attendance": "Yes",
        "CSV/PDF export": "Yes",
        "Email alerts": "Yes",
        "Status": "Active",
    },
    {
        "Plan name": "Enterprise",
        "Price": "INR 4,999 per month",
        "Student limit": "Unlimited",
        "Teacher limit": "Unlimited",
        "AI attendance": "Yes",
        "CSV/PDF export": "Yes",
        "Email alerts": "Yes",
        "Status": "Active",
    },
]


def _load_db_plans() -> list[dict[str, Any]]:
    db = get_supabase()
    if not db:
        return []
    try:
        rows = db.table("plans").select("*").order("price_inr").execute().data or []
    except Exception as exc:
        st.warning("Unable to load data. Please retry.")
        with st.expander("Developer Debug", expanded=False):
            st.code(str(exc))
        return []

    normalized: list[dict[str, Any]] = []
    for row in rows:
        limits = row.get("limits") if isinstance(row.get("limits"), dict) else {}
        features = row.get("feature_flags") if isinstance(row.get("feature_flags"), dict) else {}
        price = row.get("price_inr") or row.get("amount") or 0
        billing = row.get("billing_cycle") or "month"
        normalized.append(
            {
                "Plan name": row.get("name") or row.get("plan_name") or row.get("plan_code") or "Unnamed",
                "Price": "Free" if not price else f"INR {int(price):,} per {billing}",
                "Student limit": limits.get("students") or limits.get("student_limit") or row.get("student_limit") or "-",
                "Teacher limit": limits.get("teachers") or limits.get("teacher_limit") or row.get("teacher_limit") or "-",
                "AI attendance": "Yes" if features.get("ai_attendance") or row.get("ai_attendance") else "No",
                "CSV/PDF export": "Yes" if features.get("exports", True) else "No",
                "Email alerts": "Yes" if features.get("email_alerts", True) else "No",
                "Status": str(row.get("status") or "Active").title(),
            }
        )
    return normalized


def render_founder_plans() -> None:
    db_status_banner()
    st.markdown("### Plans & Pricing")
    st.caption("Manage subscription plans for institutes.")

    plans = _load_db_plans() or DEFAULT_PLANS
    if not plans:
        st.info("No plans found. Seed default plans.")
        return

    cols = st.columns(4, gap="medium")
    for col, plan in zip(cols, DEFAULT_PLANS):
        with col:
            with st.container(border=True):
                st.markdown(f"#### {plan['Plan name']}")
                st.markdown(f"**{plan['Price']}**")
                st.write(f"Students: {plan['Student limit']}")
                st.write(f"Teachers: {plan['Teacher limit']}")
                st.write(f"AI attendance: {plan['AI attendance']}")

    st.divider()
    st.markdown("### Institute Plans Overview")

    overview = pd.DataFrame(plans)
    if overview.empty:
        st.info("No plans found. Seed default plans.")
        return

    st.dataframe(overview, use_container_width=True, hide_index=True)

    with st.expander("Plan Actions", expanded=False):
        selected = st.selectbox("Plan", [str(plan["Plan name"]) for plan in plans])
        a1, a2 = st.columns(2)
        a1.button(f"View {selected}", use_container_width=True)
        a2.button(f"Edit {selected}", use_container_width=True)

