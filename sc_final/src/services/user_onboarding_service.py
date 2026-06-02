"""Safe self-registration and invite linking helpers.

These helpers use the public Supabase anon client only. They never require a
service-role key inside Streamlit.
"""
from __future__ import annotations

import datetime as dt
import re
import secrets
import string
from typing import Any

from src.database.client import get_supabase_client
from src.services.auth_service import save_user_profile
from src.services.institute_service import create_institute

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TEACHER_INVITE_CODE_SCHEMA_MESSAGE = (
    "Database schema missing teachers.invite_code. "
    "Run database/fix_teacher_invite_code.sql."
)


def _email(value: str) -> str:
    return (value or "").strip().lower()


def _text(value: Any) -> str:
    return str(value or "").strip()


def _user_id(user: Any) -> str:
    return _text(getattr(user, "id", None) or getattr(user, "user_id", None))


def _code(prefix: str) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return f"{prefix}-" + "".join(secrets.choice(alphabet) for _ in range(8))


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _missing_invite_code_column(error: Any) -> bool:
    raw = str(error or "").lower()
    return (
        "invite_code" in raw
        and (
            "42703" in raw
            or "pgrst204" in raw
            or "schema cache" in raw
            or "does not exist" in raw
            or "could not find" in raw
        )
    )


def _is_expired(value: Any) -> bool:
    stamp = _text(value)
    if not stamp:
        return False
    try:
        expires_at = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except Exception:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=dt.timezone.utc)
    return expires_at < dt.datetime.now(dt.timezone.utc)


def _db_or_message() -> tuple[Any | None, str]:
    db = get_supabase_client()
    if not db:
        return None, "Supabase is not configured. Add .streamlit/secrets.toml."
    return db, ""


def _first(table: str, **eq: Any) -> dict[str, Any] | None:
    db = get_supabase_client()
    if not db:
        return None
    try:
        query = db.table(table).select("*")
        for key, value in eq.items():
            query = query.eq(key, value)
        rows = query.limit(1).execute().data or []
        return rows[0] if rows else None
    except Exception:
        return None


def _profile_by_email(email: str) -> dict[str, Any] | None:
    return _first("user_profiles", email=_email(email))


def _institute_by_id(institute_id: str) -> dict[str, Any] | None:
    institute_id = _text(institute_id)
    if not institute_id:
        return None
    return _first("institutes", id=institute_id)


