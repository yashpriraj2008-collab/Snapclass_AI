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
import os


from src.database.client import get_supabase_client

from src.utils.config import get_config


# Phase 5 integrates with DB-backed `public.plans`.



def _parse_price(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return int(digits) if digits else 0


def clean_phone(phone: str) -> str:
    """Return the last 10 digits of an Indian mobile number."""
    digits = "".join(ch for ch in str(phone or "").strip() if ch.isdigit())
    if digits.startswith("91") and len(digits) > 10:
        digits = digits[-10:]
    return digits[-10:]


def _validate_indian_mobile(phone: str) -> str:
    cleaned = clean_phone(phone)
    if len(cleaned) != 10 or cleaned[0] not in {"6", "7", "8", "9"}:
        raise ValueError("Invalid Indian mobile number. Update institute admin phone with a real 10-digit number.")
    return cleaned


def _get_payment_customer(db, institute_id: str, user_id: str) -> dict:
    institute: dict = {}
    profile: dict = {}

    try:
        rows = db.table("institutes").select("*").eq("id", institute_id).limit(1).execute().data or []
        institute = rows[0] if rows else {}
    except Exception:
        institute = {}

    try:
        rows = db.table("user_profiles").select("*").eq("user_id", user_id).limit(1).execute().data or []
        if not rows:
            rows = db.table("user_profiles").select("*").eq("id", user_id).limit(1).execute().data or []
        profile = rows[0] if rows else {}
    except Exception:
        profile = {}

    name = (
        institute.get("admin_name")
        or profile.get("full_name")
        or institute.get("name")
        or "SnapClass Admin"
    )
    email = institute.get("admin_email") or profile.get("email") or ""
    phone = (
        institute.get("admin_phone")
        or profile.get("phone")
        or profile.get("admin_phone")
        or ""
    )
    return {
        "name": str(name or "").strip(),
        "email": str(email or "").strip().lower(),
        "contact": _validate_indian_mobile(str(phone or "")),
    }


def _normalize_plan(plan_code: str, row: dict) -> dict:
    plan_code_norm = str((row or {}).get("plan_code") or plan_code or "demo").strip().lower()
    fallback_prices = {"demo": 0, "starter": 499, "pro": 999, "enterprise": 4999}
    price = (
        _parse_price((row or {}).get("price_monthly"))
        or _parse_price((row or {}).get("price_display"))
        or _parse_price((row or {}).get("price"))
        or (_parse_price((row or {}).get("amount_paise")) // 100)
        or fallback_prices.get(plan_code_norm, 0)
    )
    if plan_code_norm == "pro":
        price = 999
    out = dict(row or {})
    out["plan_code"] = plan_code_norm
    out["billing_cycle"] = str(out.get("billing_cycle") or "monthly").strip().lower()
    out["currency"] = str(out.get("currency") or "INR").strip().upper()
    out["amount_paise"] = _parse_price(out.get("amount_paise")) or price * 100
    out["is_active"] = bool(out.get("is_active", True))
    return out


def get_plan(plan_code: str) -> dict:
    """Fetch a plan from public.plans by plan_code."""
    db = get_supabase_client()
    if db is None:
        raise RuntimeError("Supabase is not connected.")

    plan_code_norm = str(plan_code or "").strip().lower()
    if not plan_code_norm:
        raise ValueError("plan_code is required")

    res = db.table("plans").select("*").eq("plan_code", plan_code_norm).limit(1).execute()
    rows = res.data or []
    if not rows:
        raise ValueError(f"Plan not found: {plan_code_norm}")

    return _normalize_plan(plan_code_norm, rows[0])


def get_plan_amount_inr(plan: str) -> int:
    """Return server-owned INR price (in rupees) for Razorpay checkout-enabled plans."""
    p = get_plan(plan)
    if not p.get("is_active", False):
        raise ValueError("This plan is not active for Razorpay checkout.")
    amount_paise = int(p.get("amount_paise") or 0)
    return amount_paise // 100




def _razorpay_client():
    """Create Razorpay client.

    Uses Render environment variables first, then local st.secrets.

    Returns None if Razorpay keys are missing.
    """
    key_id = get_config("RAZORPAY_KEY_ID", "")
    key_secret = get_config("RAZORPAY_KEY_SECRET", "")
    if not key_id or not key_secret:
        return None


    import razorpay

    # Using test keys from secrets is enough; Razorpay test keys route to sandbox.
    return razorpay.Client(auth=(key_id, key_secret))


def is_razorpay_connected() -> bool:
    """Return True if Razorpay client can be created."""
    return _razorpay_client() is not None


def _unsupported_columns_from_error(error: Exception, payload: dict) -> list[str]:
    raw = str(error).lower()
    return [
        column
        for column in payload
        if column.lower() in raw
        and (
            "column" in raw
            or "schema cache" in raw
            or "could not find" in raw
            or "pgrst204" in raw
            or "42703" in raw
        )
    ]


def _insert_with_supported_columns(table: str, payload: dict) -> None:
    db = get_supabase_client()
    if db is None:
        raise RuntimeError("Supabase is not connected.")
    write_payload = dict(payload)
    last_error: Exception | None = None
    for _attempt in range(len(payload) + 1):
        try:
            db.table(table).insert(write_payload).execute()
            return
        except Exception as exc:
            last_error = exc
            unsupported = _unsupported_columns_from_error(exc, write_payload)
            if not unsupported:
                raise
            for column in unsupported:
                write_payload.pop(column, None)
    if last_error:
        raise last_error


def _update_with_supported_columns(table: str, filters: dict, payload: dict) -> None:
    db = get_supabase_client()
    if db is None:
        raise RuntimeError("Supabase is not connected.")
    write_payload = dict(payload)
    last_error: Exception | None = None
    for _attempt in range(len(payload) + 1):
        try:
            query = db.table(table).update(write_payload)
            for key, value in filters.items():
                query = query.eq(key, value)
            query.execute()
            return
        except Exception as exc:
            last_error = exc
            unsupported = _unsupported_columns_from_error(exc, write_payload)
            if not unsupported:
                raise
            for column in unsupported:
                write_payload.pop(column, None)
    if last_error:
        raise last_error


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


def create_razorpay_payment_link(plan_code: str, institute_id: str, user_id: str) -> dict:
    """Create a Razorpay Payment Link for a plan.

    Streamlit MVP note: Payment Links are more reliable than embedded checkout.

    Returns:
      {"ok": True, "payment_link_id": ..., "payment_link_url": ..., "razorpay_order_id": ..., ...}
      or {"ok": False, "error": str}
    """
    db = get_supabase_client()
    if db is None:
        raise RuntimeError("Supabase is not connected.")

    try:
        plan = get_plan(plan_code)
        if not plan.get("is_active", False):
            raise ValueError("Plan is not active")

        client = _razorpay_client()
        if client is None:
            raise RuntimeError("Razorpay not configured: missing keys")

        amount_paise = int(plan.get("amount_paise") or 0)
        if amount_paise <= 0:
            raise ValueError("This plan has no Razorpay amount")

        billing_cycle = str(plan.get("billing_cycle") or "monthly").strip().lower()
        currency = str(plan.get("currency") or "INR").strip().upper()
        app_base_url = get_config("APP_BASE_URL", "") or os.getenv("APP_BASE_URL") or "http://localhost:8507"
        callback_url = f"{app_base_url}/?payment_return=1&institute_id={institute_id}"
        plan_name = str(plan.get("display_name") or plan.get("plan_code") or plan_code).strip()
        customer = _get_payment_customer(db, str(institute_id), str(user_id))
        receipt = f"snapclass_{int(__import__('time').time() * 1000)}"

        # Razorpay Payment Link creation
        payment_link = client.payment_link.create(
            {
                "amount": amount_paise,
                "currency": currency,
                "accept_partial": False,
                "description": f"SnapClass AI {plan_name} Plan",
                "reference_id": receipt,
                "customer": customer,
                "notify": {"sms": False, "email": False},
                "reminder_enable": False,
                "notes": {
                    "institute_id": str(institute_id),
                    "plan_code": str(plan_code),
                    "plan_name": plan_name,
                    "user_id": str(user_id),
                },
                "callback_url": callback_url,
                "callback_method": "get",
            }
        )

        payment_link_id = str(payment_link.get("id") or "").strip()
        payment_link_url = str(payment_link.get("short_url") or payment_link.get("url") or "").strip()

        if not payment_link_id or not payment_link_url:
            raise RuntimeError("Razorpay did not return payment link id/url")

        _insert_with_supported_columns(
            "payment_orders",
            {
                "institute_id": institute_id,
                "user_id": user_id,
                "plan_id": plan["id"],
                "plan_name": plan_name,
                "billing_cycle": billing_cycle,
                "amount_paise": amount_paise,
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt,
                "status": "pending",
                "razorpay_payment_link_id": payment_link_id,
                "razorpay_payment_link_url": payment_link_url,
            },
        )

        return {
            "ok": True,
            "payment_link_id": payment_link_id,
            "payment_link_url": payment_link_url,
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}


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
    key_id = get_config("RAZORPAY_KEY_ID", "")

    # Razorpay Amount in paise
    amount_paise = int(plan.get("amount_paise") or 0)

    if amount_paise <= 0:
        raise ValueError("This plan has no Razorpay amount")

    import razorpay

    if not key_id:
        raise RuntimeError("RAZORPAY_KEY_ID missing in secrets")

    key_secret = get_config("RAZORPAY_KEY_SECRET", "")

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

    _insert_with_supported_columns(
        "payment_orders",
        {
            "order_id": str(order_id),
            "institute_id": institute_id,
            "user_id": user_id,
            "plan_id": plan["id"],
            "billing_cycle": billing_cycle,
            "amount_paise": amount_paise,
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
        },
    )

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
    key_secret = get_config("RAZORPAY_KEY_SECRET", "")
    if not key_secret:
        return False


    message = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
    expected = hmac.new(
        str(key_secret).encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, str(razorpay_signature or ""))


def verify_payment_link_signature(
    *,
    payment_link_id: str,
    payment_link_reference_id: str,
    payment_link_status: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> bool:
    """Verify a Razorpay Payment Link callback signature."""
    key_secret = get_config("RAZORPAY_KEY_SECRET", "")
    values = (

        payment_link_id,
        payment_link_reference_id,
        payment_link_status,
        razorpay_payment_id,
        razorpay_signature,
    )
    if not key_secret or not all(str(value or "").strip() for value in values):
        return False

    message = "|".join(
        [
            str(payment_link_id).strip(),
            str(payment_link_reference_id).strip(),
            str(payment_link_status).strip(),
            str(razorpay_payment_id).strip(),
        ]
    ).encode("utf-8")
    expected = hmac.new(
        str(key_secret).encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, str(razorpay_signature or "").strip())


def verify_webhook_signature(*, body: bytes, signature: str) -> bool:
    """Verify Razorpay webhook payload before processing it."""
    secret = get_config("RAZORPAY_WEBHOOK_SECRET", "")

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
    payment_link_id: str = "",
    payment_link_reference_id: str = "",
    payment_link_status: str = "",
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
    final_payment_link_id = str(payment_link_id or "").strip()

    if final_payment_link_id:
        if str(payment_link_status or "").strip().lower() != "paid":
            return False
        if not verify_payment_link_signature(
            payment_link_id=final_payment_link_id,
            payment_link_reference_id=payment_link_reference_id,
            payment_link_status=payment_link_status,
            razorpay_payment_id=final_payment_id,
            razorpay_signature=signature,
        ):
            return False
    elif not signature or not verify_payment_signature(
            razorpay_order_id=final_order_id,
            razorpay_payment_id=final_payment_id,
            razorpay_signature=signature,
    ):
        return False

    db = get_supabase_client()
    if db is None:
        return False

    if not (final_order_id or final_payment_link_id) or not final_payment_id:
        # payment/signature verification needs these values.
        return False


    try:
        order_query = db.table("payment_orders").select("*")
        if final_payment_link_id:
            order_query = order_query.eq("razorpay_payment_link_id", final_payment_link_id)
        else:
            order_query = order_query.eq("order_id", final_order_id)
        order_rows = order_query.limit(1).execute().data or []
        order = order_rows[0] if order_rows else {}
        if not order:
            return False
        if final_payment_link_id and str(order.get("receipt") or "") != str(payment_link_reference_id or ""):
            return False
        if institute_id and str(order.get("institute_id") or "") != str(institute_id):
            return False
        final_institute_id = institute_id or order.get("institute_id")
        final_plan_id = plan_id or order.get("plan_id")
        final_user_id = order.get("user_id")
        final_billing_cycle = order.get("billing_cycle") or "monthly"
        final_amount = int(order.get("amount_paise") or order.get("amount") or amount or 0)
        final_currency = order.get("currency") or "INR"

        if not all([final_institute_id, final_user_id, final_plan_id, final_amount]):
            return False

        _insert_with_supported_columns(
            "payments",
            {
                "institute_id": final_institute_id,
                "user_id": final_user_id,
                "plan_id": final_plan_id,
                "billing_cycle": final_billing_cycle,
                "amount_paise": final_amount,
                "currency": final_currency,
                "payment_id": final_payment_id,
                "order_id": final_order_id or final_payment_link_id,
                "razorpay_payment_link_id": final_payment_link_id or None,
                "status": status,
                "signature": signature or "",
            },
        )
        order_filter = (
            {"razorpay_payment_link_id": final_payment_link_id}
            if final_payment_link_id
            else {"order_id": final_order_id}
        )
        _update_with_supported_columns(
            "payment_orders",
            order_filter,
            {
                "status": "paid",
                "razorpay_payment_id": final_payment_id,
                "razorpay_signature": signature or "",
            },
        )
        return True
    except Exception:
        return False
