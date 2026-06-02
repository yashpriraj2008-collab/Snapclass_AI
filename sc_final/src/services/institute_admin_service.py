"""Institute admin auth utilities.

Implements:
- Ensure institute admins are real Supabase Auth users
- Ensure user_profiles row maps role/institute_id for RLS helpers

No service-role keys are used.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.database.client import get_supabase
from src.services.auth_service import (
    PROFILE_NOT_FOUND_MESSAGE,
    apply_supabase_session,
    classify_supabase_auth_error,
)
from src.services._institute_admin_auth_helpers import ensure_institute_admin_profile


def _get_user_id(user: Any) -> Optional[str]:
    if user is None:
        return None
    return getattr(user, "id", None) or getattr(user, "user_id", None)


def _fetch_profile(db: Any, *, user_id: str, email: str) -> Optional[Dict[str, Any]]:
    """Resolve user_profiles by auth user_id first, then id, then email."""
    lookups = (
        ("user_id", user_id),
        ("id", user_id),
        ("email", email),
    )
    for column, value in lookups:
        if not value:
            continue
        try:
            rows = (
                db.table("user_profiles")
                .select("*")
                .eq(column, value)
                .limit(1)
                .execute()
                .data
                or []
            )
            if rows:
                return rows[0]
        except Exception:
            continue
    return None


def _fetch_institute(db: Any, institute_id: str) -> Optional[Dict[str, Any]]:
    if not institute_id:
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
        if rows:
            institute = rows[0]
            institute.setdefault("onboarding_completed", False)
            return institute
    except Exception:
        return None
    return None


def authenticate_existing_admin(*, email: str, password: str) -> Dict[str, Any]:
    """Strict existing-admin login.

    This does not create accounts. It signs in with Supabase Auth, resolves the
    admin profile, and returns routing data for the UI.
    """
    db = get_supabase()
    if db is None:
        return {"ok": False, "message": "Supabase is not configured. Add .streamlit/secrets.toml."}

    email_norm = (email or "").strip().lower()
    if not email_norm or not password:
        return {"ok": False, "message": "Enter admin email and password."}

    try:
        auth = db.auth.sign_in_with_password({"email": email_norm, "password": password})
        apply_supabase_session(db, auth)
    except Exception as exc:
        return {"ok": False, **classify_supabase_auth_error(exc)}

    auth_user = getattr(auth, "user", None)
    auth_user_id = _get_user_id(auth_user)
    auth_email = (getattr(auth_user, "email", None) or email_norm).strip().lower()
    if not auth_user_id:
        return {"ok": False, "message": PROFILE_NOT_FOUND_MESSAGE}

    profile = _fetch_profile(db, user_id=str(auth_user_id), email=auth_email)
    if not profile:
        return {"ok": False, "message": PROFILE_NOT_FOUND_MESSAGE}

    role = str(profile.get("role") or "").strip().lower()
    if role in {"teacher", "student", "subject_teacher", "class_teacher"}:
        return {"ok": False, "message": "Please use the Teacher/Student portal."}
    if role not in {"admin", "institute_admin"}:
        return {"ok": False, "message": "This account is not an institute admin."}

    if str(profile.get("status") or "active").strip().lower() not in {"", "active"}:
        return {"ok": False, "message": "This admin account is inactive."}

    institute_id = str(profile.get("institute_id") or "").strip()
    institute = _fetch_institute(db, institute_id)
    name = str(profile.get("full_name") or auth_email.split("@")[0]).strip()

    if not institute_id or not institute:
        return {
            "ok": False,
            "message": "Your institute setup is incomplete. Complete setup to continue.",
            "auth_user_id": str(auth_user_id),
            "email": auth_email,
            "name": name,
            "role": role,
            "profile": profile,
            "institute": institute,
        }

    return {
        "ok": True,
        "needs_setup": not bool(institute.get("onboarding_completed", False)),
        "auth_user_id": str(auth_user_id),
        "email": auth_email,
        "name": name,
        "role": role,
        "profile": profile,
        "institute": institute,
        "institute_id": institute_id,
    }


def login_institute_admin(*, email: str, password: str, name: str, institute_id: str) -> Tuple[bool, str]:
    """Sign in (or create) an institute admin Supabase Auth user.

    Returns (ok, message).
    """
    db = get_supabase()
    if db is None:
        return False, "Supabase is not connected. Add .streamlit/secrets.toml"

    email_norm = (email or "").strip().lower()
    name_norm = (name or "").strip()
    inst = institute_id
    if not email_norm or not password or not name_norm or not inst:
        return False, "Missing institute admin login fields."

    # 1) Try sign in.
    user_id: Optional[str] = None
    try:
        auth = db.auth.sign_in_with_password({"email": email_norm, "password": password})
        user = getattr(auth, "user", None)
        user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
    except Exception as exc:
        auth_error = classify_supabase_auth_error(exc)
        if auth_error.get("code") == "email_not_confirmed":
            return False, auth_error["message"]
        user_id = None

    # 2) If sign-in failed, attempt sign-up.
    if not user_id:
        try:
            sign = db.auth.sign_up(
                {
                    "email": email_norm,
                    "password": password,
                    "options": {"data": {"full_name": name_norm, "role": "institute_admin"}},
                }
            )
            user = getattr(sign, "user", None) or getattr(sign, "data", {}).get("user")
            user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
        except Exception:
            return False, "Unable to sign in or create institute admin account."

    if not user_id:
        return False, "Institute admin user id missing after auth."

    # 3) Upsert user_profiles mapping for RLS.
    profile = ensure_institute_admin_profile(
        user_id=user_id,
        email=email_norm,
        name=name_norm,
        institute_id=inst,
    )
    if not profile.get("ok"):
        return False, profile.get("message") or "Failed to map institute admin profile."

    return True, ""

