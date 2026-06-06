"""Institute-level data helpers with Supabase + session-state fallback."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

import streamlit as st

from src.database.client import get_supabase
from src.services.code_service import build_code_record, generate_access_code, is_expired


INSTITUTE_KEYS = (
    "institutes",
    "codes",
    "teachers",
    "classes",
    "subjects",
    "students",
    "attendance",
)


def init_institute_state() -> None:
    """Initialize the demo fallback lists used by the new institute flow."""
    defaults: Dict[str, list] = {
        "institutes": [],
        "codes": [],
        "teachers": [],
        "classes": [],
        "subjects": [],
        "students": [],
        "attendance": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _db():
    return get_supabase()


def _new_id() -> str:
    return str(uuid.uuid4())


def _ensure_institute_columns(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(payload)
    data.setdefault("id", _new_id())
    data.setdefault("name", "")
    data.setdefault("city", "")
    data.setdefault("state", "")
    data.setdefault("address", "")
    data.setdefault("institute_type", "School")
    data.setdefault("admin_name", "")
    data.setdefault("admin_email", "")
    data.setdefault("admin_phone", "")
    data.setdefault("plan", "Demo")
    data.setdefault("status", "active")
    data.setdefault("attendance_threshold", 75)
    data.setdefault("academic_year", "")
    return data


def _ensure_code_columns(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(payload)
    data.setdefault("id", _new_id())
    data.setdefault("code", generate_access_code())
    data.setdefault("institute_id", "")
    data.setdefault("admin_email", "")
    data.setdefault("status", "unused")
    data.setdefault("created_at", "")
    data.setdefault("expires_at", "")
    return data


def _norm_text(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_code_status(code_row: dict[str, Any] | None) -> str:
    """Return the user-visible lifecycle status for a school code."""
    row = code_row or {}
    status = _norm_text(row.get("status") or "unused")
    if row.get("used_at") or row.get("used_by"):
        return "used"
    if status == "expired" or is_expired(row.get("expires_at")):
        return "expired"
    if status == "used":
        return "used"
    return "unused"


def _hydrate_code_usage_from_profiles(codes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Infer used invite codes when older rows were not marked during onboarding."""
    if not codes:
        return codes

    db = _db()
    if db is None:
        return codes

    try:
        profiles = db.table("user_profiles").select("*").execute().data or []
    except Exception:
        profiles = []

    try:
        institutes = db.table("institutes").select("*").execute().data or []
    except Exception:
        institutes = []

    admin_profiles: list[dict[str, Any]] = []
    for profile in profiles:
        role = _norm_text(profile.get("role"))
        if role in {"admin", "institute_admin", "super_admin"} and profile.get("institute_id"):
            admin_profiles.append(profile)

    profiles_by_institute: dict[str, list[dict[str, Any]]] = {}
    for profile in admin_profiles:
        profiles_by_institute.setdefault(str(profile.get("institute_id") or ""), []).append(profile)

    institutes_by_id = {str(item.get("id") or ""): item for item in institutes}
    hydrated: list[dict[str, Any]] = []
    for code in codes:
        row = dict(code)
        if normalize_code_status(row) != "unused":
            hydrated.append(row)
            continue

        institute_id = str(row.get("institute_id") or "")
        admin_email = _norm_text(row.get("admin_email"))
        matching_profile = None
        for profile in profiles_by_institute.get(institute_id, []):
            profile_email = _norm_text(profile.get("email"))
            if admin_email and profile_email != admin_email:
                continue
            matching_profile = profile
            break

        institute = institutes_by_id.get(institute_id, {})
        onboarding_done = bool(institute.get("onboarding_completed"))
        if matching_profile or onboarding_done:
            row["status"] = "used"
            row["used_by"] = (
                row.get("used_by")
                or (matching_profile or {}).get("email")
                or row.get("admin_email")
                or institute.get("admin_email")
                or ""
            )
            row["used_at"] = (
                row.get("used_at")
                or (matching_profile or {}).get("created_at")
                or institute.get("updated_at")
                or institute.get("created_at")
                or ""
            )
        hydrated.append(row)
    return hydrated


