"""Legacy floating chatbot (disabled).

This module is intentionally kept as a no-op so the old raw HTML/CSS for the
SnapBot widget cannot be injected into the app.
"""

from __future__ import annotations

import streamlit as st


def render_floating_chatbot() -> None:
    """No-op legacy renderer."""
    return

