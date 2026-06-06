from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, TypeVar

import streamlit as st

T = TypeVar("T")


def safe_selectbox(
    label: str,
    options: Sequence[T] | None,
    key: str,
    label_func: Callable[[T], Any] | None = None,
    placeholder: str = "Choose option",
    disabled: bool = False,
) -> T | None:
    """Readable selectbox for Supabase records and other object options."""
    clean_options = list(options or [])

    if not clean_options:
        st.selectbox(
            label,
            [placeholder],
            key=f"{key}_empty",
            disabled=True,
        )
        return None

    display_options: list[T | None] = [None] + clean_options

    def format_option(option: T | None) -> str:
        if option is None:
            return placeholder
        if label_func:
            try:
                return str(label_func(option))
            except Exception:
                return str(option)
        return str(option)

    selected = st.selectbox(
        label,
        display_options,
        key=key,
        format_func=format_option,
        disabled=disabled,
    )

    return selected
