"""Subscription service.

Phase 5 Part A:
- Activate subscription after successful Razorpay signature verification.
- Enforce plan limits for key features (students/teachers/features).

Current implementation is DB-backed via Supabase client. If Supabase is not
configured, functions will return safe defaults.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Optional

import streamlit as st

from src.database.client import get_supabase_client


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def get_active_subscription(institute_id: str) -> Optional[dict]:

    db = get_supabase_client()
    if db is None:
        return None

    try:
        res = (
            db.table("subscriptions")
            .select("*")
            .eq("institute_id", institute_id)
            .eq("status", "active")
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def _get_plan_limits(plan_code: str) -> dict:
    db = get_supabase_client()
    if db is None:
        return {}

    try:
        res = db.table("plans").select("limits").eq("plan_code", plan_code).limit(1).execute()
        rows = res.data or []
        if not rows:
            return {}
        return rows[0].get("limits") or {}
    except Exception:
        return {}


def _get_feature_flags(plan_code: str) -> dict:
    db = get_supabase_client()
    if db is None:
        return {}

    try:
        res = db.table("plans").select("feature_flags").eq("plan_code", plan_code).limit(1).execute()
        rows = res.data or []
        if not rows:
            return {}
        return rows[0].get("feature_flags") or {}
    except Exception:
        return {}


def activate_subscription(
    *,
    institute_id: str,
    plan_id: str,
    billing_cycle: str,
    razorpay_order_id: str,
    razorpay_payment_id: str,
) -> bool:
    """Activate subscription for an institute.

    - monthly: ends_at = now()+30 days
    - yearly: ends_at = now()+365 days
    - forever: ends_at = now()+100 years (approx)
    """
    db = get_supabase_client()
    if db is None:
        return False

    starts_at = _now()
    cycle = str(billing_cycle or "monthly").strip().lower()

    # Phase 5 spec: successful Razorpay test payment activates monthly subscription.
    if cycle == "monthly":
        ends_at = starts_at + _dt.timedelta(days=30)
    elif cycle == "yearly":
        ends_at = starts_at + _dt.timedelta(days=365)
    else:
        ends_at = starts_at + _dt.timedelta(days=365 * 100)

    try:
        # Upsert by institute_id
        payload = {
            "institute_id": institute_id,
            "plan_id": plan_id,
            "billing_cycle": cycle,
            "status": "active",
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
        }

        # We don't know PK/upsert constraints; use manual delete+insert safest.
        # subscription table has institute_id as unique.
        db.table("subscriptions").delete().eq("institute_id", institute_id).execute()
        db.table("subscriptions").insert(payload).execute()
        return True
    except Exception:
        return False


def is_feature_enabled(institute_id: str, feature: str) -> bool:
    sub = get_active_subscription(institute_id)
    if not sub:
        return False

    plan_code = _get_plan_code_by_id(sub.get("plan_id"))
    flags = _get_feature_flags(plan_code or "")
    return bool(flags.get(feature, False))


def _get_plan_code_by_id(plan_id: str) -> str:
    db = get_supabase_client()
    if db is None:
        return ""

    try:
        res = db.table("plans").select("plan_code").eq("id", plan_id).limit(1).execute()
        rows = res.data or []
        if not rows:
            return ""
        return str(rows[0].get("plan_code") or "")
    except Exception:
        return ""


def check_plan_limit(institute_id: str, feature: str) -> tuple[bool, str]:
    """Return (can_use, message)."""
    sub = get_active_subscription(institute_id)
    if not sub:
        return False, "No active subscription."

    plan_code = _get_plan_code_by_id(sub.get("plan_id"))
    limits = _get_plan_limits(plan_code or "")

    # feature naming mapping
    if feature == "max_students":
        max_students = limits.get("max_students")
        return _enforce_numeric_limit(institute_id, max_students, "Plan limit reached. Upgrade to continue.", "students")

    if feature == "max_teachers":
        max_teachers = limits.get("max_teachers")
        return _enforce_numeric_limit(institute_id, max_teachers, "Plan limit reached. Upgrade to continue.", "teachers")

    # For feature toggles like ai_attendance, reports_export, email_alerts
    enabled = is_feature_enabled(institute_id, feature)
    if enabled:
        return True, ""
    return False, "Plan limit reached. Upgrade to continue."


def _enforce_numeric_limit(institute_id: str, max_value: Any, msg: str, kind: str) -> tuple[bool, str]:
    # enterprise/custom: null means unlimited
    if max_value is None:
        return True, ""

    try:
        max_int = int(max_value)
    except Exception:
        return True, ""

    count = _count_entities(institute_id, kind)
    if count >= max_int:
        return False, msg
    return True, ""


def _count_entities(institute_id: str, kind: str) -> int:
    db = get_supabase_client()
    if db is None:
        return 0

    try:
        if kind == "students":
            res = db.table("students").select("id", count=True).eq("institute_id", institute_id).execute()
        else:
            res = db.table("teachers").select("id", count=True).eq("institute_id", institute_id).execute()

        # Supabase python client returns different shapes depending version.
        data = getattr(res, "count", None)
        if isinstance(data, int):
            return data
        if isinstance(getattr(res, "data", None), list):
            return len(res.data)
        return 0
    except Exception:
        return 0


def can_add_student(institute_id: str) -> bool:
    ok, _ = check_plan_limit(institute_id, "max_students")
    return ok


def can_add_teacher(institute_id: str) -> bool:
    ok, _ = check_plan_limit(institute_id, "max_teachers")
    return ok

