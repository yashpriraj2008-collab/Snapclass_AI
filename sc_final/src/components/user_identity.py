"""Reusable user identity UI backed by Supabase Auth profile mappings."""
from __future__ import annotations

import html
from typing import Any

import streamlit as st


ROLE_COLORS = {
    "founder": "#0EA5E9",
    "super_admin": "#0EA5E9",
    "admin": "#8B5CF6",
    "institute_admin": "#8B5CF6",
    "teacher": "#EC4899",
    "student": "#22C55E",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def normalize_role(role: Any) -> str:
    value = _text(role).lower()
    return {
        "super_admin": "founder",
        "institute_admin": "admin",
        "class_teacher": "teacher",
        "subject_teacher": "teacher",
    }.get(value, value or "unknown")


def role_badge(role: Any) -> str:
    normalized = normalize_role(role)
    color = ROLE_COLORS.get(normalized, "#6B7280")
    return (
        f'<span style="background:{color}22;color:{color};padding:6px 12px;'
        f'border-radius:999px;font-weight:700;font-size:13px;">'
        f"{html.escape(normalized.title())}</span>"
    )


def auth_password_is_set(user: dict[str, Any] | None) -> bool:
    """Treat an Auth-linked profile as password-enabled without reading a password."""
    row = user or {}
    return bool(row.get("user_id") or row.get("auth_user_id"))


def password_status_label(user: dict[str, Any] | None) -> str:
    return "Set" if auth_password_is_set(user) else "Not Set"


def render_portal_identity(user: dict[str, Any], institute_name: str = "") -> None:
    name = _text(user.get("full_name") or user.get("name")) or "User"
    email = _text(user.get("email")) or "No email"
    role = normalize_role(user.get("role"))
    institute = _text(institute_name)

    with st.container(border=True):
        details_col, role_col = st.columns([5, 1], vertical_alignment="center")
        with details_col:
            st.markdown(f"#### {name}")
            st.caption(email)
            if institute:
                st.caption(institute)
        with role_col:
            st.markdown(f"**{role.title()}**")


def session_identity(default_role: str, *, institute_name: str = "") -> dict[str, Any]:
    user = st.session_state.get("user")
    user = dict(user) if isinstance(user, dict) else {}
    user.setdefault(
        "full_name",
        st.session_state.get("user_name")
        or st.session_state.get("admin_name")
        or st.session_state.get("teacher_name")
        or st.session_state.get("student_name"),
    )
    user.setdefault(
        "email",
        st.session_state.get("user_email")
        or st.session_state.get("admin_email")
        or st.session_state.get("teacher_email")
        or st.session_state.get("student_email")
        or st.session_state.get("email"),
    )
    user.setdefault("role", st.session_state.get("role") or default_role)
    user.setdefault("user_id", st.session_state.get("auth_user_id") or st.session_state.get("user_id"))
    user["institute_name"] = institute_name
    return user


def render_password_reset(email: str, *, key: str) -> None:
    email_norm = _text(email).lower()
    if st.button("Reset Password", key=key, use_container_width=True, disabled=not email_norm):
        from src.services.auth_service import reset_password

        result = reset_password(email_norm)
        if result.get("ok"):
            st.success("Password reset email sent.")
        else:
            st.error(result.get("message") or "Could not send password reset email.")
