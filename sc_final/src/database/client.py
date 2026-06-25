"""Supabase client initialization.

Important:
- Never silently swallow the real exception when determining whether Supabase
  is configured/working.
- Return None when not configured, but preserve the actual backend exception
  for debugging.

UI is intentionally NOT modified in this file.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
import tomllib
from typing import Any

import streamlit as st
from supabase import Client, create_client

import os


_client: Client | None = None
_checked: bool = False
_last_error: str | None = None
_cached_secrets_mtime: float | None = None

SUPABASE_MISSING_MESSAGE = (
    "Supabase is not configured. Add a Streamlit secrets.toml at one of: \n"
    "- sc_final/.streamlit/secrets.toml\n"
    "- .streamlit/secrets.toml (repo root)"
)
SUPABASE_MISSING_NOTICE_KEY = "_supabase_missing_notice_shown"


def _secrets_path() -> Path:
    """Return the most likely secrets.toml location for Streamlit.

    Supports both:
    - repo/.streamlit/secrets.toml (repo root)
    - sc_final/.streamlit/secrets.toml (app folder)
    """
    app_root = Path(__file__).resolve().parents[1]  # sc_final/src/ -> sc_final/
    repo_root = app_root.parent


    candidates = [
        repo_root / ".streamlit" / "secrets.toml",
        app_root / ".streamlit" / "secrets.toml",
    ]

    for p in candidates:
        try:
            if p.exists():
                return p
        except OSError:
            continue

    # Default to the app-local path (least surprising for local dev)
    return candidates[-1]


def _streamlit_builtin_secrets_guard() -> None:

    """Prevent Streamlit's built-in “No secrets found” message.

    Streamlit emits that warning when `st.secrets` is accessed and it can't
    find a secrets.toml in its search paths.

    We already read the correct secrets file ourselves (see _secrets_path).
    So we set ST_SECRETS_PATH to our resolved file to stop the noisy warning.
    """
    try:
        path = _secrets_path()
        # Streamlit expects a directory or file path.
        # Setting it to the resolved file is safe for local dev.
        os.environ.setdefault("ST_SECRETS_PATH", str(path))
    except Exception:
        pass




def _secrets_mtime() -> float | None:
    path = _secrets_path()
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _get_nested(mapping: Any, *keys: str) -> Any:
    current = mapping
    for key in keys:
        try:
            current = current[key]
        except Exception:
            return None
    return current


def _read_toml_secrets(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except Exception:
        return {}


def _to_plain_dict(value: Any) -> dict[str, Any]:
    """Convert Streamlit secrets/AttrDict values to a normal dict."""
    if not value:
        return {}
    try:
        items = value.items()
    except Exception:
        return {}

    plain: dict[str, Any] = {}
    for key, item in items:
        if hasattr(item, "items"):
            plain[key] = _to_plain_dict(item)
        else:
            plain[key] = item
    return plain


def read_app_secrets() -> dict[str, Any]:
    """Read Streamlit secrets without exposing secret values.

    Local development reads `.streamlit/secrets.toml` directly. Deployed
    Streamlit environments may provide the same data through `st.secrets`.
    """
    secrets: dict[str, Any] = {}

    path = _secrets_path()
    if path.exists():
        secrets.update(_read_toml_secrets(path))

    try:
        streamlit_secrets = _to_plain_dict(st.secrets)
    except Exception:
        streamlit_secrets = {}
    if streamlit_secrets:
        secrets.update(streamlit_secrets)

    return secrets


def supabase_secrets_ready() -> bool:
    """Return True when Supabase secrets are present and use an anon key."""
    url, key = _read_secrets()
    return bool(url and key and not _looks_like_service_role_key(key))


def preflight_supabase_secrets(*, show_notice: bool = True) -> tuple[bool, str]:
    """Validate local Supabase secrets once and optionally show a single UI error."""
    client = get_supabase_client()
    if client is not None:
        if show_notice and hasattr(st, "session_state"):
            try:
                st.session_state.pop(SUPABASE_MISSING_NOTICE_KEY, None)
            except Exception:
                pass
        return True, ""

    message = _last_error or SUPABASE_MISSING_MESSAGE
    if show_notice:
        shown = False
        try:
            shown = bool(st.session_state.get(SUPABASE_MISSING_NOTICE_KEY, False))
        except Exception:
            shown = True

        if not shown:
            try:
                st.session_state[SUPABASE_MISSING_NOTICE_KEY] = True
            except Exception:
                pass
            st.error(message)

    return False, message


def _looks_like_service_role_key(key: str) -> bool:
    if not key:
        return False
    lowered = key.lower()
    if "service_role" in lowered or "service-role" in lowered:
        return True

    parts = key.split(".")
    if len(parts) < 2:
        return False
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload.encode("ascii"))
        claims = json.loads(decoded.decode("utf-8"))
    except Exception:
        return False
    return str(claims.get("role", "")).lower() == "service_role"


def _first_value(mapping: Any, candidates: tuple[str, ...]) -> str:
    for name in candidates:
        try:
            value = mapping.get(name, "")
        except Exception:
            value = ""
        if value:
            return str(value).strip()
    return ""


def _read_secrets() -> tuple[str, str]:
    """Read supported Supabase settings formats."""
    source = read_app_secrets()
    if not source:
        return "", ""

    url = _first_value(source, ("SUPABASE_URL", "supabase_url"))
    key = _first_value(source, ("SUPABASE_ANON_KEY", "SUPABASE_KEY", "supabase_anon_key", "supabase_key", "anon_key"))

    nested = _get_nested(source, "supabase")
    if nested:
        url = url or _first_value(nested, ("url", "URL", "SUPABASE_URL"))
        key = key or _first_value(nested, ("anon_key", "ANON_KEY", "SUPABASE_ANON_KEY", "key"))

    return url, key


@st.cache_resource(show_spinner=False)
def _create_supabase_client_cached(current_mtime: float | None) -> tuple[Client | None, str | None]:
    try:
        url, key = _read_secrets()

        if not url or not key:
            return None, SUPABASE_MISSING_MESSAGE

        if "your-project" in url or url == "https://your-project.supabase.co":
            return None, "Invalid SUPABASE_URL (still contains your-project placeholder)"

        if _looks_like_service_role_key(key):
            return None, "Service-role Supabase keys are not allowed. Use the anon public key."

        return create_client(url, key), None

    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def get_supabase_client() -> Client | None:

    _streamlit_builtin_secrets_guard()

    """Return a Streamlit resource-cached Supabase client or None."""

    global _client, _checked, _last_error, _cached_secrets_mtime

    current_mtime = _secrets_mtime()
    _checked = True
    _cached_secrets_mtime = current_mtime
    _client, _last_error = _create_supabase_client_cached(current_mtime)
    return _client


def debug_supabase_status() -> dict:
    """Return required debug fields."""
    path = _secrets_path()
    if not path.exists():
        secrets_loaded = "no"
    else:
        url, key = _read_secrets()
        secrets_loaded = "yes" if (url and key) else "no"

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
        return {"ok": False, "message": _last_error or SUPABASE_MISSING_MESSAGE}

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


def get_supabase_error() -> str:
    """Return the latest Supabase initialization error."""
    return _last_error or ""


def reset_client():
    """Force re-init (useful after secrets change in dev)."""
    global _client, _checked, _last_error, _cached_secrets_mtime
    _create_supabase_client_cached.clear()
    _client = None
    _checked = False
    _last_error = None
    _cached_secrets_mtime = None
