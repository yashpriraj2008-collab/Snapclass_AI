"""SnapClass HQ founder dashboard."""
from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timezone
from html import escape
from textwrap import dedent
from typing import Any

import streamlit as st

APP_ENV = os.getenv("APP_ENV", "development")
IS_PRODUCTION = APP_ENV == "production"


def show_debug(data: Any, title: str = "Developer Debug") -> None:
    """Show debug output only when not in production."""
    if IS_PRODUCTION:
        return
    with st.expander(title, expanded=False):
        st.code(str(data), language="python")



from src.database.client import get_supabase

from src.services.institute_service import (
    activate_institute,
    count_codes,
    count_institutes,
    create_access_code,
    init_institute_state,
    list_codes,
    list_institutes,
    normalize_code_status,
    update_institute,
)
from src.utils.session import nav_founder


ADMIN_ROLES = {"admin", "institute_admin"}


def _text(value: Any, fallback: str = "-") -> str:
    text = str(value or "").strip()
    return text or fallback


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _date(value: Any) -> str:
    raw = _text(value, "")
    if not raw:
        return "-"
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%d %b %Y")
    except Exception:
        return raw[:10] or "-"


def _is_expired(value: Any) -> bool:
    raw = _text(value, "")
    if not raw:
        return False
    try:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return stamp < datetime.now(timezone.utc)
    except Exception:
        return False


def _fetch_table(table: str, columns: str = "*") -> list[dict[str, Any]]:
    db = get_supabase()
    if not db:
        return []
    try:
        return db.table(table).select(columns).execute().data or []
    except Exception:
        return []


