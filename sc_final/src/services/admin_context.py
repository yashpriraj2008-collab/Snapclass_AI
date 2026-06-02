from __future__ import annotations

from typing import Any

import streamlit as st

from src.database.client import get_supabase_client


def _text(value: Any) -> str:
    return str(value or "").strip()


def _session_email() -> str:
    for key in ("admin_email", "user_email", "auth_user_email", "email"):
        value = _text(st.session_state.get(key))
        if value:
            return value.lower()

    user = st.session_state.get("user") or st.session_state.get("auth_user") or {}
    if isinstance(user, dict):
        return _text(user.get("email") or user.get("user_email")).lower()

    return _text(getattr(user, "email", "")).lower()


def _session_user_id() -> str:
    for key in ("auth_user_id", "user_id"):
        value = _text(st.session_state.get(key))
        if value:
            return value
    return ""


def _candidate_session_ids() -> list[str]:
    current = st.session_state.get("current_institute") or {}
    current_id = current.get("id") if isinstance(current, dict) else ""
    candidates = [
        st.session_state.get("active_institute_id"),
        st.session_state.get("institute_id"),
        st.session_state.get("current_institute_id"),
        current_id,
    ]

    seen: set[str] = set()
    normalized: list[str] = []
    for candidate in candidates:
        value = _text(candidate)
        if value and value not in seen:
            seen.add(value)
            normalized.append(value)
    return normalized


def _fetch_profile_institute_id() -> str:
    db = get_supabase_client()
    if not db:
        return ""

    user_id = _session_user_id()
    email = _session_email()
    lookups = []
    if user_id:
        lookups.extend((("user_id", user_id), ("id", user_id)))
    if email:
        lookups.append(("email", email))

    for column, value in lookups:
        try:
            rows = (
                db.table("user_profiles")
                .select("id,user_id,email,role,institute_id,status")
                .eq(column, value)
                .limit(1)
                .execute()
                .data
                or []
            )
        except Exception:
            continue

        if not rows:
            continue

        profile = rows[0]
        role = _text(profile.get("role")).lower()
        if role in {"admin", "institute_admin", "founder"}:
            institute_id = _text(profile.get("institute_id"))
            if institute_id:
                return institute_id

    return ""


def _remember_institute_id(institute_id: str) -> str:
    institute_id = _text(institute_id)
    if not institute_id:
        return ""

    st.session_state["active_institute_id"] = institute_id
    st.session_state["institute_id"] = institute_id
    st.session_state["current_institute_id"] = institute_id

    current = st.session_state.get("current_institute")
    if isinstance(current, dict):
        current["id"] = institute_id
        st.session_state["current_institute"] = current

    return institute_id


def get_current_institute_id() -> str:
    """Return the institute id all admin pages should use.

    The resolver first uses the session id set during admin login/join/demo
    setup. If that is absent, it repairs the session from the logged-in admin's
    user_profiles row.
    """
    candidates = _candidate_session_ids()
    if len(candidates) == 1:
        return _remember_institute_id(candidates[0])

    profile_institute_id = _fetch_profile_institute_id()
    if profile_institute_id:
        return _remember_institute_id(profile_institute_id)

    if candidates:
        return _remember_institute_id(candidates[0])

    return ""