def _institute_by_name_city_admin_email(
    *,
    name: str,
    city: str,
    admin_email: str,
) -> dict[str, Any] | None:
    db = get_supabase_client()
    if not db:
        return None

    name_norm = _text(name)
    city_norm = _text(city)
    email_norm = _email(admin_email)
    if not name_norm or not city_norm or not email_norm:
        return None

    try:
        rows = (
            db.table("institutes")
            .select("*")
            .eq("name", name_norm)
            .eq("city", city_norm)
            .eq("admin_email", email_norm)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def _update_institute_best_effort(institute: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    db = get_supabase_client()
    institute_id = _text((institute or {}).get("id"))
    if not db or not institute_id:
        return institute

    clean_updates = {key: value for key, value in updates.items() if value not in (None, "")}
    if not clean_updates:
        return institute

    try:
        rows = db.table("institutes").update(clean_updates).eq("id", institute_id).execute().data or []
        return rows[0] if rows else {**institute, **clean_updates}
    except Exception:
        return institute


def safe_sign_up(email: str, password: str) -> dict[str, Any]:
    """Call Supabase Auth sign_up once and normalize common failures."""
    db, message = _db_or_message()
    if not db:
        return {"ok": False, "message": message, "supabase_unavailable": True}

    email_norm = _email(email)
    if not EMAIL_RE.match(email_norm):
        return {"ok": False, "message": "Enter a valid email."}
    if len(password or "") < 8:
        return {"ok": False, "message": "Password must be at least 8 characters."}

    try:
        result = db.auth.sign_up({"email": email_norm, "password": password})
        user = getattr(result, "user", None) or getattr(result, "data", {}).get("user")
        auth_user_id = _user_id(user)
        if not auth_user_id:
            return {"ok": False, "message": "Account could not be created. Please try again."}
        return {"ok": True, "auth_user_id": auth_user_id, "user": user}
    except Exception as exc:
        raw = str(exc)
        msg = raw.lower()
        if "already" in msg or "registered" in msg or "exists" in msg:
            return {
                "ok": False,
                "message": "Account already exists. Please login.",
                "account_exists": True,
            }
        if "rate limit" in msg:
            return {
                "ok": False,
                "message": "Too many signup attempts. Please wait a few minutes, or login if this account already exists.",
                "rate_limited": True,
            }
        return {"ok": False, "message": "Account could not be created. Please try again.", "debug": raw}


def link_user_profile(
    auth_user_id: str,
    email: str,
    name: str,
    role: str,
    institute_id: str,
) -> dict[str, Any]:
    return save_user_profile(
        email=_email(email),
        full_name=_text(name),
        role=_text(role),
        user_id=_text(auth_user_id),
        institute_id=_text(institute_id),
        status="active",
    )


def link_minimal_user_profile(
    auth_user_id: str,
    email: str,
    role: str,
    institute_id: str,
) -> dict[str, Any]:
    db, message = _db_or_message()
    if not db:
        return {"ok": False, "error": message}

    auth_user_id = _text(auth_user_id)
    email_norm = _email(email)
    if not auth_user_id or not email_norm:
        return {"ok": False, "error": "Auth user id and email are required."}

    payload = {
        "id": auth_user_id,
        "user_id": auth_user_id,
        "email": email_norm,
        "role": _text(role),
        "institute_id": _text(institute_id),
        "status": "active",
    }

    try:
        existing = (
            db.table("user_profiles")
            .select("*")
            .eq("id", auth_user_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if existing:
            db.table("user_profiles").update(payload).eq("id", auth_user_id).execute()
        else:
            by_email = (
                db.table("user_profiles")
                .select("*")
                .eq("email", email_norm)
                .limit(1)
                .execute()
                .data
                or []
            )
            if by_email:
                db.table("user_profiles").update(payload).eq("email", email_norm).execute()
            else:
                db.table("user_profiles").insert(payload).execute()

        rows = (
            db.table("user_profiles")
            .select("*")
            .eq("id", auth_user_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        return {"ok": True, "profile": rows[0] if rows else payload}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _get_or_create_institute(form_data: dict[str, Any]) -> dict[str, Any]:
    email_norm = _email(form_data.get("admin_email", ""))
    admin_name = _text(form_data.get("admin_name"))
    institute_name = _text(form_data.get("institute_name"))
    city = _text(form_data.get("city"))
    state = _text(form_data.get("state"))
    phone = _text(form_data.get("phone"))

    existing_profile = _profile_by_email(email_norm)
    profile_institute_id = _text((existing_profile or {}).get("institute_id"))
    existing = _institute_by_id(profile_institute_id)
    if existing:
        return {"ok": True, "data": existing, "reused": True, "source": "profile"}

    existing = _first("institutes", admin_email=email_norm)
    if existing:
        existing = _update_institute_best_effort(
            existing,
            {
                "name": institute_name,
                "city": city,
                "state": state,
                "admin_name": admin_name,
                "admin_email": email_norm,
                "admin_phone": phone,
            },
        )
        return {"ok": True, "data": existing, "reused": True, "source": "admin_email"}

    existing = _institute_by_name_city_admin_email(
        name=institute_name,
        city=city,
        admin_email=email_norm,
    )
    if existing:
        existing = _update_institute_best_effort(
            existing,
            {
                "name": institute_name,
                "city": city,
                "state": state,
                "admin_name": admin_name,
                "admin_email": email_norm,
                "admin_phone": phone,
            },
        )
        return {"ok": True, "data": existing, "reused": True, "source": "name_city_admin_email"}

    selected_plan_code = (form_data.get("selected_plan_code") or "demo").strip().lower()
    plan_label = {"demo": "Demo", "starter": "Starter", "pro": "Pro", "enterprise": "Enterprise"}.get(
        selected_plan_code, "Demo"
    )

    return create_institute(
        name=institute_name,
        city=city,
        state=state,
        institute_type="School",
        admin_name=admin_name,
        admin_email=email_norm,
        admin_phone=phone,
        plan=plan_label,
        status="active",
    )



def _ensure_subscription(institute_id: str, plan_code: str) -> dict[str, Any]:
    db, message = _db_or_message()
    if not db:
        return {"ok": False, "message": message}

    plan_code = (plan_code or "demo").strip().lower()

    try:
        plans = (
            db.table("plans")
            .select("id,billing_cycle")
            .eq("plan_code", plan_code)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not plans:
            return {"ok": False, "message": f"Missing plan: {plan_code}."}

        plan = plans[0]
        existing = (
            db.table("subscriptions")
            .select("id,status")
            .eq("institute_id", institute_id)
            .eq("plan_id", plan["id"])
            .limit(1)
            .execute()
            .data
            or []
        )
        if existing:
            return {"ok": True, "reused": True}

        now = dt.datetime.now(dt.timezone.utc)
        is_trial = plan_code in {"starter", "pro"}

        payload = {
            "institute_id": institute_id,
            "plan_id": plan["id"],
            "billing_cycle": plan.get("billing_cycle") or "monthly",
            "status": "trialing" if is_trial else "active",
            "starts_at": now.isoformat(),
            "ends_at": (now + dt.timedelta(days=14)).isoformat() if is_trial else (now + dt.timedelta(days=14)).isoformat(),
        }
        # For demo, keep it active-like semantics in current schema; trial semantics are handled on UI.
        if not is_trial:
            payload["status"] = "active"

        db.table("subscriptions").insert(payload).execute()
        return {"ok": True}
    except Exception as exc:
        return {
            "ok": False,
            "message": f"Subscription for plan '{plan_code}' could not be created.",
            "debug": str(exc),
        }



def create_or_continue_admin_onboarding(
    email: str,
    password: str,
    institute_name: str,
    admin_name: str,
    city: str,
    state: str,
    phone: str,
    selected_plan_code: str,
) -> dict[str, Any]:
    """Idempotent admin onboarding.

    Auth flow requirements:
    - Try sign_in_with_password first.
    - If login fails due to invalid credentials, sign_up once, then sign_in.
    - If sign_up returns already-registered, instruct user to login.
    - If rate-limited, show rate-limited message (no retries).

    On success:
    - Reuse/create institute (idempotent).
    - Create/update user_profiles (role='admin').
    - Reuse/create subscription (idempotent).

    Never use service_role inside Streamlit.
    """
    db, message = _db_or_message()
    if not db:
        return {"ok": False, "message": message}

    email_norm = _email(email)
    admin_name_norm = _text(admin_name)
    institute_name_norm = _text(institute_name)
    city_norm = _text(city)
    state_norm = _text(state)
    phone_norm = _text(phone)
    selected_plan_norm = (selected_plan_code or "demo").strip().lower()
    if selected_plan_norm not in {"demo", "starter", "pro", "enterprise"}:
        selected_plan_norm = "demo"

    if not email_norm or not password or len(password or "") < 8:
        return {"ok": False, "message": "Please fill all required admin fields."}
    if not admin_name_norm or not institute_name_norm or not city_norm or not state_norm:
        return {"ok": False, "message": "Please fill all required admin fields."}

    # 1) Reuse if profile exists (used for institute reuse + account already exists messaging)
    existing_profile = _profile_by_email(email_norm)

    # 2) Try sign-in first (no sign_up on every attempt)
    try:
        auth_in = db.auth.sign_in_with_password({"email": email_norm, "password": password})
        user = getattr(auth_in, "user", None)
        auth_user_id = _user_id(user)
        if not auth_user_id:
            # treat as session missing; continue to sign_up flow
            raise Exception("Missing auth user id")
    except Exception as exc:
        # Determine whether this is invalid credentials vs other errors.
        msg = str(exc).lower()

        # If invalid login credentials -> sign_up once then sign_in
        invalid_login = (
            "invalid login credentials" in msg
            or "wrong password" in msg
            or ("invalid" in msg and "credentials" in msg)
            or "invalid email or password" in msg
        )

        # Already registered may appear here in some setups; handle as specified.
        if "already" in msg or "registered" in msg or "exists" in msg:
            return {"ok": False, "message": "Account already exists. Please login.", "account_exists": True}

        if "rate limit" in msg:
            return {
                "ok": False,
                "message": "Too many signup attempts. Please wait a few minutes, or login if this account already exists.",
                "rate_limited": True,
            }

        if not invalid_login and existing_profile:
            # If we already have an account mapping but can't sign in, still don't spam sign_up.
            return {"ok": False, "message": "Account already exists. Please login.", "account_exists": True}

        # If invalid credentials -> sign_up once, then sign_in
        try:
            sign = db.auth.sign_up(
                {
                    "email": email_norm,
                    "password": password,
                    "options": {"data": {"full_name": admin_name_norm, "role": "admin"}},
                }
            )
            # After sign_up, immediately sign_in
            auth_in = db.auth.sign_in_with_password({"email": email_norm, "password": password})
            user = getattr(auth_in, "user", None)
            auth_user_id = _user_id(user)
            if not auth_user_id:
                return {"ok": False, "message": "Account created. Please login to finish setup."}
        except Exception as exc2:
            msg2 = str(exc2).lower()
            if "already" in msg2 or "registered" in msg2 or "exists" in msg2:
                return {"ok": False, "message": "Account already exists. Please login.", "account_exists": True}
            if "rate limit" in msg2:
                return {
                    "ok": False,
                    "message": "Too many signup attempts. Please wait a few minutes, or login if this account already exists.",
                    "rate_limited": True,
                }
            # email confirmation issues: treat as missing session
            if "confirm" in msg2 or "verify" in msg2 or "session" in msg2:
                return {"ok": False, "message": "Account created. Please login to finish setup.", "missing_session": True}
            return {"ok": False, "message": "Could not create demo admin account.", "debug": str(exc2)}

    # 3) Create/reuse institute
    institute_result = _get_or_create_institute(
        {
            "institute_name": institute_name_norm,
            "admin_name": admin_name_norm,
            "admin_email": email_norm,
            "city": city_norm,
            "state": state_norm,
            "phone": phone_norm,
            "selected_plan_code": selected_plan_norm,
        }
    )
    if not institute_result.get("ok"):
        return {
            "ok": False,
            "message": "Failed to create institute.",
            "debug": str(institute_result.get("message") or institute_result.get("error") or ""),
        }

    institute = institute_result.get("data") or {}
    institute_id = _text(institute.get("id"))
    if not institute_id:
        return {"ok": False, "message": "Failed to create institute."}

    # 4) Create/update user_profiles role='admin' (idempotent via save_user_profile)
    profile = link_user_profile(auth_user_id, email_norm, admin_name_norm, "admin", institute_id)
    if not profile.get("ok"):
        return {"ok": False, "message": "Failed to create admin profile.", "debug": str(profile.get("error") or "")}

    # 5) Subscription reuse/update (idempotent)
    subscription = _ensure_subscription(institute_id, selected_plan_norm)
    if not subscription.get("ok"):
        return subscription


    return {
        "ok": True,
        "auth_user_id": auth_user_id,
        "institute": institute,
        "institute_id": institute_id,
        "email": email_norm,
        "name": admin_name_norm,
    }


def create_demo_admin_account(form_data: dict[str, Any]) -> dict[str, Any]:
    # Backward compat wrapper for the screen.
    return create_or_continue_admin_onboarding(
        email=form_data.get("admin_email", ""),
        password=str(form_data.get("admin_password") or ""),
        institute_name=form_data.get("institute_name", ""),
        admin_name=form_data.get("admin_name", ""),
        city=form_data.get("city", ""),
        state=form_data.get("state", ""),
        phone=form_data.get("phone", ""),
        selected_plan_code=form_data.get("selected_plan_code", "demo"),
    )



def create_teacher_invite(institute_id: str, name: str, email: str, phone: str | None = None) -> dict[str, Any]:
    db, message = _db_or_message()
    if not db:
        return {"ok": False, "message": message}

    institute_id = _text(institute_id)
    email_norm = _email(email)
    if not institute_id:
        return {"ok": False, "message": "Institute session is missing."}
    if not _text(name) or not EMAIL_RE.match(email_norm):
        return {"ok": False, "message": "Teacher name and valid email are required."}

    existing = _first("teachers", institute_id=institute_id, email=email_norm)
    invite_code = _text((existing or {}).get("invite_code")) or _code("TCH")
    teacher_code = _text((existing or {}).get("teacher_code")) or _code("TCH")
    payload = {
        "institute_id": institute_id,
        "name": _text(name),
        "email": email_norm,
        "phone": _text(phone),
        "teacher_code": teacher_code,
        "invite_code": invite_code,
        "invite_status": "pending",
        "status": "active",
    }

    try:
        if existing:
            db.table("teachers").update(payload).eq("id", existing["id"]).execute()
            row = {**existing, **payload}
        else:
            rows = db.table("teachers").insert(payload).execute().data or []
            row = rows[0] if rows else {**payload}
        return {"ok": True, "teacher": row, "invite_code": invite_code}
    except Exception as exc:
        if _missing_invite_code_column(exc):
            return {"ok": False, "message": TEACHER_INVITE_CODE_SCHEMA_MESSAGE}
        return {"ok": False, "message": "Teacher invite could not be saved.", "debug": str(exc)}


def register_teacher_with_invite(email: str, password: str, invite_code: str) -> dict[str, Any]:
    db, message = _db_or_message()
    if not db:
        return {"ok": False, "message": message}

    email_norm = _email(email)
    code = _text(invite_code).upper()
    if not EMAIL_RE.match(email_norm):
        return {"ok": False, "message": "Enter a valid email."}
    if not code:
        return {"ok": False, "message": "Invalid teacher invite code. Please check with your institute admin."}
    if len(password or "") < 8:
        return {"ok": False, "message": "Password must be at least 8 characters."}

    by_code: list[dict[str, Any]] = []
    try:
        rows = (
            db.table("teachers")
            .select("*")
            .eq("email", email_norm)
            .eq("invite_code", code)
            .eq("status", "active")
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            rows = (
                db.table("teachers")
                .select("*")
                .ilike("email", email_norm)
                .eq("invite_code", code)
                .eq("status", "active")
                .limit(1)
                .execute()
                .data
                or []
            )
        if not rows:
            by_code = (
                db.table("teachers")
                .select("*")
                .eq("invite_code", code)
                .eq("status", "active")
                .limit(1)
                .execute()
                .data
                or []
            )
    except Exception as exc:
        if _missing_invite_code_column(exc):
            return {"ok": False, "message": TEACHER_INVITE_CODE_SCHEMA_MESSAGE}
        return {"ok": False, "message": "Invalid teacher email or invite code.", "debug": str(exc)}

    if not rows:
        if by_code:
            return {"ok": False, "message": "This invite code is not assigned to this email."}
        return {"ok": False, "message": "Invalid teacher email or invite code."}

    teacher = rows[0]
    if teacher.get("user_id"):
        return {"ok": False, "message": "Teacher account already exists. Please sign in.", "account_exists": True}

    invite_state = _text(teacher.get("invite_status") or teacher.get("status")).lower()
    if invite_state in {"accepted", "active"}:
        return {"ok": False, "message": "Teacher account already exists. Please sign in.", "account_exists": True}
    if invite_state in {"expired", "disabled"} or _is_expired(
        teacher.get("invite_expires_at") or teacher.get("expires_at")
    ):
        return {"ok": False, "message": "This invite code has expired. Ask admin to generate a new one."}

    auth = safe_sign_up(email_norm, password)
    if not auth.get("ok"):
        if auth.get("account_exists"):
            return {"ok": False, "message": "Teacher account already exists. Please sign in.", "account_exists": True}
        return auth

    auth_user_id = auth["auth_user_id"]
    updates = {
        "user_id": auth_user_id,
        "invite_status": "accepted",
        "status": "active",
        "updated_at": _utc_now_iso(),
    }
    try:
        db.table("teachers").update(updates).eq("id", teacher["id"]).execute()
    except Exception as exc:
        raw = str(exc)
        if "invite_status" in raw or "updated_at" in raw:
            updates = {"user_id": auth_user_id, "status": "active"}
            try:
                db.table("teachers").update(updates).eq("id", teacher["id"]).execute()
            except Exception as exc2:
                return {"ok": False, "message": "Teacher profile could not be activated.", "debug": str(exc2)}
        else:
            return {"ok": False, "message": "Teacher profile could not be activated.", "debug": raw}

    profile = link_minimal_user_profile(
        auth_user_id,
        email_norm,
        "teacher",
        teacher.get("institute_id"),
    )
    if not profile.get("ok"):
        return {"ok": False, "message": "Failed to create teacher profile.", "debug": str(profile.get("error") or "")}

    teacher = {**teacher, **updates}
    return {"ok": True, "teacher": teacher, "auth_user_id": auth_user_id}


def create_student_invite(
    institute_id: str,
    class_id: str,
    name: str,
    email: str,
    roll_no: str,
) -> dict[str, Any]:
    db, message = _db_or_message()
    if not db:
        return {"ok": False, "message": message}

    institute_id = _text(institute_id)
    email_norm = _email(email)
    roll = _text(roll_no)
    if not institute_id:
        return {"ok": False, "message": "Institute session is missing."}
    if not _text(name) or not EMAIL_RE.match(email_norm) or not roll:
        return {"ok": False, "message": "Student name, valid email, and roll number are required."}

    existing = _first("students", institute_id=institute_id, email=email_norm) or _first(
        "students", institute_id=institute_id, roll_no=roll
    )

    # Generate a new student_code if missing; otherwise reuse the existing one.
    existing_code = _text((existing or {}).get("student_code"))
    student_code = existing_code or _code("STU")

    payload = {
        "institute_id": institute_id,
        "class_id": _text(class_id) or None,
        "name": _text(name),
        "email": email_norm,
        "roll_no": roll,
        "student_code": student_code,
        "invite_status": "invited",
        "status": "invited",
    }

    try:
        if existing:
            db.table("students").update(payload).eq("id", existing["id"]).execute()
            row = {**existing, **payload}
        else:
            rows = db.table("students").insert(payload).execute().data or []
            row = rows[0] if rows else {**payload}
        return {"ok": True, "student": row, "student_code": student_code}
    except Exception as exc:
        return {"ok": False, "message": "Student invite could not be saved.", "debug": str(exc)}


def register_student_with_code(email: str, password: str, student_code_or_roll_no: str) -> dict[str, Any]:
    db, message = _db_or_message()
    if not db:
        return {"ok": False, "message": message}

    email_norm = _email(email)
    lookup = _text(student_code_or_roll_no)
    if not EMAIL_RE.match(email_norm):
        return {"ok": False, "message": "Enter a valid email."}
    if not lookup:
        return {"ok": False, "message": "Invalid student code. Please ask your teacher/admin."}
    if len(password or "") < 8:
        return {"ok": False, "message": "Password must be at least 8 characters."}

    # Required behavior: student cannot self-register; must match an existing
    # public.students row by (email + student_code) OR (email + roll_no).
    try:
        rows = (
            db.table("students")
            .select("*")
            .eq("email", email_norm)
            .eq("student_code", lookup.upper())
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            rows = (
                db.table("students")
                .select("*")
                .ilike("email", email_norm)
                .eq("student_code", lookup.upper())
                .limit(1)
                .execute()
                .data
                or []
            )
        if not rows:
            rows = (
                db.table("students")
                .select("*")
                .eq("email", email_norm)
                .eq("roll_no", lookup)
                .limit(1)
                .execute()
                .data
                or []
            )
        if not rows:
            rows = (
                db.table("students")
                .select("*")
                .ilike("email", email_norm)
                .eq("roll_no", lookup)
                .limit(1)
                .execute()
                .data
                or []
            )
    except Exception as exc:
        return {"ok": False, "message": "Invalid student code. Please ask your teacher/admin.", "debug": str(exc)}

    if not rows:
        if lookup.upper().startswith("STU-"):
            return {"ok": False, "message": "Invalid student code. Please ask your teacher/admin."}
        return {"ok": False, "message": "No student record found. Ask your teacher/admin to add you first."}
    student = rows[0]
    if student.get("user_id"):
        return {"ok": False, "message": "Student account already exists. Please login.", "account_exists": True}

    # Ensure required linkage is present
    # (teacher/admin flow sets students.user_id after invite acceptance).


    auth = safe_sign_up(email_norm, password)
    if not auth.get("ok"):
        if auth.get("account_exists"):
            return {"ok": False, "message": "Student account already exists. Please login.", "account_exists": True}
        return auth

    auth_user_id = auth["auth_user_id"]
    updates = {"user_id": auth_user_id, "invite_status": "accepted", "status": "active"}
    try:
        db.table("students").update(updates).eq("id", student["id"]).execute()
    except Exception as exc:
        raw = str(exc)
        if "invite_status" in raw:
            updates = {"user_id": auth_user_id, "status": "active"}
            try:
                db.table("students").update(updates).eq("id", student["id"]).execute()
            except Exception as exc2:
                return {"ok": False, "message": "Student profile could not be activated.", "debug": str(exc2)}
        else:
            return {"ok": False, "message": "Student profile could not be activated.", "debug": raw}

    profile = link_user_profile(
        auth_user_id,
        email_norm,
        student.get("name") or email_norm.split("@")[0],
        "student",
        student.get("institute_id"),
    )
    if not profile.get("ok"):
        return {"ok": False, "message": "Failed to create student profile.", "debug": str(profile.get("error") or "")}

    student = {**student, **updates}
    return {"ok": True, "student": student, "auth_user_id": auth_user_id}