def _profiles_by_institute(profiles: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for profile in profiles:
        role = _norm(profile.get("role"))
        institute_id = _text(profile.get("institute_id"), "")
        if role in ADMIN_ROLES and institute_id:
            grouped.setdefault(institute_id, []).append(profile)
    return grouped


def _find_admin(institute: dict[str, Any], admin_profiles: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    institute_id = _text(institute.get("id"), "")
    linked = admin_profiles.get(institute_id, [])
    if linked:
        return linked[0]
    email = _norm(institute.get("admin_email"))
    if not email:
        return None
    for profiles in admin_profiles.values():
        for profile in profiles:
            if _norm(profile.get("email")) == email:
                return profile
    return None


def _status_badge(status: Any) -> None:
    label = _norm(status) or "active"
    if label in {"active", "paid"}:
        st.success(label.title())
    elif label in {"demo", "pending_payment", "payment_pending", "pending"}:
        st.warning(label.title())
    elif label in {"suspended", "disabled", "expired", "test_deleted"}:
        st.error(label.replace("_", " ").title())
    else:
        st.info(label.title())


def _link_admin_profile(institute: dict[str, Any], email: str) -> dict[str, Any]:
    db = get_supabase()
    if not db:
        return {"ok": False, "message": "Supabase is not configured. Add .streamlit/secrets.toml."}

    email_norm = _norm(email)
    institute_id = _text(institute.get("id"), "")
    if not email_norm or not institute_id:
        return {"ok": False, "message": "Admin email and institute are required."}

    try:
        rows = (
            db.table("user_profiles")
            .select("*")
            .eq("email", email_norm)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            return {
                "ok": False,
                "message": "Profile not found. Ask this admin to sign up/login first, then link again.",
            }

        profile = rows[0]
        updates = {
            "role": "admin",
            "institute_id": institute_id,
            "status": "active",
        }
        db.table("user_profiles").update(updates).eq("email", email_norm).execute()
        update_institute(
            institute_id,
            {
                "admin_email": email_norm,
                "admin_name": profile.get("full_name") or institute.get("admin_name") or "",
            },
        )
        return {"ok": True, "message": "Admin linked."}
    except Exception as exc:
        return {"ok": False, "message": "Admin could not be linked.", "debug": str(exc)}


def _render_quick_actions() -> None:
    st.subheader("Quick Actions")
    a1, a2, a3, a4, a5 = st.columns(5)
    if a1.button("Add Institute", use_container_width=True):
        nav_founder("founder_institutes")
    if a2.button("Generate Access Code", use_container_width=True):
        nav_founder("founder_institutes")
    if a3.button("View All Codes", use_container_width=True):
        nav_founder("founder_allcodes")
    if a4.button("View Institutes", use_container_width=True):
        nav_founder("founder_institutes")
    if a5.button("Manage Plans", use_container_width=True):
        nav_founder("founder_plans")


def render_institute_card(institute: dict[str, Any]) -> None:
    """Render a clean institute card (no raw IDs / no sensitive fields)."""
    name = escape(_text(institute.get("name"), "Unnamed Institute"))
    city = escape(_text(institute.get("city"), "Not set"))
    state = escape(_text(institute.get("state"), "Not set"))
    plan = escape(_text(institute.get("plan"), "Free"))
    status = escape(_text(institute.get("status"), "active").replace("_", " ").title())
    created_at = escape(_date(institute.get("created_at")))

    # Prefer display names if present; avoid showing admin_email on normal UI.
    admin_name = escape(_text(institute.get("admin_name"), "Not set"))

    st.markdown(
        dedent(
            f"""
            <div style="
                background:#ffffff;
                border:1px solid #e5e7eb;
                border-radius:18px;
                padding:20px;
                margin:10px 0;
                box-shadow:0 8px 24px rgba(15,23,42,0.06);
            ">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;">
                    <div>
                        <h2 style="margin:0;color:#111827;font-size:20px;">{name}</h2>
                        <p style="margin:6px 0 0 0;color:#6b7280;">{city}, {state}</p>
                        <p style="margin:10px 0 0 0;color:#6b7280;font-size:13px;">Admin: {admin_name}</p>
                    </div>
                    <span style="
                        background:#dcfce7;
                        color:#166534;
                        padding:8px 14px;
                        border-radius:999px;
                        font-weight:700;
                        font-size:14px;
                        white-space:nowrap;
                    ">{status}</span>
                </div>

                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:16px;">
                    <div>
                        <p style="color:#6b7280;margin:0;font-size:12px;">Plan</p>
                        <b style="color:#111827;">{plan}</b>
                    </div>
                    <div>
                        <p style="color:#6b7280;margin:0;font-size:12px;">Status</p>
                        <b style="color:#111827;">{status}</b>
                    </div>
                    <div>
                        <p style="color:#6b7280;margin:0;font-size:12px;">Created</p>
                        <b style="color:#111827;">{created_at if created_at != '-' else 'Not set'}</b>
                    </div>
                    <div>
                        <p style="color:#6b7280;margin:0;font-size:12px;">Actions</p>
                        <b style="color:#111827;">Use tabs below</b>
                    </div>
                </div>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def _render_institute_actions(institute: dict[str, Any], idx: int) -> None:
    institute_id = _text(institute.get("id"), "")
    status = _norm(institute.get("status")) or "active"

    with st.expander("Actions", expanded=False):
        t1, t2, t3 = st.tabs(["View", "Edit", "Admin"])

        with t1:
            render_institute_card(institute)

        with t2:


            with st.form(f"founder_edit_institute_{institute_id or idx}"):
                name = st.text_input("Institute name", value=_text(institute.get("name"), ""))
                city = st.text_input("City", value=_text(institute.get("city"), ""))
                state = st.text_input("State", value=_text(institute.get("state"), ""))
                admin_name = st.text_input("Admin name", value=_text(institute.get("admin_name"), ""))
                admin_email = st.text_input("Admin email", value=_text(institute.get("admin_email"), ""))
                plan = st.text_input("Plan", value=_text(institute.get("plan"), "Demo"))
                if st.form_submit_button("Save Institute", use_container_width=True):
                    result = update_institute(
                        institute_id,
                        {
                            "name": name.strip(),
                            "city": city.strip(),
                            "state": state.strip(),
                            "admin_name": admin_name.strip(),
                            "admin_email": admin_email.strip().lower(),
                            "plan": plan.strip(),
                        },
                    )
                    if result.get("ok"):
                        st.success("Institute updated.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Institute could not be updated.")

        with t3:
            link_email = st.text_input(
                "Admin email to link",
                value=_text(institute.get("admin_email"), ""),
                key=f"link_admin_email_{institute_id or idx}",
            )
            if st.button("Link Admin", key=f"link_admin_{institute_id or idx}", use_container_width=True):
                result = _link_admin_profile(institute, link_email)
                if result.get("ok"):
                    st.success(result["message"])
                    st.cache_data.clear()
                    st.rerun()

                else:
                    st.warning(result.get("message", "Admin could not be linked."))
                    if result.get("debug"):
                        show_debug(result.get("debug"))


        b1, b2, b3 = st.columns(3)
        if status in {"suspended", "disabled"}:
            if b1.button(
                "Reactivate Institute",
                key=f"reactivate_{institute_id or idx}",
                use_container_width=True,
            ):
                result = activate_institute(institute_id)
                if result.get("ok"):
                    st.success("Institute reactivated.")
                    st.cache_data.clear()
                    st.rerun()

                st.error("Institute could not be reactivated.")
        else:
            if b1.button(
                "Suspend Institute",
                key=f"suspend_{institute_id or idx}",
                use_container_width=True,
            ):
                result = update_institute(institute_id, {"status": "suspended"})
                if result.get("ok"):
                    st.success("Institute suspended.")
                    st.cache_data.clear()
                    st.rerun()

                st.error("Institute could not be suspended.")

        confirm_delete = st.checkbox(
            "I understand this will permanently remove institute access (soft delete).",
            key=f"confirm_delete_{institute_id or idx}",
        )

        if confirm_delete:
            if b2.button(
                "Delete Institute",
                key=f"delete_{institute_id or idx}",
                use_container_width=True,
            ):
                result = update_institute(institute_id, {"status": "deleted"})
                if result.get("ok"):
                    st.success("Institute deleted (soft delete).")
                    st.cache_data.clear()
                    st.rerun()
                st.error("Institute could not be deleted.")


        if b3.button("Generate Code", key=f"dash_code_{institute_id or idx}", use_container_width=True):
            result = create_access_code(
                institute_id,
                admin_email=_text(institute.get("admin_email"), ""),
                expires_days=30,
            )
            if result.get("ok"):
                code = (result.get("data") or {}).get("code", "")
                st.success(f"Access code generated: {code}" if code else "Access code generated.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(result.get("message", "Access code could not be generated."))


def render_founder_dashboard() -> None:
    """Render the SnapClass HQ overview screen."""
    init_institute_state()

    st.markdown("## SnapClass HQ")
    st.caption("Founder control center for institutes, quality checks, subscriptions, and access codes.")

    institutes = list_institutes()
    codes = list_codes()
    profiles = _fetch_table("user_profiles")
    subscriptions = _fetch_table("subscriptions")
    payments = _fetch_table("payments")
    admin_profiles = _profiles_by_institute(profiles)

    admin_by_institute = {
        _text(inst.get("id"), ""): _find_admin(inst, admin_profiles)
        for inst in institutes
    }
    missing_admin_count = sum(1 for inst in institutes if not admin_by_institute.get(_text(inst.get("id"), "")))

    duplicate_keys = [
        (_norm(inst.get("name")), _norm(inst.get("city")), _norm(inst.get("state")))
        for inst in institutes
        if _norm(inst.get("name"))
    ]
    duplicate_counts = Counter(duplicate_keys)
    duplicate_key_set = {key for key, count in duplicate_counts.items() if count > 1}
    duplicate_institute_count = sum(duplicate_counts[key] for key in duplicate_key_set)

    active_institutes = sum(1 for inst in institutes if _norm(inst.get("status")) in {"", "active"})
    demo_institutes = sum(
        1
        for inst in institutes
        if _norm(inst.get("plan")) in {"demo", "free demo"}
    )
    paid_institutes = sum(
        1
        for inst in institutes
        if _norm(inst.get("plan")) in {"starter", "pro", "enterprise"}
        and _norm(inst.get("status")) not in {"suspended", "disabled", "test_deleted"}
    )
    expired_subscriptions = sum(
        1
        for sub in subscriptions
        if _norm(sub.get("status")) in {"expired", "cancelled"} or _is_expired(sub.get("ends_at"))
    )
    suspended_institutes = sum(1 for inst in institutes if _norm(inst.get("status")) in {"suspended", "disabled"})

    pending_codes = sum(1 for code in codes if normalize_code_status(code) == "unused")
    expired_codes = sum(1 for code in codes if normalize_code_status(code) == "expired")

    now = datetime.now(timezone.utc)
    monthly_revenue = 0.0
    pending_payments = 0
    failed_payments = 0
    for payment in payments:
        status = _norm(payment.get("status"))
        amount = payment.get("amount") or payment.get("amount_rupees") or payment.get("amount_inr") or 0
        created = _text(payment.get("created_at"), "")
        same_month = True
        if created:
            try:
                created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
                same_month = created_at.year == now.year and created_at.month == now.month
            except Exception:
                same_month = True
        if status in {"paid", "success", "successful", "captured"} and same_month:
            try:
                monthly_revenue += float(amount)
            except Exception:
                pass
        if status in {"pending", "created"}:
            pending_payments += 1
        if status in {"failed", "failure"}:
            failed_payments += 1
    active_subscriptions = sum(1 for sub in subscriptions if _norm(sub.get("status")) == "active")

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Institutes", count_institutes())
    s2.metric("Active Institutes", active_institutes)
    s3.metric("Codes", count_codes())
    s4.metric("Pending Codes", pending_codes)

    s5, s6, s7, s8 = st.columns(4)
    s5.metric("Demo Institutes", demo_institutes)
    s6.metric("Paid Institutes", paid_institutes)
    s7.metric("Institutes Missing Admin", missing_admin_count)
    s8.metric("Duplicate Institute Names", duplicate_institute_count)

    st.divider()
    _render_quick_actions()

    st.divider()
    st.subheader("Institute Health")
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Demo Institutes", demo_institutes)
    h2.metric("Paid Institutes", paid_institutes)
    h3.metric("Expired Subscriptions", expired_subscriptions)
    h4.metric("Suspended Institutes", suspended_institutes)

    st.subheader("Revenue")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Monthly Revenue", f"INR {monthly_revenue:,.0f}")
    r2.metric("Pending Payments", pending_payments)
    r3.metric("Failed Payments", failed_payments)
    r4.metric("Active Subscriptions", active_subscriptions)

    st.divider()
    st.subheader("Data Quality Warnings")
    warnings: list[str] = []
    if missing_admin_count:
        warnings.append(f"{missing_admin_count} institutes have no admin linked")
    if duplicate_institute_count:
        warnings.append(f"{duplicate_institute_count} possible duplicate institute rows found")
    if expired_codes:
        warnings.append(f"{expired_codes} access codes are expired")
    orphan_profiles = [
        profile for profile in profiles
        if _norm(profile.get("role")) in {"admin", "institute_admin", "teacher", "student"}
        and not _text(profile.get("institute_id"), "")
    ]
    if orphan_profiles:
        warnings.append(f"{len(orphan_profiles)} profiles have no institute linked")
    if profiles:
        known_profile_ids = {_text(profile.get("user_id") or profile.get("id"), "") for profile in profiles}
        users_without_profiles = 0
        for table in ("teachers", "students"):
            for row in _fetch_table(table, "user_id,email"):
                user_id = _text(row.get("user_id"), "")
                if user_id and user_id not in known_profile_ids:
                    users_without_profiles += 1
        if users_without_profiles:
            warnings.append(f"{users_without_profiles} app users have no matching profile")

    if not warnings:
        st.success("No major data quality warnings found.")
    else:
        for item in warnings:
            st.warning(item)

    st.divider()
    st.subheader("Recent Institutes")

    if not institutes:
        st.info("No institutes created yet.")
        return

    for idx, institute in enumerate(institutes[:10]):
        institute_id = _text(institute.get("id"), "")
        admin = admin_by_institute.get(institute_id)
        duplicate_key = (_norm(institute.get("name")), _norm(institute.get("city")), _norm(institute.get("state")))
        possible_duplicate = duplicate_key in duplicate_key_set
        admin_name = _text((admin or {}).get("full_name") or institute.get("admin_name"), "")
        admin_email = _text((admin or {}).get("email") or institute.get("admin_email"), "")

        with st.container(border=True):
            title_col, status_col = st.columns([3, 1])
            with title_col:
                st.markdown(f"#### {_text(institute.get('name'), 'Unnamed Institute')}")
                st.caption(f"{_text(institute.get('city'))}, {_text(institute.get('state'))}")
            with status_col:
                _status_badge(institute.get("status", "active"))

            row1, row2, row3, row4 = st.columns(4)
            row1.markdown(f"**Admin**  \n{admin_name or 'Admin not linked'}")
            row2.markdown(f"**Email**  \n{admin_email or 'Admin not linked'}")
            row3.markdown(f"**Plan**  \n{_text(institute.get('plan'), 'Demo')}")
            row4.markdown(f"**Created**  \n{_date(institute.get('created_at'))}")

            if not admin:
                st.warning("Admin not linked")
            if possible_duplicate:
                st.warning("Possible duplicate")

            _render_institute_actions(institute, idx)
