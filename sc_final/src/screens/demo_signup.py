"""Free demo institute signup flow."""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

import streamlit as st

from src.components.public_nav import render_public_nav
from src.database.client import get_supabase_client
from src.services.user_onboarding_service import create_or_continue_admin_onboarding
from src.services.institute_service import create_institute, init_institute_state, set_active_institute

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _finish_progress() -> None:
    st.session_state["demo_signup_in_progress"] = False


def _go_admin_login() -> None:
    st.session_state.return_to = "pricing"
    st.session_state.page = "institute_login"
    st.rerun()


def _go_pricing() -> None:
    st.session_state.page = "pricing"
    st.rerun()


def _render_existing_account_actions() -> None:
    c1, c2 = st.columns(2)
    if c1.button("Go to Admin Login", use_container_width=True, key="demo_existing_login"):
        _go_admin_login()
    if c2.button("Back to Pricing", use_container_width=True, key="demo_existing_pricing"):
        _go_pricing()


def _validate_demo_form(
    *,
    institute_name: str,
    admin_name: str,
    admin_email: str,
    admin_password: str,
    city: str,
    state: str,
) -> list[str]:
    errors: list[str] = []
    if not institute_name.strip():
        errors.append("Institute Name is required.")
    if not admin_name.strip():
        errors.append("Admin Name is required.")
    if not admin_email.strip() or not EMAIL_RE.match(admin_email.strip()):
        errors.append("Enter a valid admin email.")
    if len(admin_password or "") < 8:
        errors.append("Admin Password must be at least 8 characters.")
    if not city.strip():
        errors.append("City is required.")
    if not state.strip():
        errors.append("State is required.")
    return errors


def _get_user_id(user: Any) -> str:
    return str(getattr(user, "id", None) or getattr(user, "user_id", None) or "").strip()


