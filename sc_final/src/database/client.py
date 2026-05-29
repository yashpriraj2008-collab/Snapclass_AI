"""Supabase client initialization.

Important:
- Never silently swallow the real exception when determining whether Supabase
  is configured/working.
- Return None when not configured, but preserve the actual backend exception
  for debugging.

UI is intentionally NOT modified in this file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
from supabase import Client, create_client

_client: Client | None = None
_checked: bool = False
_last_error: str | None = None


def _secrets_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".streamlit" / "secrets.toml"


def _read_secrets() -> tuple[str, str]:
    """Read only the non-secret status required to create a client.

    Avoid touching st.secrets when no secrets file exists so Streamlit does not
    show the "No secrets found" warning banner in demo mode.
    """
    path = _secrets_path()
    if not path.exists():
        return "", ""

    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_ANON_KEY") or ""
        return url, key
    except Exception:
        return "", ""


def get_supabase_client() -> Client | None:
    """Return a Supabase client or None."""
    global _client, _checked, _last_error

    if _checked:
        return _client

    _checked = True
    _last_error = None

    try:
        url, key = _read_secrets()

        if not url or not key:
            _client = None
            _last_error = "Missing SUPABASE_URL or SUPABASE_KEY/SUPABASE_ANON_KEY"
            return None

        if "your-project" in url or url == "https://your-project.supabase.co":
            _client = None
            _last_error = "Invalid SUPABASE_URL (still contains your-project placeholder)"
            return None

        _client = create_client(url, key)
        return _client

    except Exception as e:
        _client = None
        _last_error = f"{type(e).__name__}: {e}"
        return None


def debug_supabase_status() -> dict:
    """Return required debug fields."""
    path = _secrets_path()
    if not path.exists():
        secrets_loaded = "no"
    else:
        try:
            url_present = bool(st.secrets.get("SUPABASE_URL", ""))
            key_present = bool(st.secrets.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_ANON_KEY"))
            secrets_loaded = "yes" if (url_present and key_present) else "no"
        except Exception:
            secrets_loaded = "no"

    client = None
    try:
        client = get_supabase_client()
    except Exception:
        client = None

    supabase_client_created = "yes" if client is not None else "no"
    err = _last_error or ""

    return {
        "secrets_loaded": secrets_loaded,
        "supabase_client_created": supabase_client_created,
        "actual_backend_exception": err,
    }


def test_connection() -> dict:
    """Test Supabase connection (read query)."""
    db = get_supabase_client()
    if db is None:
        return {"ok": False, "message": _last_error or "Supabase not configured in secrets.toml"}

    try:
        db.table("institutes").select("id").limit(1).execute()
        return {"ok": True, "message": "Supabase connected successfully"}
    except Exception as e:
        err = str(e)
        if "PGRST205" in err or "schema cache" in err or "Could not find the table" in err:
            return {"ok": False, "message": "Table not found. Run schema.sql in Supabase SQL Editor."}
        if "invalid" in err.lower() or "401" in err:
            return {"ok": False, "message": "Invalid Supabase key. Check SUPABASE_ANON_KEY/SUPABASE_KEY."}
        return {"ok": False, "message": f"Supabase error: {err}"}


def is_db_connected() -> bool:
    """Return True if a simple query succeeds."""
    db = get_supabase_client()
    if db is None:
        return False
    try:
        db.table("students").select("id").limit(1).execute()
        return True
    except Exception:
        return False


def get_supabase():
    """Backward-compatible alias used across the codebase."""
    return get_supabase_client()


def reset_client():
    """Force re-init (useful after secrets change in dev)."""
    global _client, _checked, _last_error
    _client = None
    _checked = False
    _last_error = None
