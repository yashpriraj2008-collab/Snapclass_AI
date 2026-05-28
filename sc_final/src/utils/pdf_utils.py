from __future__ import annotations

import os
from typing import Optional


# NOTE:
# fpdf (fpdf2) built-in core fonts (Helvetica) do NOT support many Unicode glyphs
# such as the em dash —. To avoid FPDFUnicodeEncodingException, we either:
# 1) sanitize text to ASCII-compatible characters when using core fonts
# 2) or use a Unicode TTF font.
#
# This helper takes the safer route: if a Unicode font isn't provided,
# it replaces problematic glyphs with ASCII equivalents.


def sanitize_for_core_font(text: str) -> str:
    """Replace characters that are commonly unsupported by core FPDF fonts."""
    # em dash and en dash
    text = text.replace("—", "-" ).replace("–", "-")
    # non-breaking space
    text = text.replace("\u00A0", " ")
    return text


def get_unicode_font_path(font_filename: str = "DejaVuSans.ttf") -> Optional[str]:
    """Return absolute path to a Unicode font if present.

    You can place DejaVuSans.ttf under snapclass/static/fonts/.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))  # .../src
    candidate = os.path.join(base_dir, "static", "fonts", font_filename)
    if os.path.exists(candidate):
        return candidate
    return None