def _get_profile_by_email(email: str) -> dict[str, Any] | None:
    db = get_supabase_client()
    if not db:
        return None
    try:
        rows = (
            db.table("user_profiles")
            .select("*")
            .eq("email", (email or "").strip().lower())
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def _get_institute_by_id(institute_id: str) -> dict[str, Any] | None:
    db = get_supabase_client()
    if not db or not institute_id:
        return None
    try:
        rows = (
            db.table("institutes")
            .select("*")
            .eq("id", institute_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def _get_institute_by_admin_email(email: str) -> dict[str, Any] | None:
    db = get_supabase_client()
    if not db:
        return None
    try:
        rows = (
            db.table("institutes")
            .select("*")
            .eq("admin_email", (email or "").strip().lower())
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def _get_or_create_demo_institute(
    *,
    institute_name: str,
    admin_name: str,
    admin_email: str,
    city: str,
    state: str,
    phone: str,
    selected_plan: str,
    existing_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    institute_id = str((existing_profile or {}).get("institute_id") or "").strip()
    if institute_id:
        institute = _get_institute_by_id(institute_id)
        if institute:
            return {"ok": True, "data": institute, "reused": True}

    institute = _get_institute_by_admin_email(admin_email)
    if institute:
        return {"ok": True, "data": institute, "reused": True}

    return create_institute(
        name=institute_name,
        city=city,
        state=state,
        institute_type="School",
        admin_name=admin_name,
        admin_email=admin_email,
        admin_phone=phone,
        plan={"starter": "Starter", "pro": "Pro"}.get(selected_plan, "Demo"),
        status="active",
    )


def _ensure_demo_admin_auth(*, email: str, password: str, name: str) -> dict[str, Any]:
    db = get_supabase_client()
    if not db:
        return {"ok": False, "message": "Supabase is not configured. Add .streamlit/secrets.toml."}

    email_norm = (email or "").strip().lower()
    name_norm = (name or "").strip()
    if not email_norm or not password or not name_norm:
        return {"ok": False, "message": "Please fill all required admin fields."}

    # If user exists, we should be able to sign them in immediately.
    try:
        auth_in = db.auth.sign_in_with_password({"email": email_norm, "password": password})
        user_id = _get_user_id(getattr(auth_in, "user", None))
        if user_id:
            return {"ok": True, "user_id": user_id, "session": getattr(auth_in, "session", None)}
    except Exception:
        pass

    # 1) Signup
    # 2) Immediately sign-in (RLS/session dependent)
    try:
        sign_up_res = db.auth.sign_up(
            {
                "email": email_norm,
                "password": password,
                "options": {"data": {"full_name": name_norm, "role": "admin"}},
            }
        )
        # If email confirmation is enabled, signup may not return an active session.
        auth_user = getattr(sign_up_res, "user", None) or getattr(sign_up_res, "data", {}).get("user")
        user_id = _get_user_id(auth_user)

        try:
            auth_in = db.auth.sign_in_with_password({"email": email_norm, "password": password})
            user_id_in = _get_user_id(getattr(auth_in, "user", None))
            if not user_id_in:
                return {"ok": False, "message": "Account created. Please login to finish setup.", "missing_session": True}
            return {
                "ok": True,
                "user_id": str(user_id_in),
                "session": getattr(auth_in, "session", None),
            }
        except Exception as exc_in:
            msg_in = str(exc_in).lower()
            # Common: email not confirmed / session not available
            if "confirm" in msg_in or "verify" in msg_in or "session" in msg_in:
                return {"ok": False, "message": "Account created. Please login to finish setup.", "missing_session": True}
            if "already" in msg_in or "registered" in msg_in:
                return {"ok": False, "message": "Account already exists. Please login.", "already_exists": True}
            if "rate limit" in msg_in:
                return {
                    "ok": False,
                    "message": "Too many signup attempts. Please wait a few minutes, or login if this account already exists.",
                    "rate_limited": True,
                }
            # Fallback: still treat as no session
            if user_id:
                return {"ok": False, "message": "Account created. Please login to finish setup.", "missing_session": True}
            return {"ok": False, "message": "Could not create demo admin account.", "debug": str(exc_in)}

    except Exception as exc:
        msg = str(exc).lower()
        if "already" in msg or "registered" in msg or "exists" in msg:
            return {"ok": False, "message": "Account already exists. Please login.", "already_exists": True}
        if "rate limit" in msg:
            return {
                "ok": False,
                "message": "Too many signup attempts. Please wait a few minutes, or login if this account already exists.",
                "rate_limited": True,
            }
        return {"ok": False, "message": "Could not create demo admin account.", "debug": str(exc)}


def _activate_demo_subscription(institute_id: str, plan_code: str = "demo") -> tuple[bool, str]:
    db = get_supabase_client()
    if not db or not institute_id:
        return False, "Supabase is not configured. Add .streamlit/secrets.toml."

    try:
        plan_rows = (
            db.table("plans")
            .select("id,billing_cycle")
            .eq("plan_code", plan_code)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not plan_rows:
            return False, "Missing demo plan."

        existing = (
            db.table("subscriptions")
            .select("id,status")
            .eq("institute_id", institute_id)
            .eq("plan_id", plan_rows[0]["id"])
            .limit(1)
            .execute()
            .data
            or []
        )
        if existing:
            return True, ""

        now = dt.datetime.now(dt.timezone.utc)
        payload = {
            "institute_id": institute_id,
            "plan_id": plan_rows[0]["id"],
            "billing_cycle": plan_rows[0].get("billing_cycle") or "forever",
            "status": "active",
            "starts_at": now.isoformat(),
            "ends_at": (now + dt.timedelta(days=3650)).isoformat(),
        }
        db.table("subscriptions").insert(payload).execute()
        return True, ""
    except Exception as exc:
        return False, "Demo subscription could not be created."


def _set_demo_session(
    *,
    institute: dict[str, Any],
    admin_name: str,
    admin_email: str,
    auth_user_id: str,
    plan_code: str,
) -> None:
    institute_id = institute.get("id")
    set_active_institute(institute)
    st.session_state.logged_in = True
    st.session_state.portal = "admin"
    st.session_state.role = "admin"
    st.session_state.admin_name = admin_name
    st.session_state.admin_email = admin_email
    st.session_state.user_name = admin_name
    st.session_state.user_email = admin_email
    st.session_state.email = admin_email
    if auth_user_id:
        st.session_state.auth_user_id = auth_user_id
        st.session_state.user_id = auth_user_id
    st.session_state.institute_id = institute_id
    st.session_state.active_institute_id = institute_id
    st.session_state.active_institute_name = institute.get("name", "")
    st.session_state.current_institute = institute
    st.session_state.selected_plan = plan_code
    st.session_state.selected_plan_code = plan_code

    # Session semantics for dashboard setup.
    st.session_state.subscription_status = "demo" if plan_code == "demo" else "pending_payment"

    st.session_state.admin_onboarding_completed = True
    if plan_code == "demo":
        st.session_state.page = "institute_dashboard"
        st.session_state.institute_page = "institute_dashboard"
    else:
        st.session_state.page = "payment"
        st.session_state.current_page = "payment"


def show_demo_signup() -> None:
    init_institute_state()
    if "demo_signup_in_progress" not in st.session_state:
        st.session_state["demo_signup_in_progress"] = False
    render_public_nav(show_links=False)

    if st.button("Back to Pricing", key="demo_signup_back"):
        st.session_state.page = "pricing"
        st.rerun()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        selected_plan_code = str(st.session_state.get("selected_plan_code") or st.session_state.get("selected_plan") or "demo").strip().lower()
        selected_plan_code = selected_plan_code if selected_plan_code in {"demo", "starter", "pro", "enterprise"} else "demo"

        titles = {
            "demo": "Try Demo",
            "starter": "Subscribe to Starter Plan",
            "pro": "Subscribe to Pro Plan",
            "enterprise": "Subscribe to Enterprise Plan",
        }
        subtitles = {
            "demo": "Create a demo institute account. No institute access code required.",
            "starter": "Create your institute account and continue to payment.",
            "pro": "Create your institute account and continue to payment.",
            "enterprise": "Create your institute account and continue to payment.",
        }
        buttons = {
            "demo": "Create Demo Account",
            "starter": "Create Institute & Continue to Payment",
            "pro": "Create Institute & Continue to Payment",
            "enterprise": "Create Institute & Continue to Payment",
        }

        in_progress = bool(st.session_state.get("demo_signup_in_progress", False))
        st.markdown(f"## {titles.get(selected_plan_code, titles['demo'])}")
        st.caption(subtitles.get(selected_plan_code, subtitles["demo"]))

        with st.form("demo_signup_form"):

            institute_name = st.text_input("Institute Name *", placeholder="Sunrise Coaching Centre")
            admin_name = st.text_input("Admin Name *", placeholder="Priya Sharma")
            admin_email = st.text_input("Admin Email *", placeholder="admin@institute.com")
            admin_password = st.text_input("Admin Password *", type="password")
            c1, c2 = st.columns(2)
            city = c1.text_input("City *", placeholder="Delhi")
            state = c2.text_input("State *", placeholder="Delhi")
            phone = st.text_input("Phone", placeholder="+91 98765 43210")

            submitted = st.form_submit_button(
                buttons.get(selected_plan_code, buttons["demo"]),
                type="primary",
                use_container_width=True,
                disabled=in_progress,
            )

        if not submitted:
            st.markdown("---")
            st.caption("Already received an institute access code?")
            join_left, join_mid, join_right = st.columns([1, 1.4, 1])
            with join_mid:
                if st.button("Join Institute with Code", key="demo_join_institute", use_container_width=True):
                    st.session_state.return_to = "pricing"
                    st.session_state.page = "institute_join"
                    st.rerun()
            return

        errors = _validate_demo_form(
            institute_name=institute_name,
            admin_name=admin_name,
            admin_email=admin_email,
            admin_password=admin_password,
            city=city,
            state=state,
        )
        if errors:
            st.error(" ".join(errors))
            return

        if st.session_state.get("signup_in_progress"):
            # Prevent double-submit while processing.
            return

        st.session_state["demo_signup_in_progress"] = True
        st.session_state["signup_in_progress"] = True
        admin_email = admin_email.strip().lower()

        subscription_status = "demo" if selected_plan_code == "demo" else "pending_payment"

        result = create_or_continue_admin_onboarding(
            email=admin_email,
            password=admin_password,
            institute_name=institute_name,
            admin_name=admin_name,
            city=city,
            state=state,
            phone=phone,
            selected_plan_code=selected_plan_code,
        )

        if not result.get("ok"):
            _finish_progress()
            st.session_state["signup_in_progress"] = False

            message = result.get("message") or "Could not create demo account."
            if result.get("account_exists"):
                st.warning(message)
                _render_existing_account_actions()
                return

            st.error(message)
            if result.get("rate_limited"):
                _render_existing_account_actions()
            return

        st.session_state["signup_in_progress"] = False



        _set_demo_session(
            institute=result.get("institute") or {},
            admin_name=result.get("name") or admin_name,
            admin_email=result.get("email") or admin_email,
            auth_user_id=str(result.get("auth_user_id") or ""),
            plan_code=selected_plan_code if selected_plan_code in {"demo", "starter", "pro", "enterprise"} else "demo",
        )

        st.session_state["selected_plan_code"] = selected_plan_code
        st.session_state["subscription_status"] = subscription_status

        _finish_progress()
        st.rerun()
