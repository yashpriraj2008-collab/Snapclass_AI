"""Reusable UI components for SnapClass authentication screens."""

from __future__ import annotations

import html

import streamlit as st

AUTH_MAX_WIDTH_PX = 520

_AUTH_CSS = """
<style>
[data-testid="stAppViewContainer"] {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: flex-start !important;
  min-height: 100dvh !important;
  background:
    radial-gradient(circle at top, rgba(99, 102, 241, 0.08), transparent 34rem),
    linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%) !important;
}

.main .block-container,
[data-testid="stAppViewContainer"] .block-container {
  width: min(520px, calc(100vw - 32px)) !important;
  max-width: 520px !important;
  margin: clamp(10px, 2vh, 18px) auto 12px !important;
  padding: 18px 32px 22px !important;
  background: rgba(255, 255, 255, 0.94) !important;
  border: 1px solid rgba(226, 232, 240, 0.95) !important;
  border-radius: 24px !important;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.12) !important;
  overflow: visible !important;
}


.main .block-container > div,
[data-testid="stAppViewContainer"] .block-container > div {
  max-width: 100% !important;
}

.sc-auth-brand {
  text-align: center;
  margin: 0 0 18px;
}

.sc-auth-logo {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  margin: 0 auto 10px;
  background: linear-gradient(135deg, #5b6cff 0%, #ec4899 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Poppins", "Inter", sans-serif;
  font-size: 0.95rem;
  font-weight: 900;
  letter-spacing: 0;
  box-shadow: 0 14px 34px rgba(91, 108, 255, 0.26);
}

.sc-auth-title {
  margin: 0 !important;
  color: #0f172a !important;
  font-family: "Poppins", "Inter", sans-serif !important;
  font-size: 1.6rem !important;
  font-weight: 900 !important;
  letter-spacing: 0 !important;
  line-height: 1.18 !important;
}

.sc-auth-subtitle {
  margin: 7px 0 0 !important;
  color: #475569 !important;
  font-size: 0.96rem !important;
  line-height: 1.5 !important;
}

.main .block-container label,
[data-testid="stAppViewContainer"] .block-container label {
  color: #334155 !important;
  font-size: 0.86rem !important;
  font-weight: 700 !important;
  line-height: 1.3 !important;
}

.main .block-container div[data-testid="stTextInput"],
.main .block-container div[data-testid="stTextInput"] *,
[data-testid="stAppViewContainer"] .block-container div[data-testid="stTextInput"],
[data-testid="stAppViewContainer"] .block-container div[data-testid="stTextInput"] * {
  max-width: 100% !important;
  box-sizing: border-box !important;
}

.main .block-container div[data-testid="stTextInput"] input,
[data-testid="stAppViewContainer"] .block-container div[data-testid="stTextInput"] input {
  height: 48px !important;
  min-height: 48px !important;
  border-radius: 12px !important;
  border: 1.5px solid #d5dbe7 !important;
  background: #ffffff !important;
  color: #111827 !important;
  font-size: 0.95rem !important;
  padding: 10px 14px !important;
  box-shadow: none !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

.main .block-container div[data-testid="stTextInput"] input:focus,
[data-testid="stAppViewContainer"] .block-container div[data-testid="stTextInput"] input:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.13) !important;
}

/* password toggle button – keep transparent background */
.main .block-container div[data-testid="stTextInput"] button,
[data-testid="stAppViewContainer"] .block-container div[data-testid="stTextInput"] button {
  background: transparent !important;
  border: none !important;
  color: #64748b !important;
}
.main .block-container div[data-testid="stTextInput"] button:hover,
[data-testid="stAppViewContainer"] .block-container div[data-testid="stTextInput"] button:hover {
  color: #334155 !important;
}

/* ghost back-button wrapper */
.sc-back-btn-wrapper {
  margin-bottom: 6px;
}
.sc-back-btn-wrapper .stButton > button {
  background: transparent !important;
  border: none !important;
  color: #6366f1 !important;
  -webkit-text-fill-color: #6366f1 !important;
  box-shadow: none !important;
  min-height: auto !important;
  height: auto !important;
  padding: 4px 0 !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  text-align: left !important;
}
.sc-back-btn-wrapper .stButton > button:hover {
  color: #4f46e5 !important;
  -webkit-text-fill-color: #4f46e5 !important;
  background: transparent !important;
}

.main .block-container .stButton > button,
[data-testid="stAppViewContainer"] .block-container .stButton > button {
  min-height: 46px !important;
  border-radius: 12px !important;
  border: 1px solid #e2e8f0 !important;
  background: #ffffff !important;
  color: #172033 !important;
  -webkit-text-fill-color: #172033 !important;
  font-size: 0.94rem !important;
  font-weight: 750 !important;
  letter-spacing: 0 !important;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06) !important;
}

.main .block-container .stButton > button[kind="primary"],
.main .block-container [data-testid="stBaseButton-primary"],
[data-testid="stAppViewContainer"] .block-container .stButton > button[kind="primary"],
[data-testid="stAppViewContainer"] .block-container [data-testid="stBaseButton-primary"] {
  min-height: 50px !important;
  border: none !important;
  background: linear-gradient(135deg, #5b6cff 0%, #ec4899 100%) !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  box-shadow: 0 14px 30px rgba(91, 108, 255, 0.24) !important;
}

.sc-google-btn-wrap {
  width: 100% !important;
  margin: 10px 0 0 !important;
}

.sc-google-btn {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 10px !important;
  width: 100% !important;
  min-height: 48px !important;
  padding: 0 18px !important;
  background: #ffffff !important;
  border: 1px solid #d9dee7 !important;
  border-radius: 12px !important;
  color: #1f2937 !important;
  -webkit-text-fill-color: #1f2937 !important;
  font-family: "Inter", "Google Sans", Arial, sans-serif !important;
  font-size: 0.95rem !important;
  font-weight: 750 !important;
  letter-spacing: 0 !important;
  line-height: 1.2 !important;
  text-decoration: none !important;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06) !important;
}

.sc-google-btn svg {
  width: 20px !important;
  height: 20px !important;
  flex: 0 0 20px !important;
}

.sc-google-btn span {
  color: #1f2937 !important;
  -webkit-text-fill-color: #1f2937 !important;
  font-size: 0.95rem !important;
  font-weight: 750 !important;
  white-space: normal !important;
}

.sc-google-btn-disabled {
  cursor: default !important;
  opacity: 0.68 !important;
}

.sc-auth-divider {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 20px 0;
}

.sc-auth-divider::before,
.sc-auth-divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: #e2e8f0;
}

.sc-auth-divider span {
  color: #94a3b8 !important;
  font-size: 0.76rem !important;
  font-weight: 800 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  white-space: nowrap !important;
}

.main .block-container .stTabs [data-baseweb="tab-list"],
[data-testid="stAppViewContainer"] .block-container .stTabs [data-baseweb="tab-list"] {
  width: 100% !important;
  padding: 4px !important;
  margin-bottom: 20px !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  background: #f1f5f9 !important;
  gap: 4px !important;
}

.main .block-container .stTabs [data-baseweb="tab"],
[data-testid="stAppViewContainer"] .block-container .stTabs [data-baseweb="tab"] {
  flex: 1 1 0 !important;
  border-radius: 9px !important;
  color: #64748b !important;
  font-size: 0.88rem !important;
  font-weight: 750 !important;
  letter-spacing: 0 !important;
}

.main .block-container .stTabs [aria-selected="true"],
[data-testid="stAppViewContainer"] .block-container .stTabs [aria-selected="true"] {
  background: #ffffff !important;
  color: #4f46e5 !important;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08) !important;
}

.main .block-container hr,
[data-testid="stAppViewContainer"] .block-container hr {
  margin: 18px 0 !important;
  border-color: #e2e8f0 !important;
}

.main .block-container [data-testid="stHorizontalBlock"],
[data-testid="stAppViewContainer"] .block-container [data-testid="stHorizontalBlock"] {
  gap: 0.75rem !important;
}

@media (max-width: 640px) {
  .main .block-container,
  [data-testid="stAppViewContainer"] .block-container {
    width: min(100%, calc(100vw - 20px)) !important;
    margin: 10px auto 20px !important;
    padding: 22px 16px 24px !important;
    border-radius: 18px !important;
  }

  .sc-auth-title {
    font-size: 1.45rem !important;
  }

  .main .block-container [data-testid="stHorizontalBlock"],
  [data-testid="stAppViewContainer"] .block-container [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
  }

  .main .block-container [data-testid="column"],
  [data-testid="stAppViewContainer"] .block-container [data-testid="column"] {
    flex: 1 1 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
  }
}
</style>
"""


