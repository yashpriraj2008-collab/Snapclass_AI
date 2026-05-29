from __future__ import annotations

import html
from typing import Any, Dict, List

import streamlit as st

from src.services.bot_service import get_bot_response, get_suggested_questions, normalize_role


def update_snapbot_context(**kwargs: Any) -> None:
    if "snapbot_context" not in st.session_state:
        st.session_state.snapbot_context = {}

    for key, value in kwargs.items():
        if value is not None:
            st.session_state.snapbot_context[key] = value


def _safe(value: Any, default: str = "Not available") -> str:
    return default if value is None or value == "" else str(value)


def _context() -> Dict[str, Any]:
    return dict(st.session_state.get("snapbot_context", {}))


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _current_page() -> str:
    context = _context()
    return _normalize(context.get("current_page") or context.get("screen") or "home")


def _current_role() -> str:
    context = _context()
    return _normalize(context.get("current_role") or context.get("role") or "public")


def _current_user_name() -> str:
    context = _context()
    return _safe(context.get("current_user_name") or context.get("user_name") or context.get("name"), "User")


def _current_last_error() -> str:
    context = _context()
    return _safe(context.get("last_error"), "")


def _question_bank(current_role: str, current_page: str) -> List[str]:
    return get_suggested_questions(current_role=current_role, current_page=current_page)


def _render_answer_card(response: Dict[str, Any]) -> str:
    title = html.escape(str(response.get("title", "")))
    answer = html.escape(str(response.get("answer", "")))
    checks = response.get("checks") or []
    tables = response.get("tables") or []
    next_action = html.escape(str(response.get("next_action", "")))

    checks_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in checks) or "<li>No extra checks available.</li>"
    tables_html = ", ".join(html.escape(str(item)) for item in tables) if tables else "No Supabase table needed."

    return f"""
    <div class="snapbot-answer-card">
      <div class="snapbot-answer-heading">Problem</div>
      <div class="snapbot-answer-title">{title}</div>

      <div class="snapbot-answer-heading">Why this happens</div>
      <div class="snapbot-answer-text">{answer}</div>

      <div class="snapbot-answer-heading">What to check</div>
      <ul class="snapbot-list">{checks_html}</ul>

      <div class="snapbot-answer-heading">Supabase table</div>
      <div class="snapbot-answer-note">{tables_html}</div>

      <div class="snapbot-answer-heading">Next action</div>
      <div class="snapbot-answer-next">{next_action}</div>
    </div>
    """


def render_snapbot_floating(
    context: Dict[str, Any] | None = None,
    *,
    current_role: str | None = None,
    current_page: str | None = None,
) -> None:
    if "snapbot_context" not in st.session_state:
        st.session_state.snapbot_context = {}

    if context:
        update_snapbot_context(**context)

    if current_role is not None:
        update_snapbot_context(current_role=current_role)
    if current_page is not None:
        update_snapbot_context(current_page=current_page)

    merged_context = _context()
    role = normalize_role(current_role or merged_context.get("current_role") or merged_context.get("role") or "public")
    page = _normalize(current_page or merged_context.get("current_page") or merged_context.get("screen") or "home")

    questions = _question_bank(role, page)
    current_user_name = _current_user_name()
    current_error = _current_last_error()

    item_html = ""
    answer_css = ""

    for index, question in enumerate(questions):
        response = get_bot_response(
            question=question,
            current_page=page,
            current_role=role,
            context={
                **merged_context,
                "user_name": current_user_name,
                "last_error": current_error,
            },
        )

        item_html += f"""
        <div class="snapbot-item">
          <input type="radio" name="snapbot-question" id="snapbot-q{index}" class="snapbot-radio" {"checked" if index == 0 else ""}>
          <label for="snapbot-q{index}" class="snapbot-question snapbot-question-card">
            <span class="snapbot-question-title">{html.escape(str(response.get("title", question)))}</span>
            <span class="snapbot-question-sub">{html.escape(question)}</span>
          </label>
          <div class="snapbot-answer">
            {_render_answer_card(response)}
          </div>
        </div>
        """
        answer_css += f"#snapbot-q{index}:checked + .snapbot-question + .snapbot-answer{{display:block;}}"

    panel_note = "Choose a question to see page-aware help."
    if current_error:
        panel_note = f"Last error captured: {current_error}"

    snapbot_html = f"""
<style>
.snapbot-toggle:checked~.snapbot-panel{{display:flex;}}
.snapbot-answer{{display:none;margin-top:10px;}}
{answer_css}
</style>
<input type="checkbox" id="snapbot-toggle" class="snapbot-toggle">
<label for="snapbot-toggle" class="snapbot-floating-button snapbot-float-btn" aria-label="Open SnapClass Bot">&#129302;</label>
<div class="snapbot-panel" role="dialog" aria-label="SnapClass Bot">
  <div class="snapbot-header">
    <div class="snapbot-header-left">
      <div class="snapbot-avatar">&#129302;</div>
      <div>
        <div class="snapbot-title">SnapClass Bot</div>
        <div class="snapbot-subtitle">Page-aware support for {html.escape(page.replace('_', ' ').title())}</div>
      </div>
    </div>
    <label for="snapbot-toggle" class="snapbot-close" aria-label="Close SnapClass Bot">&times;</label>
  </div>
  <div class="snapbot-body">
    <div class="snapbot-role-badge">&#128100; {html.escape(current_user_name)} &bull; {html.escape(role or "public")}</div>
    <div class="snapbot-section-title">Try asking:</div>
    <div class="snapbot-question-list">
      {item_html}
    </div>
  </div>
  <div class="snapbot-footer">
    {html.escape(panel_note)} Full typing input comes in a later version.
  </div>
</div>
"""

    snapbot_html = "\n".join(line.strip() for line in snapbot_html.splitlines() if line.strip())
    st.markdown(snapbot_html, unsafe_allow_html=True)
