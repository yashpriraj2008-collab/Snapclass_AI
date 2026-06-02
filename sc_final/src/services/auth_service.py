from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.database.client import get_supabase
from src.utils.constants import DEMO_STUDENT, DEMO_TEACHER

EMAIL_NOT_CONFIRMED_MESSAGE = "Email not confirmed. Please verify your email or contact admin."
INVALID_CREDENTIALS_MESSAGE = "Invalid email or password."
PROFILE_NOT_FOUND_MESSAGE = "Profile not found. Contact admin."
LOCAL_EMAIL_CONFIRMATION_HINT = "Email confirmation may be enabled in Supabase. Turn it off for local testing."
AUTH_USER_PENDING_MESSAGE = (
    "Login account not created yet. Ask user to sign up with this email "
    "or create Auth user in Supabase."
)


def classify_supabase_auth_error(exc: Exception | str) -> Dict[str, str]:
    """Map Supabase Auth errors to safe user-facing messages."""
    raw = str(exc or "")
    msg = raw.lower().replace("-", "_").replace(" ", "_")

    if "email_not_confirmed" in msg or ("email" in msg and "confirm" in msg):
        return {
            "code": "email_not_confirmed",
            "message": EMAIL_NOT_CONFIRMED_MESSAGE,
            "debug": LOCAL_EMAIL_CONFIRMATION_HINT,
        }

    invalid_markers = (
        "invalid_login_credentials",
        "invalid_credentials",
        "invalid_email_or_password",
        "wrong_password",
        "password",
    )
    if any(marker in msg for marker in invalid_markers):
        return {"code": "invalid_credentials", "message": INVALID_CREDENTIALS_MESSAGE}

    return {"code": "auth_failed", "message": INVALID_CREDENTIALS_MESSAGE}


def apply_supabase_session(db: Any, auth: Any) -> None:
    """Attach the signed-in user's access token to the Supabase client."""
    session = getattr(auth, "session", None)
    access_token = getattr(session, "access_token", None)
    if access_token:
        try:
            db.postgrest.auth(access_token)
        except Exception:
            pass


def _demo_email_matches(value: str, expected: str) -> bool:
    return (value or "").strip().lower() == expected.strip().lower()


def demo_auth_enabled() -> bool:
    """Allow built-in demo credentials only when explicitly enabled.

    Production deployments must set APP_ENV=production or DEMO_AUTH_ENABLED=false
    in Streamlit secrets/environment. The default remains demo-friendly for local
    development so the app can still be explored without Supabase Auth users.
    """
    import os
    import tomllib
    from pathlib import Path

    secrets_path = Path(__file__).resolve().parents[2] / ".streamlit" / "secrets.toml"
    file_secrets: dict[str, Any] = {}
    if secrets_path.exists():
        try:
            with secrets_path.open("rb") as fh:
                file_secrets = tomllib.load(fh)
        except Exception:
            file_secrets = {}

    app_env = str(os.getenv("APP_ENV") or file_secrets.get("APP_ENV", "") or "").strip().lower()
    if app_env in {"prod", "production"}:
        return False

    value = os.getenv("DEMO_AUTH_ENABLED")
    if value is None:
        value = file_secrets.get("DEMO_AUTH_ENABLED", "true")
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def _get_public_row(table: str, email: str) -> Optional[Dict[str, Any]]:
    db = get_supabase()
    if db is None:
        return None
    try:
        res = (
            db.table(table).select("*").eq("email", email.strip().lower()).limit(1).execute()
        )
        rows = res.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def _verify_demo_student(email: str, password: str) -> Optional[Dict[str, Any]]:
    if not (
        _demo_email_matches(email, DEMO_STUDENT["email"])
        and password == DEMO_STUDENT["password"]
    ):
        return None

    row = _get_public_row("students", DEMO_STUDENT["email"]) or {}
    return {
        "user_id": row.get("user_id") or row.get("id") or "demo-student",
        "student_id": row.get("id"),
        "email": DEMO_STUDENT["email"],
        "name": row.get("name") or DEMO_STUDENT["name"],
        "roll": row.get("roll_no") or DEMO_STUDENT["roll"],
        "class_name": row.get("class_name") or DEMO_STUDENT["class_name"],
    }


