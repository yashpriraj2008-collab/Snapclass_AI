"""Responsive UI helpers for SnapClass Streamlit screens."""

from __future__ import annotations

import streamlit as st


def inject_responsive_css() -> None:
    """Inject global responsive rules without changing app logic."""
    st.markdown(
        """
<style>
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

button,
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

/* Fix Streamlit/BaseWeb selectbox visibility globally. */
div[data-baseweb="select"] > div {
  background-color: #ffffff !important;
  color: #111827 !important;
  border: 1px solid #d1d5db !important;
  border-radius: 10px !important;
  min-height: 44px !important;
  opacity: 1 !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] input,
div[data-baseweb="select"] svg {
  color: #111827 !important;
  fill: #111827 !important;
  opacity: 1 !important;
  visibility: visible !important;
}

[data-testid="stSelectbox"] label {
  color: #111827 !important;
  font-weight: 600 !important;
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

.stSelectbox * {
  visibility: visible !important;
}

.stTabs [data-baseweb="tab-list"] {
  max-width: 100% !important;
  overflow-x: auto !important;
  flex-wrap: nowrap !important;
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
  [data-testid="stCaptionContainer"] {
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
  }

  .stButton > button {
    width: 100% !important;
    min-height: 44px !important;
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
</style>
""",
        unsafe_allow_html=True,
    )
