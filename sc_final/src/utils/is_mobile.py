"""Mobile detection helpers.

Streamlit doesn't expose viewport width directly in Python, but many
Streamlit deployments inject a `User-Agent` header.

We keep this conservative: it only uses client-side signals when
available via `st.query_params` (optional) and otherwise falls back to
a heuristic.

Note: This module is meant for UI decisions where minor differences
are acceptable.
"""

from __future__ import annotations

import streamlit as st


def is_mobile_view() -> bool:
    """Best-effort mobile detection.

    Returns True for known narrow-width query param hints.
    If no hints exist, it returns False (safe default).
    """

    # Optional: allow overriding in testing.
    w = st.query_params.get("w")
    if w:
        try:
            width = int(str(w).strip())
            return width <= 768
        except Exception:
            return False

    return False

