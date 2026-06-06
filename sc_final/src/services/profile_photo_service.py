"""Profile photo and institute logo storage helpers."""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any


BUCKET_NAME = "profile-photos"
MAX_FILE_SIZE = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


def _safe_slug(value: str, fallback: str = "user") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return slug or fallback


def _safe_filename(email: str, original_name: str) -> str:
    ext = Path(str(original_name or "")).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".png"
    return f"{_safe_slug(email, 'user')}-{int(time.time() * 1000)}{ext}"


def _role_folder(role: str) -> str:
    role_norm = str(role or "").strip().lower()
    aliases = {
        "institute_admin": "admin",
        "institute-admin": "admin",
        "super_admin": "founder",
        "super-admin": "founder",
    }
    return aliases.get(role_norm, _safe_slug(role_norm, "user"))


def validate_profile_photo(uploaded_file: Any) -> tuple[bool, str]:
    if uploaded_file is None:
        return False, "Please select a photo first."

    original_name = str(getattr(uploaded_file, "name", "") or "")
    extension = Path(original_name).suffix.lower()
    content_type = str(getattr(uploaded_file, "type", "") or "").lower()
    if extension not in ALLOWED_EXTENSIONS or (
        content_type and content_type not in ALLOWED_CONTENT_TYPES
    ):
        return False, "Only JPG, JPEG, and PNG images are allowed."

    size = getattr(uploaded_file, "size", None)
    if size is None:
        try:
            size = len(uploaded_file.getvalue())
        except Exception:
            size = 0
    if int(size or 0) <= 0:
        return False, "The selected image is empty."
    if int(size) > MAX_FILE_SIZE:
        return False, "Profile photo must be 2 MB or smaller."
    return True, ""


def _public_url_value(response: Any) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        nested = response.get("data")
        if isinstance(nested, dict):
            nested_url = _public_url_value(nested)
            if nested_url:
                return nested_url
        return str(
            response.get("publicUrl")
            or response.get("public_url")
            or response.get("signedURL")
            or response.get("signed_url")
            or ""
        )
    return str(
        getattr(response, "public_url", "")
        or getattr(response, "publicUrl", "")
        or ""
    )


def upload_profile_photo(
    supabase: Any,
    uploaded_file: Any,
    email: str,
    role: str,
) -> str | None:
    valid, message = validate_profile_photo(uploaded_file)
    if not valid:
        raise ValueError(message)
    if not supabase:
        raise RuntimeError("Supabase is not connected.")

    role_folder = _role_folder(role)
    file_name = _safe_filename(email, getattr(uploaded_file, "name", "photo.png"))
    storage_path = f"{role_folder}/{file_name}"
    file_bytes = uploaded_file.getvalue()
    content_type = getattr(uploaded_file, "type", None) or "image/png"
    bucket = supabase.storage.from_(BUCKET_NAME)
    bucket.upload(
        storage_path,
        file_bytes,
        {
            "content-type": content_type,
            "upsert": "true",
        },
    )
    return _public_url_value(bucket.get_public_url(storage_path)) or None


def update_user_profile_photo(
    supabase: Any,
    *,
    email: str,
    role: str,
    photo_url: str,
) -> None:
    email_norm = str(email or "").strip().lower()
    role_norm = str(role or "").strip().lower()
    if not email_norm or not photo_url:
        raise ValueError("Email and photo URL are required.")

    supabase.table("user_profiles").update(
        {"profile_photo_url": photo_url}
    ).eq("email", email_norm).execute()

    role_table = {"student": "students", "teacher": "teachers"}.get(role_norm)
    if role_table:
        try:
            supabase.table(role_table).update(
                {"profile_photo_url": photo_url}
            ).eq("email", email_norm).execute()
        except Exception:
            # user_profiles remains the source of truth when a role table has
            # not received the optional profile_photo_url migration yet.
            pass


def fetch_user_profile(supabase: Any, email: str) -> dict[str, Any]:
    email_norm = str(email or "").strip().lower()
    if not supabase or not email_norm:
        return {}
    try:
        rows = (
            supabase.table("user_profiles")
            .select("*")
            .eq("email", email_norm)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else {}
    except Exception:
        return {}


def profile_photos_by_email(supabase: Any, emails: list[str]) -> dict[str, str]:
    clean = sorted({str(email or "").strip().lower() for email in emails if email})
    if not supabase or not clean:
        return {}
    try:
        rows = (
            supabase.table("user_profiles")
            .select("email,profile_photo_url")
            .in_("email", clean)
            .execute()
            .data
            or []
        )
    except Exception:
        return {}
    return {
        str(row.get("email") or "").strip().lower(): str(row.get("profile_photo_url") or "").strip()
        for row in rows
        if row.get("email") and row.get("profile_photo_url")
    }


def upload_institute_logo(
    supabase: Any,
    uploaded_file: Any,
    institute_id: str,
) -> str | None:
    valid, message = validate_profile_photo(uploaded_file)
    if not valid:
        raise ValueError(message)
    if not supabase or not institute_id:
        raise RuntimeError("Institute or Supabase connection is missing.")

    extension = Path(str(getattr(uploaded_file, "name", "") or "")).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        extension = ".png"
    storage_path = f"institute/{_safe_slug(institute_id, 'institute')}-{int(time.time() * 1000)}{extension}"
    bucket = supabase.storage.from_(BUCKET_NAME)
    bucket.upload(
        storage_path,
        uploaded_file.getvalue(),
        {
            "content-type": getattr(uploaded_file, "type", None) or "image/png",
            "upsert": "true",
        },
    )
    return _public_url_value(bucket.get_public_url(storage_path)) or None
