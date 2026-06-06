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
    plan_name: str = "",
    payment_link_id: str = "",
) -> bool:
    """Activate a verified paid subscription and keep all access flags aligned."""
    db = get_supabase_client()
    institute_id = str(institute_id or "").strip()
    plan_id = str(plan_id or "").strip()
    if db is None or not institute_id or not plan_id:
        return False

    starts_at = _now()
    ends_at = starts_at + _dt.timedelta(days=30)
    cycle = str(billing_cycle or "monthly").strip().lower()
    selected_plan = str(plan_name or "").strip()
    if not selected_plan:
        try:
            rows = db.table("plans").select("*").eq("id", plan_id).limit(1).execute().data or []
            plan = rows[0] if rows else {}
            selected_plan = str(
                plan.get("display_name")
                or plan.get("name")
                or plan.get("plan_code")
                or ""
            ).strip()
        except Exception:
            selected_plan = ""
    if not selected_plan:
        return False

    try:
        payload = {
            "institute_id": institute_id,
            "plan_id": plan_id,
            "plan_name": selected_plan,
            "billing_cycle": cycle,
            "status": "pending_payment",
            "payment_status": "paid",
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "current_period_start": starts_at.isoformat(),
            "current_period_end": ends_at.isoformat(),
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "updated_at": starts_at.isoformat(),
        }

        existing = (
            db.table("subscriptions")
            .select("id")
            .eq("institute_id", institute_id)
            .limit(1)
            .execute()
            .data
            or []
        )

        # Write all non-gating fields first. Access remains locked until the
        # final two status updates complete.
        if existing:
            db.table("subscriptions").update(payload).eq("institute_id", institute_id).execute()
        else:
            db.table("subscriptions").insert(payload).execute()

        order_updated = False
        order_filters = []
        if payment_link_id:
            order_filters.append(("razorpay_payment_link_id", payment_link_id))
        if razorpay_order_id:
            order_filters.extend(
                [
                    ("order_id", razorpay_order_id),
                    ("razorpay_order_id", razorpay_order_id),
                    ("razorpay_payment_link_id", razorpay_order_id),
                ]
            )
        for column, value in order_filters:
            try:
                rows = (
                    db.table("payment_orders")
                    .update(
                        {
                            "status": "paid",
                            "razorpay_payment_id": razorpay_payment_id,
                            "paid_at": starts_at.isoformat(),
                            "updated_at": starts_at.isoformat(),
                        }
                    )
                    .eq(column, value)
                    .execute()
                    .data
                    or []
                )
                if rows:
                    order_updated = True
                    break
                verified = (
                    db.table("payment_orders")
                    .select("status")
                    .eq(column, value)
                    .eq("status", "paid")
                    .limit(1)
                    .execute()
                    .data
                    or []
                )
                if verified:
                    order_updated = True
                    break
            except Exception:
                continue
        if order_filters and not order_updated:
            raise RuntimeError("Verified payment order could not be marked paid.")

        db.table("institutes").update(
            {
                "plan": selected_plan,
                "status": "active",
                "subscription_status": "active",
                "updated_at": starts_at.isoformat(),
            }
        ).eq("id", institute_id).execute()
        db.table("subscriptions").update(
            {"status": "active", "updated_at": starts_at.isoformat()}
        ).eq("institute_id", institute_id).execute()

        institute_rows = (
            db.table("institutes")
            .select("plan,subscription_status")
            .eq("id", institute_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        subscription_rows = (
            db.table("subscriptions")
            .select("status,plan_name,current_period_start,current_period_end")
            .eq("institute_id", institute_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        final_institute = institute_rows[0] if institute_rows else {}
        final_subscription = subscription_rows[0] if subscription_rows else {}
        if (
            str(final_institute.get("subscription_status") or "").lower() != "active"
            or str(final_subscription.get("status") or "").lower() != "active"
            or str(final_institute.get("plan") or "") != selected_plan
            or str(final_subscription.get("plan_name") or "") != selected_plan
            or not final_subscription.get("current_period_start")
            or not final_subscription.get("current_period_end")
        ):
            raise RuntimeError("Subscription activation could not be verified.")
        return True
    except Exception:
        # Best-effort compensation prevents a partial write from unlocking the
        # portal through either canonical status field.
        try:
            db.table("institutes").update(
                {"subscription_status": "pending_payment"}
            ).eq("id", institute_id).execute()
        except Exception:
            pass
        try:
            db.table("subscriptions").update(
                {"status": "pending_payment"}
            ).eq("institute_id", institute_id).execute()
        except Exception:
            pass
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