def _auth_bg() -> None:
    """Apply auth-page styling after the global CSS has loaded."""
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)




def AuthCard() -> None:
    """Apply the shared auth-card styling for the current page (portal-card rhythm)."""

    _auth_bg()
    # Give the auth container a stable max-width/padding consistent with portal-card.
    # Auth pages build their internal layout using AuthHeader/AuthBackButton.
    st.markdown('<div class="portal-card">', unsafe_allow_html=True)



def AuthCardEnd() -> None:
    """Close the portal-card wrapper opened by AuthCard()."""
    st.markdown('</div>', unsafe_allow_html=True)
    return


def AuthBackButton(key: str = "auth_back_default") -> None:
    """Compact back-to-home action for auth screens."""
    # Use global spacing token classes so every portal/auth screen
    # stays consistent (logo/header -> 32px -> back -> 48px -> content)
    st.markdown('<div class="portal-back-button sc-back-btn-wrapper">', unsafe_allow_html=True)
    if st.button("← Back", key=key, use_container_width=False):
        st.session_state.page = "landing"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def AuthHeader(*, title: str, subtitle: str | None = None, brand_text: str = "SC") -> None:
    """Brand logo + title for auth/portal screens (spacing-rhythm aligned)."""
    initials = (brand_text or "SC").strip().upper()[:3]
    title_html = html.escape(title)
    subtitle_html = (
        f'<p class="sc-auth-subtitle">{html.escape(subtitle)}</p>'
        if subtitle
        else ""
    )

    # Align to global portal hierarchy:
    # portal-header (logo/title) -> 32px -> back button -> 48px -> icon/title/desc stack handled by auth card content.
    st.markdown(
        f"""
<div class="portal-header sc-auth-brand">
  <div class="sc-auth-logo" aria-hidden="true">{html.escape(initials)}</div>
  <h2 class="sc-auth-title">{title_html}</h2>
</div>

{subtitle_html}
""".strip(),
        unsafe_allow_html=True,
    )


