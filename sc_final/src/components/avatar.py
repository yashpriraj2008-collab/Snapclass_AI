"""Reusable user and institute image components."""
from __future__ import annotations

import html
from typing import Any

import streamlit as st

from src.services.profile_photo_service import (
    update_user_profile_photo,
    upload_profile_photo,
    validate_profile_photo,
)


def avatar_html(
    user: dict[str, Any] | None,
    *,
    size: int = 48,
    border_color: str = "#E5E7EB",
    css_class: str = "",
) -> str:
    user = user or {}
    name = str(user.get("full_name") or user.get("name") or "User").strip() or "User"
    photo_url = str(user.get("profile_photo_url") or "").strip()
    class_attr = f' class="{html.escape(css_class, quote=True)}"' if css_class else ""
    if photo_url:
        return (
            f'<img{class_attr} src="{html.escape(photo_url, quote=True)}" alt="{html.escape(name, quote=True)}" '
            f'style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;'
            f'border:2px solid {html.escape(border_color, quote=True)};flex-shrink:0;">'
        )
    initial = html.escape(name[:1].upper() or "U")
    font_size = max(13, int(size * 0.4))
    return (
        f'<div{class_attr} style="width:{size}px;height:{size}px;border-radius:50%;'
        "background:linear-gradient(135deg,#6366F1,#EC4899);color:#fff;"
        "display:flex;align-items:center;justify-content:center;flex-shrink:0;"
        f'font-size:{font_size}px;font-weight:850;">{initial}</div>'
    )


def render_avatar(user: dict[str, Any] | None, size: int = 48) -> None:
    st.markdown(avatar_html(user, size=size), unsafe_allow_html=True)


def render_profile_photo_section(
    supabase: Any,
    user: dict[str, Any],
    *,
    key_prefix: str,
) -> None:
    name = str(user.get("full_name") or user.get("name") or "User")
    email = str(user.get("email") or "").strip().lower()
    role = str(user.get("role") or "user").strip().lower()

    st.markdown("#### Profile Photo")
    left, right = st.columns([1, 4], gap="large", vertical_alignment="center")
    with left:
        st.markdown(
            (
                '<div style="display:flex;align-items:center;justify-content:center;'
                'width:100%;padding:12px 0;">'
                f"{avatar_html(user, size=118)}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    with right:
        st.caption("JPG or PNG, maximum 2 MB. A square photo works best.")
        uploaded_photo = st.file_uploader(
            "Upload profile photo",
            type=["png", "jpg", "jpeg"],
            key=f"{key_prefix}_photo_upload",
        )
        if st.button(
            "Update Profile Photo",
            type="primary",
            key=f"{key_prefix}_photo_update",
        ):
            valid, message = validate_profile_photo(uploaded_photo)
            if not valid:
                st.warning(message)
                return
            if not email:
                st.error("Your account email is missing. Please log in again.")
                return
            try:
                photo_url = upload_profile_photo(supabase, uploaded_photo, email, role)
                if not photo_url:
                    raise RuntimeError("Supabase Storage did not return a public URL.")
                update_user_profile_photo(
                    supabase,
                    email=email,
                    role=role,
                    photo_url=photo_url,
                )
                st.session_state["profile_photo_url"] = photo_url
                session_user = st.session_state.get("user")
                if not isinstance(session_user, dict):
                    session_user = {}
                st.session_state["user"] = {
                    **session_user,
                    "email": session_user.get("email") or email,
                    "role": session_user.get("role") or role,
                    "profile_photo_url": photo_url,
                }
                st.success(f"{name}'s profile photo was updated.")
                st.cache_data.clear()
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))
            except Exception:
                st.error(
                    "Photo upload failed. Confirm the profile-photos bucket and database migration are configured."
                )
