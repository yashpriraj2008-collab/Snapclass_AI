from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import streamlit as st


def _app_env() -> str:
    value = str(os.getenv("APP_ENV") or "").strip().lower()
    if value:
        return value

    secrets_path = Path(__file__).resolve().parents[2] / ".streamlit" / "secrets.toml"
    try:
        if secrets_path.exists():
            import tomllib

            with secrets_path.open("rb") as fh:
                return str(tomllib.load(fh).get("APP_ENV", "")).strip().lower()
    except Exception:
        return ""
    return ""


def perf_enabled() -> bool:
    try:
        if bool(st.session_state.get("debug_mode")):
            return True
    except Exception:
        pass
    return _app_env() == "development"


@contextmanager
def time_block(label: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        if perf_enabled():
            try:
                st.caption(f"[perf] {label}: {elapsed_ms:.1f} ms")
            except Exception:
                print(f"[perf] {label}: {elapsed_ms:.1f} ms")
