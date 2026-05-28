"""Access-code helpers for SnapClass HQ and institute onboarding."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
import string
from typing import Dict


_ALPHABET = string.ascii_uppercase + string.digits


def generate_access_code(prefix: str = "SC", length: int = 6) -> str:
    """Return an invite-style access code such as SC-1A2B3C."""
    token = "".join(secrets.choice(_ALPHABET) for _ in range(length))
    return f"{prefix}-{token}"


def build_code_record(
    *,
    code: str,
    institute_id: str,
    admin_email: str = "",
    expires_days: int = 30,
    status: str = "unused",
) -> Dict[str, str]:
    """Create a code payload for Supabase or session-state storage."""
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(days=expires_days)
    return {
        "code": code,
        "institute_id": institute_id,
        "admin_email": admin_email,
        "status": status,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
    }


def is_expired(expires_at: str | None) -> bool:
    """Return True when the code has expired."""
    if not expires_at:
        return False
    try:
        stamp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        return stamp <= datetime.now(timezone.utc)
    except Exception:
        return False