def GoogleButton(oauth_url: str | None, *, label: str = "Continue with Google") -> None:
    """Render a compact Google OAuth button with a disabled fallback."""
    google_svg = """<svg width="20" height="20" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20 20 20 20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"/><path fill="#FF3D00" d="m6.306 14.691 6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 16.318 4 9.656 8.337 6.306 14.691z"/><path fill="#4CAF50" d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0 1 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z"/><path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.087 5.571l.003-.002 6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z"/></svg>"""
    safe_label = html.escape(label)

    if oauth_url:
        safe_url = html.escape(oauth_url, quote=True)
        button_html = f'''
<a class="sc-google-btn" href="{safe_url}" target="_self">
  {google_svg}
  <span>{safe_label}</span>
</a>'''
    else:
        button_html = f'''
<div class="sc-google-btn sc-google-btn-disabled" aria-disabled="true">
  {google_svg}
  <span>{safe_label}</span>
</div>'''

    st.markdown(
        f'<div class="sc-google-btn-wrap">{button_html}</div>',
        unsafe_allow_html=True,
    )


def AuthDivider() -> None:
    """OR divider between Google and email form."""
    st.markdown(
        '<div class="sc-auth-divider"><span>or continue with</span></div>',
        unsafe_allow_html=True,
    )


def AuthInput(label: str, *, key: str, placeholder: str = "", type: str = "default") -> str:
    """Labeled input constrained to the auth card width."""
    if type == "password":
        return st.text_input(label, placeholder=placeholder, type="password", key=key)
    return st.text_input(label, placeholder=placeholder, key=key)


def AuthButton(text: str, *, key: str, primary: bool = True, disabled: bool = False) -> bool:
    """Primary CTA button. Returns True if clicked."""
    return st.button(
        text,
        key=key,
        type="primary" if primary else "secondary",
        use_container_width=True,
        disabled=disabled,
    )