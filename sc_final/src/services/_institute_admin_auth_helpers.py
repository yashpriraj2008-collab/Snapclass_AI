"""Internal helper module for institute-admin authentication.

This file exists to keep `auth_service.py` readable.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.database.client import get_supabase


def ensure_institute_admin_profile(
    *,
    user_id: str,
    email: str,
    name: str,
    institute_id: str,
) -> Dict[str, Any]:
    """Upsert into user_profiles for institute admin.

    RLS helper functions expect:
      - private.current_user_role() from user_profiles.role
      - private.current_institute_id() from user_profiles.institute_id
    """
    if not user_id or not email or not institute_id:
        return {"ok": False, "message": "Missing institute admin mapping inputs."}

    db = get_supabase()
    if not db:
        return {"ok": False, "message": "Supabase not connected."}

    email_norm = (email or "").strip().lower()

    payload = {
        "id": user_id,
        "user_id": user_id,
        "email": email_norm,
        "full_name": (name or "").strip(),
        "role": "institute_admin",
        "institute_id": institute_id,
        "status": "active",
    }

    try:
        existing = db.table("user_profiles").select("id").eq("id", user_id).limit(1).execute()
        if existing.data:
            db.table("user_profiles").update(payload).eq("id", user_id).execute()
        else:
            # Fall back to email match if id not found.
            by_email = db.table("user_profiles").select("id").eq("email", email_norm).limit(1).execute()
            if by_email.data:
                db.table("user_profiles").update(payload).eq("email", email_norm).execute()
            else:
                db.table("user_profiles").insert(payload).execute()
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "message": f"Failed to upsert institute admin profile: {exc}"}

