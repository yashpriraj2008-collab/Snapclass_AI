"""UI helpers — CSS loader, status banner, navbar."""
from pathlib import Path
import os
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]

def _debug_enabled() -> bool:
    app_env = str(os.getenv("APP_ENV", "production")).strip().lower()
    return app_env == "development" or bool(st.session_state.get("debug_mode", False))

def load_css():
    css = ""
    for f in ["style.css", "chatbot.css"]:
        p = ROOT / "static" / f
        if not p.exists():
            continue
        try:
            css += p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def navbar(show_links: bool = True):
    from src.components.public_nav import render_public_nav
    render_public_nav(show_links=show_links)

def db_status_banner():
    if not _debug_enabled():
        return
    from src.database.client import get_supabase
    if get_supabase() is None:
        st.markdown("""<div style="background:#EFF6FF;border:1px solid #BFDBFE;
          border-radius:10px;padding:8px 14px;margin-bottom:18px;
          font-size:.82rem;font-weight:500;color:#1D4ED8;">
          🔵 <strong>Demo Mode</strong> — Add Supabase keys to secrets.toml for live data.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:#ECFDF5;border:1px solid #A7F3D0;
          border-radius:10px;padding:8px 14px;margin-bottom:18px;
          font-size:.82rem;font-weight:500;color:#065F46;">
          🟢 <strong>Supabase Connected</strong> — Live data active.
        </div>""", unsafe_allow_html=True)

def show_connection_status():
    db_status_banner()

def page_header(title: str, subtitle: str = ""):
    st.markdown(f"<h1 style='margin-bottom:4px;'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p style='color:#6B7280;margin-top:0;margin-bottom:20px;'>{subtitle}</p>",
                    unsafe_allow_html=True)


def render_portal_badge(
    role: str,
    institute_name: str | None = None,
    plan: str | None = None,
    status: str | None = None,
) -> None:
    institute_text = institute_name or "No institute selected"
    plan_text = plan or "No plan"
    status_text = status or "Unknown"
    st.markdown(
        f"""
        <style>
        .portal-badge {{
            width: 100%;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 14px 18px;
            margin-bottom: 20px;
            display: flex;
            gap: 18px;
            align-items: center;
            flex-wrap: wrap;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            color: #111827;
        }}
        .portal-badge strong {{
            color: #4f46e5;
        }}
        </style>
        <div class="portal-badge">
            <strong>{role} Portal</strong>
            <span>{institute_text}</span>
            <span>{plan_text}</span>
            <span>{status_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
