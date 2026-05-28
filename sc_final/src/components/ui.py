"""UI helpers — CSS loader, status banner, navbar."""
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]

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

def page_header(title: str, subtitle: str = ""):
    st.markdown(f"<h1 style='margin-bottom:4px;'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p style='color:#6B7280;margin-top:0;margin-bottom:20px;'>{subtitle}</p>",
                    unsafe_allow_html=True)