def list_institutes() -> List[Dict[str, Any]]:
    """Return all institutes from Supabase or session_state."""
    db = _db()
    if db is None:
        init_institute_state()
        return list(st.session_state.institutes)

    try:
        data = db.table("institutes").select("*").order("created_at", desc=True).execute().data or []
        return data
    except Exception:
        init_institute_state()
        return list(st.session_state.institutes)


def list_codes() -> List[Dict[str, Any]]:
    """Return all access codes from Supabase or session_state."""
    db = _db()
    if db is None:
        init_institute_state()
        return list(st.session_state.codes)

    try:
        data = db.table("school_codes").select("*").order("created_at", desc=True).execute().data or []
        return _hydrate_code_usage_from_profiles(data)
    except Exception:
        init_institute_state()
        return list(st.session_state.codes)


def create_institute(
    *,
    name: str,
    city: str,
    state: str = "",
    address: str = "",
    institute_type: str = "School",
    admin_name: str = "",
    admin_email: str = "",
    admin_phone: str = "",
    plan: str = "Demo",
    status: str = "active",
    attendance_threshold: int = 75,
    academic_year: str = "",
) -> Dict[str, Any]:
    """Create a new institute record."""
    payload = _ensure_institute_columns(
        {
            "name": name.strip(),
            "city": city.strip(),
            "state": state.strip(),
            "address": address.strip(),
            "institute_type": institute_type,
            "admin_name": admin_name.strip(),
            "admin_email": admin_email.strip().lower(),
            "admin_phone": admin_phone.strip(),
            "plan": plan,
            "status": status,
            "attendance_threshold": attendance_threshold,
            "academic_year": academic_year.strip(),
        }
    )


    db = _db()
    if db is None:
        init_institute_state()
        for index, existing in enumerate(st.session_state.institutes):
            same_admin = payload.get("admin_email") and _norm_text(existing.get("admin_email")) == _norm_text(payload.get("admin_email"))
            same_identity = (
                bool(payload.get("admin_email"))
                and
                _norm_text(existing.get("name")) == _norm_text(payload.get("name"))
                and _norm_text(existing.get("city")) == _norm_text(payload.get("city"))
                and _norm_text(existing.get("admin_email")) == _norm_text(payload.get("admin_email"))
            )
            if same_admin or same_identity:
                merged = {**existing, **{k: v for k, v in payload.items() if v not in (None, "")}}
                st.session_state.institutes[index] = merged
                return {
                    "ok": True,
                    "demo": True,
                    "data": merged,
                    "reused": True,
                    "message": f"Institute '{name}' already exists locally. Reused existing row.",
                }
        st.session_state.institutes.append(payload)
        return {"ok": True, "demo": True, "data": payload, "message": f"Institute '{name}' created locally."}

    try:
        existing_rows: list[dict[str, Any]] = []
        if payload.get("admin_email"):
            existing_rows = (
                db.table("institutes")
                .select("*")
                .eq("admin_email", payload.get("admin_email"))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data
                or []
            )
        if not existing_rows and payload.get("name") and payload.get("city") and payload.get("admin_email"):
            existing_rows = (
                db.table("institutes")
                .select("*")
                .eq("name", payload.get("name"))
                .eq("city", payload.get("city"))
                .eq("admin_email", payload.get("admin_email"))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data
                or []
            )
        if existing_rows:
            existing = existing_rows[0]
            clean_updates = {key: value for key, value in payload.items() if value not in (None, "") and key != "id"}
            rows = db.table("institutes").update(clean_updates).eq("id", existing["id"]).execute().data or []
            record = rows[0] if rows else {**existing, **clean_updates}
            return {
                "ok": True,
                "demo": False,
                "data": record,
                "reused": True,
                "message": f"Institute '{name}' already exists. Reused existing row.",
            }

        db.table("institutes").insert(payload).execute()
        response = (
            db.table("institutes")
            .select("*")
            .eq("id", payload.get("id"))
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            response = (
                db.table("institutes")
                .select("*")
                .eq("name", payload.get("name"))
                .eq("city", payload.get("city"))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            rows = response.data or []
        record = rows[0] if rows else payload

        # Ensure subsequent steps have the correct id.
        if isinstance(record, dict) and record.get("id"):
            return {"ok": True, "demo": False, "data": record, "message": f"Institute '{name}' created."}

        return {"ok": True, "demo": False, "data": payload, "message": f"Institute '{name}' created."}

    except Exception as exc:
        return {"ok": False, "demo": False, "data": payload, "error": exc, "message": f"Supabase error: {exc}"}


def update_institute(institute_id: str, updates: dict) -> dict:
    """Update institute in Supabase. Always log what happens."""
    import streamlit as st
    from src.database.client import get_supabase

    db = get_supabase()

    # Check if we have a valid ID
    if not institute_id:
        if st.session_state.get("current_institute"):
            st.session_state.current_institute.update(updates)
        if "name" in updates:
            st.session_state.active_institute_name = updates["name"]
        return {
            "ok": True,
            "demo": True,
            "message": "✅ Saved locally (no institute_id in session — demo mode)."
        }

    # Check Supabase connection
    if db is None:
        return {
            "ok": True,
            "demo": True,
            "message": "✅ Saved locally (Supabase not connected)."
        }

    # Try Supabase update
    try:
        result = db.table("institutes").update(updates).eq("id", institute_id).execute()
        
        # Check if any rows were actually updated
        if result.data:
            if st.session_state.get("current_institute"):
                st.session_state.current_institute.update(updates)
            if "name" in updates:
                st.session_state.active_institute_name = updates["name"]
            return {
                "ok": True,
                "demo": False,
                "message": f"✅ Institute updated in Supabase. ({len(result.data)} row updated)"
            }
        else:
            # No rows matched — wrong ID or RLS blocking
            return {
                "ok": False,
                "demo": False,
                "message": f"⚠️ Supabase returned 0 rows updated. institute_id used: {institute_id}. Check RLS policy."
            }
    except Exception as e:
        return {
            "ok": False,
            "demo": False,
            "error": e,
            "message": f"❌ Supabase error: {str(e)}"
        }


def deactivate_institute(institute_id: str) -> Dict[str, Any]:
    return update_institute(institute_id, {"status": "disabled"})


def activate_institute(institute_id: str) -> Dict[str, Any]:
    return update_institute(institute_id, {"status": "active"})


def create_access_code(
    institute_id: str,
    admin_email: str = "",
    expires_days: int = 30,
) -> Dict[str, Any]:
    """Generate and persist an access code for the given institute."""
    code = generate_access_code()
    payload = build_code_record(
        code=code,
        institute_id=institute_id,
        admin_email=admin_email,
        expires_days=expires_days,
    )
    payload = _ensure_code_columns(payload)


    db = _db()
    if db is None:
        init_institute_state()
        st.session_state.codes.append(payload)
        return {"ok": True, "demo": True, "data": payload, "message": f"Access code generated: {code}"}

    try:
        rows = db.table("school_codes").insert(payload).execute().data or []
        record = rows[0] if rows else payload
        return {"ok": True, "demo": False, "data": record, "message": f"Access code generated: {code}"}
    except Exception as exc:
        return {"ok": False, "demo": False, "data": payload, "error": exc, "message": f"Supabase error: {exc}"}


def get_code_by_value(code_value: str) -> Optional[Dict[str, Any]]:
    """Return one access code record by exact code value."""
    db = _db()
    if db is None:
        init_institute_state()
        return next((code for code in st.session_state.codes if code.get("code") == code_value), None)

    try:
        normalized = code_value.strip().upper().replace(" ", "")
        data = (
            db.table("school_codes")
            .select("*")
            .eq("code", normalized)
            .limit(1)
            .execute()
            .data
            or []
        )

        return data[0] if data else None
    except Exception:
        init_institute_state()
        return next((code for code in st.session_state.codes if code.get("code") == code_value), None)


def validate_access_code(code_value: str) -> Dict[str, Any]:
    """Validate an institute access code and return its institute payload."""
    code_record = get_code_by_value(code_value)
    if not code_record:
        return {"ok": False, "message": "Invalid institute access code."}

    if normalize_code_status(code_record) == "used":
        return {"ok": False, "message": "This access code has already been used."}

    if is_expired(code_record.get("expires_at")):
        return {"ok": False, "message": "This access code has expired."}

    institute_id = code_record.get("institute_id", "")
    institute = get_institute_by_id(institute_id)
    if not institute:
        return {"ok": False, "message": "Institute not found for this access code."}

    # normalize onboarding_completed presence for the routing decision
    if "onboarding_completed" not in institute:
        institute["onboarding_completed"] = False

    return {"ok": True, "code": code_record, "institute": institute, "message": "Access code validated."}



def _unsupported_columns_from_error(error: Exception, payload: dict[str, Any]) -> list[str]:
    raw = str(error).lower()
    return [column for column in payload if column.lower() in raw and "column" in raw]


def _update_school_code_usage(db, normalized_code: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return (
            db.table("school_codes")
            .update(payload)
            .eq("code", normalized_code)
            .execute()
            .data
            or []
        )
    except Exception as exc:
        unsupported = _unsupported_columns_from_error(exc, payload)
        if not unsupported:
            raise
        retry = dict(payload)
        for column in unsupported:
            retry.pop(column, None)
        return (
            db.table("school_codes")
            .update(retry)
            .eq("code", normalized_code)
            .execute()
            .data
            or []
        )


def _get_school_code_by_normalized_value(db, normalized_code: str) -> dict[str, Any] | None:
    try:
        rows = (
            db.table("school_codes")
            .select("*")
            .eq("code", normalized_code)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def mark_code_used(
    code_value: str,
    *,
    admin_email: str = "",
    institute_id: str = "",
) -> Dict[str, Any]:
    """Mark a code as used after onboarding starts."""
    normalized = str(code_value or "").strip().upper().replace(" ", "")
    if not normalized:
        return {"ok": False, "demo": False, "message": "Access code missing."}

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "status": "used",
        "used_by": str(admin_email or "").strip().lower(),
        "used_at": now,
        "updated_at": now,
    }
    if institute_id:
        payload["institute_id"] = institute_id

    db = _db()
    if db is None:
        init_institute_state()
        for code in st.session_state.codes:
            if str(code.get("code") or "").strip().upper().replace(" ", "") == normalized:
                code.update({k: v for k, v in payload.items() if v})
                return {"ok": True, "demo": True, "message": "Code marked as used locally."}
        return {"ok": False, "demo": True, "message": "Code not found."}

    try:
        rows = _update_school_code_usage(db, normalized, payload)
        if not rows:
            verified = _get_school_code_by_normalized_value(db, normalized)
            if verified and normalize_code_status(verified) == "used":
                st.cache_data.clear()
                return {"ok": True, "demo": False, "data": verified, "message": "Code marked as used."}
            return {
                "ok": False,
                "demo": False,
                "message": "Code was not marked as used. Check school_codes table or RLS.",
            }
        st.cache_data.clear()
        return {"ok": True, "demo": False, "data": rows[0], "message": "Code marked as used."}

    except Exception as exc:
        return {"ok": False, "demo": False, "debug": str(exc), "message": "Code could not be marked as used."}


def get_institute_by_id(institute_id: str) -> Optional[Dict[str, Any]]:
    """Return one institute by ID."""
    db = _db()
    if db is None:
        init_institute_state()
        return next((inst for inst in st.session_state.institutes if inst.get("id") == institute_id), None)

    try:
        data = db.table("institutes").select("*").eq("id", institute_id).limit(1).execute().data or []
        if not data:
            return None
        inst = data[0]
        # onboarding_completed may be missing if schema not yet migrated in this environment.
        inst.setdefault("onboarding_completed", False)
        return inst
    except Exception:
        init_institute_state()
        return next((inst for inst in st.session_state.institutes if inst.get("id") == institute_id), None)



def set_active_institute(institute: Dict[str, Any], code_value: str = "") -> None:
    """Store the current institute in session_state for institute-admin pages."""
    institute_id = institute.get("id", "")
    st.session_state.active_institute_id = institute_id
    st.session_state.institute_id = institute_id
    st.session_state.current_institute_id = institute_id
    st.session_state.active_institute_name = institute.get("name", "")
    st.session_state.current_institute = institute
    st.session_state.active_institute_code = code_value

    # onboarding_completed lives on the institute row (DB-backed in Phase 2)
    st.session_state.onboarding_completed = bool(institute.get("onboarding_completed", False))



def count_institutes() -> int:
    return len(list_institutes())


def count_codes() -> int:
    return len(list_codes())


def count_active_institutes() -> int:
    return sum(1 for inst in list_institutes() if inst.get("status", "active") == "active")


def create_institute_with_code(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Required shape: insert institute -> get institute_id -> generate code -> insert into school_codes.

    If Supabase fails at any step, store institute/code in session_state for this session and return ok=True.
    """
    # Normalize expected keys from the Founder form.
    name = form_data.get("name", "").strip()
    city = form_data.get("city", "").strip()
    state = form_data.get("state", "").strip()
    address = form_data.get("address", "").strip()
    institute_type = form_data.get("institute_type", "School")
    admin_name = form_data.get("admin_name", "").strip()
    admin_email = form_data.get("admin_email", "").strip()
    admin_phone = form_data.get("admin_phone", "").strip()
    plan = form_data.get("plan", "Demo")
    attendance_threshold = int(form_data.get("attendance_threshold", 75))
    academic_year = form_data.get("academic_year", "").strip()

    # 1) Insert institute.
    inst_result = create_institute(
        name=name,
        city=city,
        state=state,
        address=address,
        institute_type=institute_type,
        admin_name=admin_name,
        admin_email=admin_email,
        admin_phone=admin_phone,
        plan=plan,
        status="active",
        attendance_threshold=attendance_threshold,
        academic_year=academic_year,
    )
    if not inst_result.get("ok"):
        return inst_result

    institute = inst_result.get("data") or {}
    institute_id = institute.get("id", "")

    if not institute_id:
        local = list_institutes()
        for it in reversed(local):
            if it.get("name") == name and it.get("city") == city:
                institute_id = it.get("id", "")
                institute = it
                break

    if not institute_id:
        return {
            "ok": False,
            "demo": True,
            "message": "Could not determine institute_id after creation.",
            "data": {"institute": institute},
        }

    # 2) Generate code.
    code_result = create_access_code(
        institute_id=institute_id,
        admin_email=admin_email,
        expires_days=int(form_data.get("expires_days", 30)),
    )

    if not code_result.get("ok"):
        return {
            "ok": False,
            "demo": False,
            "error": code_result.get("error"),
            "message": code_result.get("message", "Failed to generate access code."),
            "data": {"institute": institute, "code": code_result.get("data")},
        }

    code_data = code_result.get("data") or {}

    # 3) Refresh logic: re-fetch and store into session_state, then return.
    try:
        st.session_state.institutes = list_institutes()
        st.session_state.codes = list_codes()

    except Exception:
        pass


    access_code = code_data.get("code", "")
    if inst_result.get("demo") or code_result.get("demo"):
        return {
            "ok": True,
            "demo": True,
            "message": "Supabase save failed. Saved locally for this session.",
            "data": {"institute": institute, "code": code_data, "access_code": access_code},
        }

    return {
        "ok": True,
        "demo": False,
        "message": "Institute created successfully. Access Code: " + str(access_code),
        "data": {"institute": institute, "code": code_data, "access_code": access_code},
    }
