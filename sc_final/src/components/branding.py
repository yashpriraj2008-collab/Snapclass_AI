"""SnapClass AI logo rendering with safe file fallbacks."""
from __future__ import annotations

import base64
import html
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]


def logo_path(compact: bool = False) -> Path | None:
    filenames = ("logo-icon.png",) if compact else ("logo.png",)
    for directory in (ROOT / "static", ROOT / "assets"):
        for filename in filenames:
            candidate = directory / filename
            if candidate.is_file():
                return candidate
    return None


def render_logo(compact: bool = False) -> None:
    """Render the configured logo, or branded text when no image exists."""
    path = logo_path(compact=compact)
    if path:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        width = 42 if compact else 220
        compact_class = " snapclass-logo-compact" if compact else ""
        st.markdown(
            f"""
            <div class="snapclass-logo{compact_class}">
              <img src="data:image/png;base64,{encoded}" alt="SnapClass AI"
                style="display:block;max-width:100%;width:{width}px;height:auto;object-fit:contain;">
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    label = "S" if compact else "SnapClass AI"
    compact_class = " snapclass-logo-compact" if compact else ""
    st.markdown(
        f"""
        <div class="snapclass-logo snapclass-logo-fallback{compact_class}"
          aria-label="SnapClass AI">{html.escape(label)}</div>
        """,
        unsafe_allow_html=True,
    )


def render_brand_lockup() -> None:
    """Render a compact icon-and-wordmark lockup for public navigation."""
    path = logo_path(compact=True)
    icon_html = ""
    if path:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        icon_html = (
            f'<img src="data:image/png;base64,{encoded}" alt="" '
            'class="snapclass-brand-icon">'
        )
    else:
        icon_html = '<span class="snapclass-brand-icon snapclass-brand-icon-fallback">S</span>'

    st.markdown(
        f"""
        <div class="snapclass-brand-lockup" aria-label="SnapClass AI">
          {icon_html}
          <span class="snapclass-brand-name">
            <span>SnapClass</span><span class="snapclass-brand-ai"> AI</span>
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    """Render the compact brand header used by every authenticated portal."""
    path = logo_path(compact=True)
    if path:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        icon_html = (
            f'<img src="data:image/png;base64,{encoded}" alt="" '
            'class="sidebar-brand-logo">'
        )
    else:
        icon_html = '<span class="sidebar-brand-logo sidebar-brand-logo-fallback">S</span>'

    st.markdown(
        f"""
        <div class="sidebar-brand" aria-label="SnapClass AI">
          {icon_html}
          <div class="sidebar-brand-text">
            <div class="sidebar-brand-name">SnapClass AI</div>
            <div class="sidebar-brand-subtitle">Smart Attendance Platform</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
