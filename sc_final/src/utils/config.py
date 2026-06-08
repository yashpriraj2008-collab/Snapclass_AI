from __future__ import annotations

import os
from typing import Any

import streamlit as st


def _env_get_raw(key: str) -> str:
    v = os.environ.get(key)
    if v is None:
        return ""
    return str(v).strip()


def _secrets_get_raw(key: str) -> str:
    try:
        # Streamlit secrets behaves like a mapping.
        v: Any = st.secrets.get(key, "")  # type: ignore[attr-defined]
        if v is None:
            return ""
        return str(v).strip()
    except Exception:
        return ""


def get_config(key: str, default: str = "") -> str:
    """Load configuration from Render env vars first, then st.secrets.

    Render secrets are mounted into /etc/secrets/secrets.toml and are not
    automatically exposed as `.streamlit/secrets.toml`.

    Local dev still uses `.streamlit/secrets.toml` through st.secrets.
    """

    # 1) Render / platform environment variables
    env_val = _env_get_raw(key)
    if env_val:
        return env_val

    # 2) Local dev (and any environments where st.secrets is populated)
    secrets_val = _secrets_get_raw(key)
    if secrets_val:
        return secrets_val

    # 3) Missing
    return default


