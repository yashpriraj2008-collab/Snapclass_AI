from __future__ import annotations

from pathlib import Path
from typing import Any
import html


def _read_embed_html() -> str:
    # HTML lives in src/services/realtime_attendance_js.html
    here = Path(__file__).resolve().parent
    p = here / "realtime_attendance_js.html"
    if not p.exists():
        # Hard-fail so caller sees misconfiguration.
        raise FileNotFoundError(f"Missing realtime embed html: {p}")
    return p.read_text(encoding="utf-8")


def build_realtime_embed_html(
    *,
    supabase_url: str,
    supabase_anon_key: str,
    student_id: str,
) -> str:
    """Return the HTML snippet to embed with st.components.v1.html.

    Uses placeholder replacement for:
    - __SUPABASE_URL__
    - __SUPABASE_ANON_KEY__
    - __STUDENT_ID__

    IMPORTANT:
    We intentionally do HTML escaping inside the script-injection layer.
    """

    html_template = _read_embed_html()

    # Inject values via window globals.
    inject = (
        "<script>\n"
        f"window.__SUPABASE_URL__ = {html.escape(supabase_url)!r};\n"
        f"window.__SUPABASE_ANON_KEY__ = {html.escape(supabase_anon_key)!r};\n"
        f"window.__STUDENT_ID__ = {html.escape(student_id)!r};\n"
        "</script>\n"
    )

    # Place injection early in <body>.
    marker = "<body>"
    if marker not in html_template:
        # fallback: just prefix
        composed = inject + html_template
    else:
        composed = html_template.replace(marker, marker + "\n" + inject)

    return composed

