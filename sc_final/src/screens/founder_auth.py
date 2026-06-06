"""Founder / SnapClass HQ auth screen."""
import streamlit as st
from src.components.public_nav import render_public_nav
from src.components.navigation import go_to, render_back_to_home
from src.database.client import get_supabase, get_supabase_error
from src.services.auth_service import (
    EMAIL_NOT_CONFIRMED_MESSAGE,
    LOCAL_EMAIL_CONFIRMATION_HINT,
    PROFILE_NOT_FOUND_MESSAGE,
    apply_supabase_session,
    classify_supabase_auth_error,
    demo_auth_enabled,
)

# NOTE: Never render real founder credentials in production.
FOUNDER_EMAIL = "founder@snapclass.ai"
FOUNDER_PASSWORD = "founder@123"


def _is_local_env() -> bool:
    """True when running locally/dev; used to decide whether demo credentials can be shown."""
    import os
    import tomllib
    from pathlib import Path

    # APP_ENV can be set by deploy; default to empty.
    app_env = str(os.getenv("APP_ENV") or "").strip().lower()

    # In local runs, app-local Streamlit secrets may also contain APP_ENV.
    secrets_path = Path(__file__).resolve().parents[2] / ".streamlit" / "secrets.toml"
    file_secrets: dict[str, object] = {}
    if secrets_path.exists():
        try:
            with secrets_path.open("rb") as fh:
                file_secrets = tomllib.load(fh)
        except Exception:
            file_secrets = {}

    if not app_env:
        file_env = str(file_secrets.get("APP_ENV", "")).strip().lower()
        app_env = file_env

    return app_env in {"local", "dev", "development"}


def _first_user_profile(db, column: str, value: str):
    if not value:
        return None

    res = (
        db.table("user_profiles")
        .select("*")
        .eq(column, value)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    return rows[0] if rows else None


def _clear_rejected_auth(db) -> None:
    try:
        db.auth.sign_out()
    except Exception:
        pass
    for key in (
        "user_id",
        "auth_user_id",
        "user_email",
        "email",
        "institute_id",
        "role",
        "user_name",
        "founder_logged_in",
        "logged_in",
        "portal",
    ):
        st.session_state.pop(key, None)


def _login_founder(email: str, password: str) -> tuple[bool, str]:
    email_norm = (email or "").strip().lower()
    password = (password or "")

    db = get_supabase()
    if db is None:
        return False, get_supabase_error() or "Supabase is not configured. Add .streamlit/secrets.toml."

    try:
        auth = db.auth.sign_in_with_password({"email": email_norm, "password": password})
        apply_supabase_session(db, auth)
    except Exception as exc:
        classified = classify_supabase_auth_error(exc)
        return False, classified["message"]

    user = getattr(auth, "user", None)
    auth_user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
    user_email = (getattr(user, "email", None) or email_norm).strip().lower()
    if not auth_user_id:
        _clear_rejected_auth(db)
        return False, PROFILE_NOT_FOUND_MESSAGE

    profile = None
    try:
        profile = _first_user_profile(db, "user_id", str(auth_user_id))
        if not profile:
            profile = _first_user_profile(db, "email", user_email)
            if profile and profile.get("user_id") in (None, "", "None"):
                db.table("user_profiles").update({"user_id": str(auth_user_id)}).eq(
                    "email", user_email
                ).execute()
                profile["user_id"] = str(auth_user_id)
    except Exception:
        profile = None

    if not profile:
        _clear_rejected_auth(db)
        return False, PROFILE_NOT_FOUND_MESSAGE

    role = str(profile.get("role") or "").strip().lower()
    if role not in {"founder", "super_admin"}:
        _clear_rejected_auth(db)
        return False, "Founder role not assigned. Contact system owner."

    # Routing in app.py checks role == "founder".
    # Keep the portal role unified, but do not change authorization logic.
    st.session_state.user_id = str(auth_user_id)
    st.session_state.auth_user_id = str(auth_user_id)
    st.session_state.user_email = user_email
    st.session_state.email = user_email
    st.session_state.institute_id = profile.get("institute_id")
    # Keep role marker so downstream routing can decide what to show.
    st.session_state.role = "founder" if role == "founder" else "super_admin"

    st.session_state.user_name = profile.get("full_name") or "Founder"
    st.session_state.founder_logged_in = True
    st.session_state.logged_in = True
    st.session_state.portal = "founder"
    st.session_state.founder_page = "founder_dashboard"
    st.session_state.page = "founder_dashboard"
    return True, ""



def show_founder_auth():
    render_public_nav(show_links=False)
    render_back_to_home(key="fa_back")
    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
        <div class="sc-card" style="text-align:center;padding:36px;margin-bottom:20px;">
        <div style="font-size:3rem;margin-bottom:12px;">⚡</div>
          <h2 style="margin:0 0 4px;">SnapClass HQ</h2>
          <p style="color:#6B7280;margin:0;">
            This portal is only for SnapClass HQ and internal super admins.
          </p>
          <p style="color:#6B7280;margin:10px 0 0;">
            If you are a school/coaching admin, teacher, or student, use your correct portal.
          </p>
        </div>""", unsafe_allow_html=True)
        # Quick navigation (prevents confusion if someone lands here accidentally)
        nav_cols = st.columns(2)
        with nav_cols[0]:
            if st.button("🏫 Institute Login", key="fa_go_institute", use_container_width=True):
                go_to("institute_login")
        with nav_cols[1]:
            if st.button("👩‍🏫 Teacher Login", key="fa_go_teacher", use_container_width=True):
                go_to("teacher_auth")

        nav_cols2 = st.columns(2)
        with nav_cols2[0]:
            if st.button("🎓 Student Login", key="fa_go_student", use_container_width=True):
                go_to("student_auth")
        with nav_cols2[1]:
            if st.button("↩ Back to Home", key="fa_go_home", use_container_width=True):
                go_to("landing")

        st.divider()

        email = st.text_input("Email", placeholder="founder@snapclass.ai", key="fl_email")
        pwd   = st.text_input("Password", placeholder="••••••••", key="fl_pwd", type="password")

        # Hide demo credentials on production.
        if demo_auth_enabled() and _is_local_env():
            st.caption(f"Local demo: {FOUNDER_EMAIL} / {FOUNDER_PASSWORD}")
        else:
            st.caption("Use your Supabase-auth mapped founder account.")


        if st.button("Access SnapClass HQ", type="primary", use_container_width=True, key="founder_go"):
            ok, message = _login_founder(email, pwd)
            if ok:
                st.rerun()
            else:
                st.error(message)
                if message == EMAIL_NOT_CONFIRMED_MESSAGE and _is_local_env():
                    with st.expander("Developer Debug", expanded=False):
                        st.info(LOCAL_EMAIL_CONFIRMATION_HINT)
