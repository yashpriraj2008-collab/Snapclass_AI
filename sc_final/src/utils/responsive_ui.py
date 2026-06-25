"""Responsive UI helpers for SnapClass Streamlit screens."""

from __future__ import annotations

import streamlit as st
from collections.abc import Iterable
from typing import Any


def inject_responsive_css() -> None:
    """Inject global responsive rules without changing app logic."""
    st.markdown(
        """
<style>

/* Ensure Streamlit columns never force horizontal scroll */
html, body, .stApp, .main { overflow-x: hidden !important; }

html,
body,
.stApp,
.main,
[class*="css"] {
  max-width: 100% !important;
  overflow-x: hidden !important;
}

* {
  box-sizing: border-box !important;
  overflow-wrap: anywhere;
}

h1,
h2,
h3,
h4,
h5,
h6 {
  letter-spacing: 0 !important;
}

.main .block-container,
[data-testid="stAppViewContainer"] .block-container {
  width: 100% !important;
  max-width: 1200px !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
}

img,
svg,
canvas,
video,
iframe {
  max-width: 100% !important;
}

.stButton > button {
  border-radius: 12px !important;
  min-height: 42px !important;
  white-space: normal !important;
  color: #111827 !important;
}

button[kind="primary"],
.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  color: #ffffff !important;
}

.custom-dark-button,
.custom-dark-button *,
.dark-button,
.dark-button * {
  color: #ffffff !important;
}

.sc-card,
.sc-stat,
.student-dashboard-card,
.today-class-card,
.platform-feature-card,
.platform-stats-strip,
[data-testid="stMetric"] {
  max-width: 100% !important;
}

div[data-testid="stDataFrame"],
div[data-testid="stDataEditor"],
div[data-testid="stTable"] {
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: auto !important;
}

div[data-testid="stDataFrame"] [role="grid"],
div[data-testid="stDataEditor"] [role="grid"] {
  min-width: max-content;
}

div[data-baseweb="popover"] {
  z-index: 999999 !important;
}

div[role="listbox"] {
  background-color: #ffffff !important;
  color: #111827 !important;
  border: 1px solid #e5e7eb !important;
}

div[role="option"] {
  background-color: #ffffff !important;
  color: #111827 !important;
  opacity: 1 !important;
  visibility: visible !important;
}

div[role="option"] span,
div[role="option"] div {
  color: #111827 !important;
  opacity: 1 !important;
  visibility: visible !important;
}

div[role="option"]:hover,
div[role="option"][aria-selected="true"] {
  background-color: #f3f4f6 !important;
  color: #111827 !important;
}

.stTabs [data-baseweb="tab-list"] {
  max-width: 100% !important;
  overflow-x: auto !important;
  flex-wrap: nowrap !important;
}

div[data-testid="stForm"] {
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

div[data-testid="stForm"] > form {
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
}

div[data-testid="stForm"] [data-testid="column"] {
  min-width: 0 !important;
}

div[data-testid="stForm"] .stButton > button {
  width: 100% !important;
}

.sc-class-item,
.sc-alert {
  min-width: 0 !important;
}

.stMarkdown div[style*="max-width"] {
  max-width: 100% !important;
}

.stMarkdown div[style*="margin:40px auto"],
.stMarkdown div[style*="margin: 40px auto"] {
  margin-left: auto !important;
  margin-right: auto !important;
}

@media (max-width: 768px) {
  /* Mobile-first type system */
  :root {
    --sc-heading-font-size: 1.375rem; /* ~22px */
    --sc-body-font-size: 0.875rem; /* ~14px */
  }

  .main .block-container,
  [data-testid="stAppViewContainer"] .block-container {
    max-width: 100% !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    padding-top: 1rem !important;
    padding-bottom: 5rem !important;
  }

  h1 {
    font-size: 2rem !important;
    line-height: 1.2 !important;
    letter-spacing: 0 !important;
  }

  h2 {
    font-size: 1.5rem !important;
    line-height: 1.25 !important;
    letter-spacing: 0 !important;
  }

  h3 {
    font-size: 1.2rem !important;
    line-height: 1.3 !important;
    letter-spacing: 0 !important;
  }

  p,
  label,
  .stMarkdown,
  [data-testid="stCaptionContainer"],
  [data-testid="stMarkdown"],
  span {
    font-size: var(--sc-body-font-size) !important;
    line-height: 1.45 !important;
  }

  /* Restore caption container sizing override for consistency */
  p,
  label,
  .stMarkdown,
  [data-testid="stCaptionContainer"] {
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
  }

  .stButton > button {
    width: 100% !important;
    min-height: 44px !important;
  }

  div[data-testid="stForm"] {
    padding: 0 !important;
  }

  div[data-testid="stForm"] > form {
    padding: 0 !important;
  }

  input,
  textarea,
  select {
    width: 100% !important;
    max-width: 100% !important;
    font-size: 16px !important;
  }

  .stTextInput,
  .stTextArea,
  .stSelectbox,
  .stDateInput,
  .stNumberInput,
  .stFileUploader,
  [data-testid="stForm"] {
    width: 100% !important;
    max-width: 100% !important;
  }

  .stTextInput label,
  .stTextArea label,
  .stSelectbox label,
  .stDateInput label,
  .stNumberInput label,
  .stFileUploader label {
    display: block !important;
    width: 100% !important;
    white-space: normal !important;
  }

  [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 0.75rem !important;
  }

  [data-testid="column"] {
    width: 100% !important;
    flex: 1 1 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
  }

  .sc-card {
    padding: 18px !important;
    border-radius: 16px !important;
    height: auto !important;
  }

  [data-testid="stMetric"] {
    padding: 14px 16px !important;
  }

  [data-testid="stMetricValue"] {
    font-size: 1.45rem !important;
  }

  section[data-testid="stSidebar"] {
    max-width: min(88vw, 320px) !important;
  }

  section[data-testid="stSidebar"] .stButton > button {
    min-height: 40px !important;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
  }

  .sc-navbar {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 12px !important;
    padding: 14px !important;
    border-radius: 18px !important;
  }

  .sc-nav-links {
    flex-wrap: wrap !important;
    gap: 10px !important;
  }

  .sc-hero {
    padding: 28px 6px 18px !important;
  }

  .sc-title {
    font-size: 2.2rem !important;
    line-height: 1.08 !important;
  }

  .sc-subtitle {
    font-size: 1rem !important;
    max-width: 100% !important;
  }

  .portal-section,
  .platform-features-section {
    padding-left: 0 !important;
    padding-right: 0 !important;
  }

  .portal-grid,
  .platform-features-grid,
  .platform-stats-strip {
    grid-template-columns: 1fr !important;
  }

  .snapbot-floating-button,
  .snapbot-float-btn {
    width: 54px !important;
    height: 54px !important;
    right: 14px !important;
    bottom: 14px !important;
    font-size: 24px !important;
  }

  .snapbot-panel {
    left: 10px !important;
    right: 10px !important;
    bottom: 76px !important;
    width: auto !important;
    max-width: none !important;
    height: min(72vh, 620px) !important;
    border-radius: 18px !important;
  }
}

@media (max-width: 480px) {
  /* Make any remaining fixed-width blocks wrap */
  [style*="width:"] { max-width: 100% !important; }


  :root {
    --sc-heading-font-size: 1.375rem; /* 22px */
    --sc-body-font-size: 0.875rem; /* 14px */
  }

  .main .block-container,
  [data-testid="stAppViewContainer"] .block-container {
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
  }

  h1 {
    font-size: 1.6rem !important;
  }

  h2 {
    font-size: 1.25rem !important;
  }

  h3 {
    font-size: 1.05rem !important;
  }

  .sc-card,
  .stMarkdown div[style*="padding:32px"],
  .stMarkdown div[style*="padding:36px"],
  .stMarkdown div[style*="padding: 32px"],
  .stMarkdown div[style*="padding: 36px"],
  [data-testid="stForm"] {
    padding: 14px !important;
  }

  .sc-title {
    font-size: 1.75rem !important;
  }

  .sc-portal-icon,
  .platform-feature-icon {
    width: 46px !important;
    height: 46px !important;
    font-size: 1.25rem !important;
  }

  .stDataFrame,
  .stTable {
    overflow-x: auto !important;
  }

  iframe {
    max-width: 100% !important;
  }

  .snapbot-panel {
    height: min(68vh, 560px) !important;
  }
}

/*
 * Authoritative global selectbox styling.
 * Keep this at the end so legacy screen CSS cannot clip selected values.
 */
div[data-testid="stSelectbox"] {
  min-width: 0 !important;
}

div[data-testid="stSelectbox"] label {
  color: #334155 !important;
  font-size: 0.86rem !important;
  font-weight: 650 !important;
  line-height: 1.35 !important;
  margin-bottom: 6px !important;
  background: transparent !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}

div[data-testid="stSelectbox"] label * {
  background: transparent !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] {
  width: 100% !important;
  height: 50px !important;
  min-height: 50px !important;
  overflow: visible !important;
  background: #ffffff !important;
  border: 1px solid #d8dee9 !important;
  border-radius: 14px !important;
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04) !important;
  color: #0f172a !important;
  opacity: 1 !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
  background: transparent !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  width: 100% !important;
  height: 48px !important;
  min-height: 48px !important;
  display: flex !important;
  align-items: center !important;
  overflow: hidden !important;
  padding: 0 6px 0 16px !important;
  margin: 0 !important;
  background: transparent !important;
  border: 0 !important;
  border-radius: 13px !important;
  box-shadow: none !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div {
  min-width: 0 !important;
  min-height: 0 !important;
  height: auto !important;
  display: flex !important;
  align-items: center !important;
  overflow: visible !important;
  padding: 0 !important;
  margin: 0 !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div:first-child {
  flex: 1 1 auto !important;
  min-width: 0 !important;
  padding-right: 10px !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div:last-child {
  flex: 0 0 38px !important;
  width: 38px !important;
  height: 48px !important;
  min-height: 48px !important;
  position: relative !important;
  justify-content: center !important;
  padding: 0 0 0 8px !important;
  border-left: 0 !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div:last-child::before {
  content: "" !important;
  position: absolute !important;
  top: 50% !important;
  left: 0 !important;
  width: 1px !important;
  height: 20px !important;
  background: #e2e8f0 !important;
  border: 0 !important;
  border-radius: 999px !important;
  transform: translateY(-50%) !important;
  pointer-events: none !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
div[data-testid="stSelectbox"] div[data-baseweb="select"] input,
div[data-testid="stSelectbox"] div[data-baseweb="select"] [class*="singleValue"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] [class*="SingleValue"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] [class*="placeholder"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] [class*="Placeholder"] {
  position: static !important;
  transform: none !important;
  width: auto !important;
  max-width: 100% !important;
  height: auto !important;
  min-height: 0 !important;
  overflow: hidden !important;
  color: #0f172a !important;
  -webkit-text-fill-color: #0f172a !important;
  font-size: 1rem !important;
  font-weight: 500 !important;
  line-height: 1.4 !important;
  white-space: nowrap !important;
  text-overflow: ellipsis !important;
  opacity: 1 !important;
  visibility: visible !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] input {
  appearance: none !important;
  -webkit-appearance: none !important;
  flex: 0 1 1px !important;
  width: 1px !important;
  min-width: 1px !important;
  height: 1px !important;
  min-height: 1px !important;
  background: transparent !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
  outline: 0 !important;
  caret-color: #0f172a !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
  width: 20px !important;
  height: 20px !important;
  flex: 0 0 20px !important;
  color: #334155 !important;
  fill: #334155 !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"]:hover {
  border-color: #a5b4fc !important;
  box-shadow: 0 5px 14px rgba(79, 70, 229, 0.08) !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
}

div[data-baseweb="popover"] ul[role="listbox"],
div[data-baseweb="popover"] div[role="listbox"] {
  padding: 6px !important;
  background: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.14) !important;
}

div[data-baseweb="popover"] li[role="option"],
div[data-baseweb="popover"] div[role="option"] {
  min-height: 40px !important;
  display: flex !important;
  align-items: center !important;
  padding: 9px 12px !important;
  border-radius: 8px !important;
  color: #0f172a !important;
  -webkit-text-fill-color: #0f172a !important;
  line-height: 1.35 !important;
}
</style>
""",
        unsafe_allow_html=True,
    )
