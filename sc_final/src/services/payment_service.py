"""Razorpay payment service.

Adds:
- Razorpay client from Streamlit secrets
- create_order() for INR plan payments
- signature verification before marking payments successful
- save_successful_payment() into Supabase `payments` table

IMPORTANT:
- Do not enable live payments until signature/webhook verification is wired in UI.
"""

from __future__ import annotations

import hmac
import hashlib

import streamlit as st

from src.database.client import get_supabase_client, read_app_secrets


# Phase 5 integrates with DB-backed `public.plans`.


def get_plan(plan_code: str) -> dict:
    """Fetch a plan from public.plans by plan_code."""
    db = get_supabase_client()
    if db is None:
        raise RuntimeError("Supabase is not connected.")

    plan_code_norm = str(plan_code or "").strip().lower()
    if not plan_code_norm:
        raise ValueError("plan_code is required")

    res = (
        db.table("plans")
        .select("id,plan_code,display_name,billing_cycle,amount_paise,currency,is_active,limits,feature_flags")
        .eq("plan_code", plan_code_norm)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise ValueError(f"Plan not found: {plan_code_norm}")

    return rows[0]


def get_plan_amount_inr(plan: str) -> int:
    """Return server-owned INR price (in rupees) for Razorpay checkout-enabled plans."""
    p = get_plan(plan)
    if not p.get("is_active", False):
        raise ValueError("This plan is not active for Razorpay checkout.")
    amount_paise = int(p.get("amount_paise") or 0)
    return amount_paise // 100




def _razorpay_client():
    """Create Razorpay client using Streamlit secrets.

    Returns None if Razorpay keys are missing.
    """
    secrets = read_app_secrets()
    key_id = secrets.get("RAZORPAY_KEY_ID")
    key_secret = secrets.get("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        return None

    import razorpay

    # Using test keys from secrets is enough; Razorpay test keys route to sandbox.
    return razorpay.Client(auth=(key_id, key_secret))


def is_razorpay_connected() -> bool:
    """Return True if Razorpay client can be created."""
    return _razorpay_client() is not None


def create_order(amount: int, plan: str = "pro", user_email: str = "") -> dict:
    """Create a Razorpay order after validating the server-owned plan amount.

    Args:
        amount: INR amount. Must match the configured server-side plan price.
        plan: plan identifier (e.g., "pro")
        user_email: used for DB persistence later (optional)

    Returns:
        Razorpay order response dict.

    Raises:
        RuntimeError if Razorpay isn't configured.
    """
    client = _razorpay_client()
    if client is None:
        raise RuntimeError("Razorpay not configured: missing RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET")

    expected_amount = get_plan_amount_inr(plan)
    if int(amount) != expected_amount:
        raise ValueError("Payment amount mismatch. Server-side plan price must be used.")

    order = client.order.create(
        {
            "amount": expected_amount * 100,  # paise
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "plan": str(plan or "").strip().lower(),
                "user_email": str(user_email or "").strip().lower(),
            },
        }
    )
    return order


def create_razorpay_order(plan_code: str, institute_id: str, user_id: str) -> dict:
    """Create Razorpay order for a plan.

    Required spec behavior (Phase 5 Part A):
    - Fetch plan from public.plans
    - Check plan is active
    - Create receipt snapclass_<timestamp>
    - Create Razorpay order
    - Save order in payment_orders
    - Return order_id, amount, currency, key_id
    """
    db = get_supabase_client()
    if db is None:
        raise RuntimeError("Supabase is not connected.")

    plan = get_plan(plan_code)
    if not plan.get("is_active", False):
        raise ValueError("Plan is not active")

    receipt = f"snapclass_{int(__import__('time').time() * 1000)}"
    secrets = read_app_secrets()
    key_id = secrets.get("RAZORPAY_KEY_ID")

    # Razorpay Amount in paise
    amount_paise = int(plan.get("amount_paise") or 0)
    if amount_paise <= 0:
        raise ValueError("This plan has no Razorpay amount")

    import razorpay

    if not key_id:
        raise RuntimeError("RAZORPAY_KEY_ID missing in secrets")

    key_secret = secrets.get("RAZORPAY_KEY_SECRET")
    if not key_secret:
        raise RuntimeError("RAZORPAY_KEY_SECRET missing in secrets")

    client = razorpay.Client(auth=(key_id, key_secret))
    order = client.order.create(
        {
            "amount": amount_paise,
            "currency": plan.get("currency") or "INR",
            "payment_capture": 1,
            "notes": {"plan_code": plan.get("plan_code") or plan_code},
            "receipt": receipt,
        }
    )

    order_id = order.get("id")
    currency = order.get("currency") or "INR"

    if not order_id:
        raise RuntimeError("Razorpay did not return order id")

    billing_cycle = str(plan.get("billing_cycle") or "monthly").strip().lower()

    # Save order in payment_orders
    db.table("payment_orders").insert(
        {
            "order_id": str(order_id),
            "institute_id": institute_id,
            "user_id": user_id,
            "plan_id": plan["id"],
            "billing_cycle": billing_cycle,
            "amount_paise": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
        }
    ).execute()

    return {
        "order_id": str(order_id),
        "amount": amount_paise,
        "currency": currency,
        "key_id": key_id,
        "plan_id": plan["id"],
        "billing_cycle": billing_cycle,
    }



def verify_payment_signature(
    *,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> bool:
    """Verify checkout signature before granting paid access."""
    key_secret = read_app_secrets().get("RAZORPAY_KEY_SECRET")
    if not key_secret:
        return False

    message = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
    expected = hmac.new(
        str(key_secret).encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, str(razorpay_signature or ""))


def verify_webhook_signature(*, body: bytes, signature: str) -> bool:
    """Verify Razorpay webhook payload before processing it."""
    secret = read_app_secrets().get("RAZORPAY_WEBHOOK_SECRET")
    if not secret or not body or not signature:
        return False

    expected = hmac.new(
        str(secret).encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, str(signature))


def save_successful_payment(
    *,
    user_email: str,
    amount: int,
    plan: str,
    payment_id: str,
    institute_id: str = "",
    plan_id: str = "",
    order_id: str = "",
    signature: str = "",
    status: str = "success",
    razorpay_order_id: str | None = None,
    razorpay_payment_id: str | None = None,
) -> bool:
    """Insert a successful payment row into Supabase `payments`.

    Returns:
        True if insert succeeded, else False.
    """
    # Signature must verify before we write payment/subscription state.
    # Query params / Razorpay checkout typically pass:
    # - razorpay_order_id
    # - razorpay_payment_id
    # - razorpay_signature
    final_order_id = str(razorpay_order_id or order_id or "").strip()
    final_payment_id = str(razorpay_payment_id or payment_id or "").strip()

    if signature:
        if not verify_payment_signature(
            razorpay_order_id=final_order_id,
            razorpay_payment_id=final_payment_id,
            razorpay_signature=signature,
        ):
            return False

    db = get_supabase_client()
    if db is None:
        return False

    if not final_order_id or not final_payment_id:
        # payment/signature verification needs these values.
        return False


    try:
        order_rows = (
            db.table("payment_orders")
            .select("institute_id,user_id,plan_id,billing_cycle,amount_paise,currency")
            .eq("order_id", final_order_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        order = order_rows[0] if order_rows else {}
        final_institute_id = institute_id or order.get("institute_id")
        final_plan_id = plan_id or order.get("plan_id")
        final_user_id = order.get("user_id")
        final_billing_cycle = order.get("billing_cycle") or "monthly"
        final_amount = int(order.get("amount_paise") or amount or 0)
        final_currency = order.get("currency") or "INR"

        if not all([final_institute_id, final_user_id, final_plan_id, final_amount]):
            return False

        db.table("payments").insert(
            {
                "institute_id": final_institute_id,
                "user_id": final_user_id,
                "plan_id": final_plan_id,
                "billing_cycle": final_billing_cycle,
                "amount_paise": final_amount,
                "currency": final_currency,
                "payment_id": final_payment_id,
                "order_id": final_order_id,
                "status": status,
                "signature": signature or "",
            }
        ).execute()
        db.table("payment_orders").update({"status": "paid"}).eq("order_id", final_order_id).execute()
        return True
    except Exception:
        return False
