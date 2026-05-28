"""Notification feature removed (fast fix).

This module previously rendered raw HTML for a bell notification center.
To eliminate the broken UI (raw HTML showing in a black code box), we
now provide no-op stubs.
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st


def get_notifications(supabase: Optional[Any] = None, limit: int = 8):
    # Keep backward-compatible signature; return empty list so callers (if any)
    # won't render notifications.
    return []


def render_notification_center(supabase: Optional[Any] = None):
    # No-op: do not render any HTML or UI.
    return None

