"""Payment success page.

Phase 5 Part A (Razorpay test flow):
- Verify Razorpay checkout signature
- Insert payments row after signature verification
- Activate subscription (status='active')

UI theme/sidebar/chatbot/attendance are intentionally untouched.
"""

from __future__ import annotations

import streamlit as st

from src.database.client import get_supabase_client
from src.services.payment_service import save_successful_payment, verify_payment_signature
from src.services.subscription_service import activate_subscription


def show_payment_success() -> None:
    st.title("✅ Payment Successful")
    st.caption("Verifying payment and activating your subscription...")

    q = st.query_params
    razorpay_order_id = (q.get("razorpay_order_id") or q.get("order_id") or "").strip()
    razorpay_payment_id = (q.get("razorpay_payment_id") or q.get("payment_id") or "").strip()
    razorpay_signature = (q.get("razorpay_signature") or q.get("signature") or "").strip()

    institute_id = st.session_state.get("institute_id")
    user_id = st.session_state.get("user_id") or st.session_state.get("auth_user_id")

    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        st.info("Missing Razorpay redirect parameters. Open this page from Razorpay checkout after payment.")
        return

    if not institute_id or not user_id:
        st.warning("Missing institute/user context. Please login again and try payment.")
        return

    plan_code = (q.get("plan_code") or st.session_state.get("selected_plan") or "").strip().lower()

    # Signature verification
    ok = verify_payment_signature(
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
    )

    if not ok:
        st.error("Payment signature verification failed. Subscription will NOT be activated.")
        st.session_state.page = "payment_failed"
        st.rerun()

    # Save payment row
    amount = int((q.get("amount") or "0").strip() or "0")
    currency = (q.get("currency") or "INR").strip().upper()

    # payment_service.save_successful_payment expects amount in paise per schema.
    payment_saved = save_successful_payment(
        user_email=str(st.session_state.get("user_email") or st.session_state.get("auth_user_email") or ""),
        amount=amount,
        plan=plan_code,
        payment_id=razorpay_payment_id,
        institute_id=str(institute_id),
        plan_id="",
        order_id=razorpay_order_id,
        signature=razorpay_signature,
        status="success",
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
    )

    if not payment_saved:
        st.error("Failed to insert payments row after verification. Subscription will NOT be activated.")
        st.session_state.page = "payment_failed"
        st.rerun()

    # Activate subscription row
    # plan_id comes from public.plans table; subscription_service.activate_subscription needs it.
    # Here we pass plan_id from query/state if present; otherwise activate_subscription can still work
    # if caller provides correct plan_id in your Phase 5 wiring.
    plan_id = (q.get("plan_id") or st.session_state.get("plan_id") or "").strip()
    billing_cycle = "monthly"
    if not plan_id:
        db = get_supabase_client()
        if db:
            try:
                rows = (
                    db.table("payment_orders")
                    .select("plan_id,billing_cycle")
                    .eq("order_id", razorpay_order_id)
                    .limit(1)
                    .execute()
                    .data
                    or []
                )
                if rows:
                    plan_id = str(rows[0].get("plan_id") or "")
                    billing_cycle = str(rows[0].get("billing_cycle") or "monthly")
            except Exception:
                pass

    subscribed = False
    if plan_id:
        subscribed = activate_subscription(
            institute_id=str(institute_id),
            plan_id=plan_id,
            billing_cycle=billing_cycle,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
        )

    if not subscribed:
        # Fallback: mark as failed if we cannot activate subscription deterministically.
        st.error("Failed to activate subscription. Missing plan_id for subscription activation.")
        st.session_state.page = "payment_failed"
        st.rerun()

    st.success("Payment verified and subscription activated successfully.")
    st.session_state.page = "admin_billing"
    st.rerun()