def _verify_demo_teacher(email: str, password: str) -> Optional[Dict[str, Any]]:
    if not (
        _demo_email_matches(email, DEMO_TEACHER["email"])
        and password == DEMO_TEACHER["password"]
    ):
        return None

    row = _get_public_row("teachers", DEMO_TEACHER["email"]) or {}
    return {
        "user_id": row.get("id") or row.get("user_id") or "demo-teacher",
        "email": DEMO_TEACHER["email"],
        "name": row.get("name") or DEMO_TEACHER["name"],
        "subject": row.get("subject") or DEMO_TEACHER["subject"],
    }


def save_user_profile(
    *,
    email: str,
    full_name: str,
    role: str,
    subject: str | None = None,
    roll_no: str | None = None,
    class_name: str | None = None,
    user_id: str | None = None,
    institute_id: str | None = None,
    status: str = "active",
) -> Dict[str, Any]:
    """Save/replace user_profiles row without relying on ON CONFLICT constraints."""
    db = get_supabase()
    if not db:
        return {"ok": False, "error": "Supabase is not configured. Add .streamlit/secrets.toml."}

    email_norm = (email or "").strip().lower()
    if not email_norm:
        return {"ok": False, "error": "Email is required."}
    if not user_id:
        return {"ok": False, "error": AUTH_USER_PENDING_MESSAGE, "pending_auth": True}

    # user_profiles.id is the PK and MUST equal auth.users.id
    payload = {
        "id": user_id,
        "email": email_norm,
        "full_name": (full_name or "").strip(),
        "role": role,
        "subject": (subject or "").strip() if subject else None,
        "roll_no": (roll_no or "").strip() if roll_no else None,
        "class_name": (class_name or "").strip() if class_name else None,
        "user_id": user_id,
        "institute_id": institute_id,
        "status": status,
    }

    try:
        existing = db.table("user_profiles").select("*").eq("email", email_norm).execute()
        if existing.data:
            response = (
                db.table("user_profiles").update(payload).eq("email", email_norm).execute()
            )
        else:
            response = db.table("user_profiles").insert(payload).execute()

        return {"ok": True, "data": getattr(response, "data", None)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ensure_user_profile_for_existing_auth_user(
    *,
    email: str,
    role: str,
    institute_id: str | None = None,
    status: str = "active",
) -> Dict[str, Any]:
    """Create/update user_profiles only when a real Auth user id is known.

    public.user_profiles.id is commonly constrained to auth.users.id, so admin
    setup flows must not insert random ids. With the anon Supabase client we
    cannot safely list or create other Auth users; the only reliable signal
    available in the app is an existing Auth-backed profile row.
    """
    db = get_supabase()
    if not db:
        return {"ok": False, "message": "Supabase is not configured. Add .streamlit/secrets.toml."}

    email_norm = (email or "").strip().lower()
    role_norm = (role or "").strip().lower()
    if not email_norm:
        return {"ok": False, "message": "Email is required."}
    if not role_norm:
        return {"ok": False, "message": "Role is required."}

    try:
        existing_res = (
            db.table("user_profiles")
            .select("*")
            .eq("email", email_norm)
            .limit(1)
            .execute()
        )
        rows = existing_res.data or []
        existing = rows[0] if rows else None
    except Exception as exc:
        return {"ok": False, "message": "Profile lookup failed.", "debug": str(exc)}

    auth_user_id = ""
    if existing:
        auth_user_id = str(existing.get("user_id") or existing.get("id") or "").strip()

    if not auth_user_id:
        return {
            "ok": False,
            "pending_auth": True,
            "message": AUTH_USER_PENDING_MESSAGE,
        }

    payload: Dict[str, Any] = {
        "id": auth_user_id,
        "user_id": auth_user_id,
        "email": email_norm,
        "role": role_norm,
        "institute_id": institute_id,
        "status": status,
    }

    try:
        if existing:
            db.table("user_profiles").update(payload).eq("email", email_norm).execute()
        else:
            db.table("user_profiles").insert(payload).execute()

        refreshed = (
            db.table("user_profiles")
            .select("*")
            .eq("email", email_norm)
            .limit(1)
            .execute()
        )
        data = refreshed.data or []
        return {"ok": True, "profile": data[0] if data else payload}
    except Exception as exc:
        return {"ok": False, "message": "Profile mapping failed.", "debug": str(exc)}


def ensure_student_row(
    *,
    email: str,
    full_name: str,
    roll_no: str | None = None,
    class_name: str | None = None,
    user_id: str | None = None,
) -> Dict[str, Any]:
    """Ensure a public.students row exists for student identity resolver."""
    db = get_supabase()
    if not db:
        return {"ok": False, "error": "Supabase is not connected."}

    email_norm = (email or "").strip().lower()
    if not email_norm:
        return {"ok": False, "error": "Email is required."}

    payload = {
        "email": email_norm,
        "name": (full_name or "Student").strip() or "Student",
        "roll_no": (roll_no or "").strip() or None,
        "class_name": (class_name or "").strip() or None,
        "status": "active",
    }

    try:
        existing = (
            db.table("students")
            .select("id")
            .eq("email", email_norm)
            .limit(1)
            .execute()
        )
        if existing.data:
            db.table("students").update(payload).eq("email", email_norm).execute()
        else:
            db.table("students").insert(payload).execute()

        res = (
            db.table("students")
            .select("*")
            .eq("email", email_norm)
            .limit(1)
            .execute()
        )
        return {"ok": True, "data": getattr(res, "data", None)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# -----------------------------------------------------------------------------
# Low-level helpers
# -----------------------------------------------------------------------------

def _db_or_error() -> Tuple[Optional[Any], Optional[Dict[str, str]]]:
    db = get_supabase()
    if db is None:
        return None, {"ok": False, "message": "Supabase is not configured. Add .streamlit/secrets.toml."}
    return db, None


def _get_user_id(user: Any) -> Optional[str]:
    if user is None:
        return None
    return getattr(user, "id", None) or getattr(user, "user_id", None)


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    db = get_supabase()
    if db is None:
        return None
    try:
        res = (
            db.table("user_profiles")
            .select(
                "user_id,email,full_name,role,institute_id,roll_no,class_name,subject,created_at"
            )
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        data = res.data or []
        return data[0] if data else None
    except Exception:
        return None


def get_user_profile_by_email(email: str) -> Optional[Dict[str, Any]]:
    db = get_supabase()
    if db is None:
        return None

    email_norm = (email or "").strip().lower()
    if not email_norm:
        return None

    try:
        res = (
            db.table("user_profiles")
            .select("*")
            .eq("email", email_norm)
            .limit(1)
            .execute()
        )
        data = res.data or []
        return data[0] if data else None
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Public auth functions
# -----------------------------------------------------------------------------

def register_user(

    email: str,
    password: str,
    name: str,
    role: str,
    *,
    institute_id: Optional[str] = None,
    extra_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Register Supabase Auth user and upsert into user_profiles."""
    db, err = _db_or_error()
    if err:
        return err

    email = (email or "").strip().lower()
    full_name = (name or "").strip()
    extra_profile = extra_profile or {}

    try:
        result = db.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"full_name": full_name, "role": role, **extra_profile}},
            }
        )

        user = getattr(result, "user", None) or getattr(result, "data", {}).get("user")
        user_id = _get_user_id(user)
        if not user_id:
            return {"ok": False, "message": "Registration failed: user id missing."}

        profile_payload: Dict[str, Any] = {
            "id": user_id,
            "full_name": full_name,
            "email": email,
            "subject": None,
            "roll_no": None,
            "class_name": None,
            "role": role,
            "user_id": user_id,
            "institute_id": institute_id,
        }

        subject = extra_profile.get("subject")
        if role == "teacher":
            profile_payload["subject"] = subject.strip() if isinstance(subject, str) and subject.strip() else None

        roll_no = extra_profile.get("roll") or extra_profile.get("roll_no")
        class_name = extra_profile.get("class_name")
        if role == "student":
            profile_payload["roll_no"] = roll_no.strip() if isinstance(roll_no, str) and roll_no.strip() else None
            profile_payload["class_name"] = (
                class_name.strip() if isinstance(class_name, str) and class_name.strip() else None
            )

        profile_resp = save_user_profile(
            email=email,
            full_name=full_name,
            role=role,
            subject=profile_payload.get("subject"),
            roll_no=profile_payload.get("roll_no"),
            class_name=profile_payload.get("class_name"),
            user_id=user_id,
            institute_id=institute_id,
            status="active",
        )

        if not profile_resp.get("ok"):
            return {
                "ok": False,
                "message": f"Auth created, but profile save failed: {profile_resp.get('error','Profile save failed.')}",
            }

        if role == "student":
            student_resp = ensure_student_row(
                email=email,
                full_name=full_name,
                roll_no=profile_payload.get("roll_no"),
                class_name=profile_payload.get("class_name"),
                user_id=user_id,
            )
            if not student_resp.get("ok"):
                return {
                    "ok": False,
                    "message": f"Auth/profile created, but student row save failed: {student_resp.get('error','Student row save failed.')}",
                }

        return {"ok": True, "user": user}

    except Exception as e:
        return {"ok": False, "message": str(e)}


def login_user(email: str, password: str) -> Dict[str, Any]:
    db, err = _db_or_error()
    if err:
        return err

    try:
        result = db.auth.sign_in_with_password({"email": email, "password": password})
        apply_supabase_session(db, result)
        return {"ok": True, "user": result.user, "session": result.session}
    except Exception as e:
        return {"ok": False, **classify_supabase_auth_error(e)}


def verify_student(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate and resolve a student account.

    Required behavior:
    - authenticate with Supabase Auth
    - get auth_user_id and auth_user_email
    - find user_profiles by user_id first, fallback email
    - confirm role = student
    - find students row by user_id first, fallback email
    - set required st.session_state keys
    - if profile/student exists by email but user_id is null, update it
    - clear role error message when not a student
    - do not show raw database errors
    - include Developer Debug expander
    """
    import streamlit as st

    db = get_supabase()
    if db is None:
        return {"ok": False, "message": "Supabase is not configured. Add .streamlit/secrets.toml."}

    email_norm_input = (email or "").strip().lower()

    login_res = login_user(email_norm_input, password)
    if not login_res.get("ok"):
        return login_res

    auth_user = login_res.get("user")
    auth_user_id = _get_user_id(auth_user)
    auth_user_email = (
        getattr(auth_user, "email", None) or email_norm_input
    )
    auth_user_email = (auth_user_email or "").strip().lower()

    if not auth_user_id or not auth_user_email:
        return {"ok": False, "message": PROFILE_NOT_FOUND_MESSAGE}

    profile_found = False
    profile_role: str = ""
    student_found = False
    student_id: Optional[str] = None

    # 1) Resolve user_profiles by user_id first, fallback email
    try:
        profile_row = (
            db.table("user_profiles")
            .select("*")
            .eq("user_id", str(auth_user_id))
            .limit(1)
            .execute()
        )
        rows = profile_row.data or []
        profile = rows[0] if rows else None
    except Exception:
        profile = None

    if not profile:
        try:
            profile_row = (
                db.table("user_profiles")
                .select("*")
                .eq("email", auth_user_email)
                .limit(1)
                .execute()
            )
            rows = profile_row.data or []
            profile = rows[0] if rows else None
        except Exception:
            profile = None

    # If exists by email but user_id is null, update user_profiles.user_id
    if profile and (profile.get("user_id") in (None, "", "None")):
        try:
            db.table("user_profiles").update({"user_id": str(auth_user_id)}).eq(
                "email", auth_user_email
            ).execute()
            profile["user_id"] = str(auth_user_id)
        except Exception:
            pass

    profile_found = bool(profile)
    if profile:
        profile_role = str(profile.get("role") or "").strip().lower()

    # confirm role = student
    if not profile:
        return {"ok": False, "message": PROFILE_NOT_FOUND_MESSAGE}

    if profile_role != "student":
        # Required clear error message
        return {"ok": False, "message": "This account exists but is not registered as a student."}

    # 2) Resolve students row by user_id first, fallback email
    try:
        student_res = (
            db.table("students")
            .select("*")
            .eq("user_id", str(auth_user_id))
            .limit(1)
            .execute()
        )
        rows = student_res.data or []
        student_row = rows[0] if rows else None
    except Exception:
        student_row = None

    if not student_row:
        try:
            student_res = (
                db.table("students")
                .select("*")
                .eq("email", auth_user_email)
                .limit(1)
                .execute()
            )
            rows = student_res.data or []
            student_row = rows[0] if rows else None
        except Exception:
            student_row = None

    # If exists by email but user_id is null, update students.user_id
    if student_row and (student_row.get("user_id") in (None, "", "None")):
        try:
            db.table("students").update({"user_id": str(auth_user_id)}).eq(
                "email", auth_user_email
            ).execute()
            student_row["user_id"] = str(auth_user_id)
        except Exception:
            pass

    if student_row:
        student_found = True
        student_id = student_row.get("id")

    # Required: set st.session_state values
    try:
        institute_id = student_row.get("institute_id") if student_row else profile.get("institute_id")
    except Exception:
        institute_id = profile.get("institute_id")

    user_name = (
        (student_row or {}).get("name")
        or profile.get("full_name")
        or "Student"
    )

    roll_val = None
    if student_row:
        roll_val = student_row.get("roll_no")
    if not roll_val:
        roll_val = profile.get("roll_no") or profile.get("roll") or profile.get("user_roll")

    # Ensure student row exists (best-effort) so My Subjects/Attendance works.
    try:
        ensure_student_row(
            email=auth_user_email,
            full_name=user_name,
            roll_no=roll_val,
            class_name=student_row.get("class_name") if student_row else profile.get("class_name") or "",
            user_id=str(auth_user_id),
        )
        # refresh student row by user_id/email
        student_id = None
        res = (
            db.table("students")
            .select("id,institute_id,name,roll_no,class_name,user_id,email")
            .eq("user_id", str(auth_user_id))
            .limit(1)
            .execute()
        )
        if res.data:
            student_row = res.data[0]
            student_found = True
            student_id = student_row.get("id")
    except Exception:
        pass

    # session state required keys
    st.session_state["auth_user_id"] = str(auth_user_id)
    st.session_state["user_id"] = str(auth_user_id)
    st.session_state["user_email"] = auth_user_email
    st.session_state["email"] = auth_user_email
    st.session_state["role"] = "student"
    st.session_state["student_id"] = str(student_id) if student_id is not None else None
    st.session_state["institute_id"] = institute_id
    st.session_state["user_name"] = str(user_name)
    st.session_state["logged_in"] = True
    st.session_state["portal"] = "student"

    # Developer Debug collapsed
    with st.expander("Developer Debug", expanded=False):
        st.write({
            "auth_user_id": str(auth_user_id),
            "auth_user_email": auth_user_email,
            "profile_found": profile_found,
            "profile_role": profile_role,
            "student_found": student_found,
            "student_id": str(student_id) if student_id is not None else None,
        })

    return {
        "ok": True,
        "auth_user_id": str(auth_user_id),
        "user_id": str(auth_user_id),
        "student_id": str(student_id) if student_id is not None else None,
        "email": auth_user_email,
        "name": str(user_name),
        "roll": str(roll_val) if roll_val is not None else "",
    }



def verify_teacher(email: str, password: str) -> Dict[str, Any]:
    """Authenticate and resolve a teacher account."""
    import streamlit as st

    db = get_supabase()
    if db is None:
        return {"ok": False, "message": "Supabase is not configured. Add .streamlit/secrets.toml."}

    email_norm = (email or "").strip().lower()

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

    # Fetch profile by user_id, then id, then email
    profile = None
    res = db.table("user_profiles").select("*").eq("user_id", auth_user_id).limit(1).execute()
    rows = res.data or []
    profile = rows[0] if rows else None

    if not profile:
        res = db.table("user_profiles").select("*").eq("id", auth_user_id).limit(1).execute()
        rows = res.data or []
        profile = rows[0] if rows else None

    if not profile:
        res = db.table("user_profiles").select("*").eq("email", auth_email).limit(1).execute()
        rows = res.data or []
        profile = rows[0] if rows else None

    if not profile:
        return {"ok": False, "message": PROFILE_NOT_FOUND_MESSAGE}

    allowed_roles = {"teacher", "subject_teacher", "class_teacher"}
    profile_role = str(profile.get("role") or "").strip().lower()
    if profile_role not in allowed_roles:
        return {"ok": False, "message": "This account is not assigned as teacher"}

    if "status" in profile and str(profile.get("status") or "").strip().lower() != "active":
        return {"ok": False, "message": "This teacher account is inactive"}

    # Fetch teachers row by user_id, then email
    teacher_row = None
    res = db.table("teachers").select("*").eq("user_id", auth_user_id).limit(1).execute()
    rows = res.data or []
    teacher_row = rows[0] if rows else None

    if not teacher_row:
        res = db.table("teachers").select("*").eq("email", auth_email).limit(1).execute()
        rows = res.data or []
        teacher_row = rows[0] if rows else None

    if not teacher_row:
        # Required behavior
        return {"ok": False, "message": "Teacher row missing in teachers table"}

    teacher_id = teacher_row.get("id")
    teacher_name = teacher_row.get("name") or profile.get("full_name") or teacher_row.get("name") or "Teacher"
    institute_id = teacher_row.get("institute_id") or profile.get("institute_id")

    # Required: Save session_state values before redirect
    st.session_state["auth_user_id"] = str(auth_user_id)
    st.session_state["user_id"] = str(auth_user_id)
    st.session_state["user_email"] = auth_email
    st.session_state["email"] = auth_email
    st.session_state["user_name"] = str(teacher_name)
    st.session_state["role"] = profile_role
    st.session_state["institute_id"] = institute_id
    st.session_state["teacher_id"] = str(teacher_id)
    st.session_state["logged_in"] = True
    st.session_state["portal"] = "teacher"

    # Ensure teacher_id never None
    if st.session_state.get("teacher_id") in (None, "None", ""):
        return {"ok": False, "message": "Teacher row missing in teachers table"}

    return {
        "ok": True,
        "auth_user_id": str(auth_user_id),
        "user_id": str(auth_user_id),
        "teacher_id": str(teacher_id),
        "email": auth_email,
        "name": str(teacher_name),
        "role": "teacher",
        "profile_role": profile_role,
        "institute_id": institute_id,
        "subject": teacher_row.get("subject") or profile.get("subject") or "",
    }


def login_institute_admin(*, email: str, password: str, name: str, institute_id: str) -> Tuple[bool, str]:
    """Compatibility wrapper for institute admin login.

    Keeps institute-admin mapping logic out of the public student/teacher auth surface.
    """
    from src.services.institute_admin_service import login_institute_admin as _impl

    return _impl(email=email, password=password, name=name, institute_id=institute_id)


def logout_user() -> None:

    db = get_supabase()
    if not db:
        return
    try:
        db.auth.sign_out()
    except Exception:
        pass


def reset_password(email: str) -> Dict[str, Any]:
    db = get_supabase()
    if db is None:
        return {"ok": False, "message": "Supabase is not configured. Add .streamlit/secrets.toml."}
    try:
        db.auth.reset_password_email(email)
        return {"ok": True, "message": "Password reset email sent"}
    except Exception as e:
        classified = classify_supabase_auth_error(e)
        return {
            "ok": False,
            "message": "Could not send password reset email.",
            "debug": classified.get("debug", ""),
        }


# Legacy compatibility (kept but no longer used for demo login)

def verify_admin(pwd: str) -> bool:
    return False


def register_student_demo(name: str, email: str, roll: str) -> Dict[str, Any]:
    return {"ok": False, "message": "Demo registration disabled. Use real Register flow."}


def register_teacher_demo(name: str, email: str, subject: str) -> Dict[str, Any]:
    return {"ok": False, "message": "Demo registration disabled. Use real Register flow."}

