from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.database.client import get_supabase


def save_user_profile(
    *,
    email: str,
    full_name: str,
    role: str,
    subject: str | None = None,
    roll_no: str | None = None,
    class_name: str | None = None,
    user_id: str | None = None,
) -> Dict[str, Any]:
    """Save/replace user_profiles row without relying on ON CONFLICT constraints."""
    db = get_supabase()
    if not db:
        return {"ok": False, "error": "Supabase is not connected."}

    email_norm = (email or "").strip().lower()
    if not email_norm:
        return {"ok": False, "error": "Email is required."}

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
    }


    try:
        existing = (
            db.table("user_profiles").select("*").eq("email", email_norm).execute()
        )
        if existing.data:
            response = db.table("user_profiles").update(payload).eq("email", email_norm).execute()
        else:
            response = db.table("user_profiles").insert(payload).execute()

        return {"ok": True, "data": getattr(response, "data", None)}
    except Exception as e:
        # Safe error: do not include secrets; just return the message.
        return {"ok": False, "error": str(e)}





def ensure_student_row(
    *,
    email: str,
    full_name: str,
    roll_no: str | None = None,
    class_name: str | None = None,
    user_id: str | None = None,
) -> Dict[str, Any]:
    """Ensure a public.students row exists for student identity resolver.

    MVP rule: student login email must match public.students.email.
    """
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
        return None, {"ok": False, "message": "Supabase not configured."}
    return db, None


def _get_user_id(user: Any) -> Optional[str]:
    if user is None:
        return None
    return getattr(user, "id", None) or getattr(user, "user_id", None)


def _extract_user_metadata(user: Any) -> Dict[str, Any]:
    if user is None:
        return {}
    meta = getattr(user, "user_metadata", None) or getattr(user, "metadata", None) or {}
    return meta if isinstance(meta, dict) else {}


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    db = get_supabase()
    if db is None:
        return None
    try:
        res = (
            db.table("user_profiles")
            .select("user_id,email,full_name,role,institute_id,roll_no,class_name,subject,created_at")
            .eq("user_id", user_id)
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

    # Normalize email for both auth and profile upsert.
    email = (email or "").strip().lower()
    full_name = (name or "").strip()
    extra_profile = extra_profile or {}

    try:
        # Creates real account in Supabase Auth
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
            # Some client versions may return a different shape; treat as failure.
            return {"ok": False, "message": "Registration failed: user id missing."}

        # Build user_profiles payload.
        # IMPORTANT: user_profiles.id (PK) MUST equal auth.users.id.
        # Also keep user_profiles.user_id consistent for any foreign keys/queries.
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


        # Teacher profile
        subject = extra_profile.get("subject")
        if role == "teacher":
            profile_payload["subject"] = subject.strip() if isinstance(subject, str) and subject.strip() else None

        # Student profile
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
        )

        if not profile_resp.get("ok"):
            return {
                "ok": False,
                "message": f"Auth created, but profile save failed: {profile_resp.get('error','Profile save failed.')}",
            }

        # Critical PRD fix: student identity resolver uses public.students.id.
        # So student registration must also create/update public.students.
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
        msg = str(e)
        # If email confirmation is enabled, sign_up can still succeed; sign_in later will fail.
        return {"ok": False, "message": msg}



def login_user(email: str, password: str) -> Dict[str, Any]:
    db, err = _db_or_error()
    if err:
        return err

    try:
        result = db.auth.sign_in_with_password({"email": email, "password": password})
        return {"ok": True, "user": result.user, "session": result.session}
    except Exception as e:
        # Keep message granular so UI can show required errors.
        msg = str(e).lower()
        if "invalid login credentials" in msg or "wrong password" in msg:
            return {"ok": False, "message": "Wrong password."}
        if "email" in msg and ("confirm" in msg or "verify" in msg):
            return {"ok": False, "message": "Please verify your email before logging in."}
        if "invalid" in msg and "credentials" in msg:
            return {"ok": False, "message": "Wrong password."}
        return {"ok": False, "message": "Account not found or wrong credentials."}


def verify_student(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify student login.

    Returns dict for UI/session, or None for failure.
    """
    res = login_user(email, password)
    if not res.get("ok"):
        return None

    user = res.get("user")
    user_id = _get_user_id(user)
    if not user_id:
        return None

    profile = get_user_profile(user_id)
    if not profile:
        return None

    if profile.get("role") != "student":
        return None

    # Ensure student row exists and fetch public.students.id for the PRD resolver.
    email_norm = (profile.get("email") or email or "").strip().lower()
    roll_no = profile.get("roll_no") or profile.get("roll") or profile.get("user_roll") or ""
    student_row = None
    try:
        ensure_student_row(
            email=email_norm,
            full_name=profile.get("full_name") or "Student",
            roll_no=roll_no,
            class_name=profile.get("class_name") or "",
            user_id=user_id,
        )
        db = get_supabase()
        if db:
            found = db.table("students").select("*").eq("email", email_norm).limit(1).execute()
            if found.data:
                student_row = found.data[0]
    except Exception:
        student_row = None

    return {
        "user_id": user_id,
        "student_id": student_row.get("id") if student_row else None,
        "email": email_norm,
        "name": (student_row or {}).get("name") or profile.get("full_name") or "Student",
        "roll": (student_row or {}).get("roll_no") or roll_no or "",
        "class_name": (student_row or {}).get("class_name") or profile.get("class_name") or "",
    }


def verify_teacher(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify teacher login."""
    res = login_user(email, password)
    if not res.get("ok"):
        return None

    user = res.get("user")
    user_id = _get_user_id(user)
    if not user_id:
        return None

    profile = get_user_profile(user_id)
    if not profile:
        return None

    if profile.get("role") != "teacher":
        return None

    return {
        "user_id": user_id,
        "email": profile.get("email") or email,
        "name": profile.get("full_name") or "Teacher",
        "subject": profile.get("subject") or "",
    }


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
        return {"ok": False, "message": "Supabase not configured."}
    try:
        db.auth.reset_password_email(email)
        return {"ok": True, "message": "Password reset email sent"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


# Legacy compatibility (kept but no longer used for demo login)

def verify_admin(pwd: str) -> bool:
    return False


def register_student_demo(name: str, email: str, roll: str) -> Dict[str, Any]:
    return {"ok": False, "message": "Demo registration disabled. Use real Register flow."}


def register_teacher_demo(name: str, email: str, subject: str) -> Dict[str, Any]:
    return {"ok": False, "message": "Demo registration disabled. Use real Register flow."}
