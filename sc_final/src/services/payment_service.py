"""Razorpay payment service (TEST MODE only).

Adds:
- Razorpay client from Streamlit secrets
- create_order() for INR plan payments
- save_successful_payment() into Supabase `payments` table

IMPORTANT:
- Uses ONLY RAZORPAY_* TEST keys from .streamlit/secrets.toml
- No live keys / no production endpoints.
"""

from __future__ import annotations

import streamlit as st

from src.database.client import get_supabase_client




def _razorpay_client():
    """Create Razorpay client using Streamlit secrets.

    Returns None if Razorpay keys are missing.
    """
    key_id = st.secrets.get("RAZORPAY_KEY_ID")
    key_secret = st.secrets.get("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        return None

    import razorpay

    # Using test keys from secrets is enough; Razorpay test keys route to sandbox.
    return razorpay.Client(auth=(key_id, key_secret))


def is_razorpay_connected() -> bool:
    """Return True if Razorpay client can be created."""
    return _razorpay_client() is not None


def create_order(amount: int, plan: str = "pro", user_email: str = "") -> dict:
    """Create a Razorpay order for the given INR amount.

    Args:
        amount: INR amount (e.g., 499)
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

    order = client.order.create(
        {
            "amount": int(amount) * 100,  # paise
            "currency": "INR",
            "payment_capture": 1,
        }
    )
    return order


def save_successful_payment(
    *,
    user_email: str,
    amount: int,
    plan: str,
    payment_id: str,
    status: str = "success",
) -> bool:
    """Insert a successful payment row into Supabase `payments`.

    Returns:
        True if insert succeeded, else False.
    """
    db = get_supabase_client()
    if db is None:
        return False

    try:
        # Expected schema (create in Supabase SQL editor):
        # create table payments (
        #   id uuid default gen_random_uuid() primary key,
        #   user_email text,
        #   amount integer,
        #   plan text,
        #   payment_id text,
        #   status text,
        #   created_at timestamp default now()
        # );
        db.table("payments").insert(
            {
                "user_email": user_email or "",
                "amount": int(amount),
                "plan": plan,
                "payment_id": payment_id,
                "status": status,
            }
        ).execute()
        return True
    except Exception:
        return False

