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
from src.services.payment_service import (
    save_successful_payment,
    verify_payment_link_signature,
    verify_payment_signature,
)
from src.services.subscription_service import activate_subscription


def show_payment_success() -> None:
    st.title("✅ Payment Successful")
    st.caption("Verifying payment and activating your subscription...")

    q = st.query_params
    razorpay_order_id = (q.get("razorpay_order_id") or q.get("order_id") or "").strip()
    razorpay_payment_id = (q.get("razorpay_payment_id") or q.get("payment_id") or "").strip()
    razorpay_signature = (q.get("razorpay_signature") or q.get("signature") or "").strip()
    payment_link_id = (q.get("razorpay_payment_link_id") or "").strip()
    payment_link_reference_id = (q.get("razorpay_payment_link_reference_id") or "").strip()
    payment_link_status = (q.get("razorpay_payment_link_status") or "").strip().lower()

    # Strictly ensure all required values exist before activation.
    institute_id = st.session_state.get("institute_id")
    user_id = st.session_state.get("user_id") or st.session_state.get("auth_user_id")

    # Hard fail if any required verification parameters are missing.
    # This prevents accidental unlock just by visiting the page.
    is_payment_link = bool(payment_link_id)
    callback_fields = (
        [payment_link_id, payment_link_reference_id, payment_link_status]
        if is_payment_link
        else [razorpay_order_id]
    )
    if not all([institute_id, user_id, razorpay_payment_id, razorpay_signature, *callback_fields]):
        st.error(
            "Payment verification failed. Please complete payment through Razorpay checkout again."
        )
        st.stop()

    if is_payment_link:
        ok = payment_link_status == "paid" and verify_payment_link_signature(
            payment_link_id=payment_link_id,
            payment_link_reference_id=payment_link_reference_id,
            payment_link_status=payment_link_status,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
        )
    else:
        ok = verify_payment_signature(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
        )

    if not ok:
        st.error("Payment signature verification failed. Subscription will NOT be activated.")
        st.session_state.page = "payment_failed"
        st.rerun()

    db = get_supabase_client()
    order_rows = []
    if db:
        try:
            order_query = db.table("payment_orders").select("*")
            if is_payment_link:
                order_query = order_query.eq("razorpay_payment_link_id", payment_link_id)
            else:
                order_query = order_query.eq("order_id", razorpay_order_id)
            order_rows = order_query.limit(1).execute().data or []
        except Exception:
            order_rows = []
    order = order_rows[0] if order_rows else {}
    if (
        not order
        or str(order.get("institute_id") or "") != str(institute_id)
        or str(order.get("user_id") or "") != str(user_id)
        or (
            is_payment_link
            and str(order.get("receipt") or "") != payment_link_reference_id
        )
    ):
        st.error("Payment does not match the signed-in institute account. Subscription will NOT be activated.")
        st.stop()

    plan_id = str(order.get("plan_id") or "").strip()
    plan = {}
    if db and plan_id:
        try:
            plan_rows = db.table("plans").select("*").eq("id", plan_id).limit(1).execute().data or []
            plan = plan_rows[0] if plan_rows else {}
        except Exception:
            plan = {}
    plan_code = str(plan.get("plan_code") or "").strip().lower()
    plan_name = str(
        plan.get("display_name")
        or plan.get("name")
        or order.get("plan_name")
        or plan_code
    ).strip()
    amount = int(order.get("amount_paise") or order.get("amount") or 0)
    billing_cycle = str(order.get("billing_cycle") or "monthly").strip().lower()
    if not plan_id or not plan_name or amount <= 0:
        st.error("Stored payment order is incomplete. Subscription will NOT be activated.")
        st.stop()

    # payment_service.save_successful_payment expects amount in paise per schema.
    payment_saved = save_successful_payment(
        user_email=str(st.session_state.get("user_email") or st.session_state.get("auth_user_email") or ""),
        amount=amount,
        plan=plan_code,
        payment_id=razorpay_payment_id,
        institute_id=str(institute_id),
        plan_id=plan_id,
        order_id=razorpay_order_id,
        signature=razorpay_signature,
        status="success",
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        payment_link_id=payment_link_id,
        payment_link_reference_id=payment_link_reference_id,
        payment_link_status=payment_link_status,
    )

    if not payment_saved:
        st.error("Failed to insert payments row after verification. Subscription will NOT be activated.")
        st.session_state.page = "payment_failed"
        st.rerun()

    # Activate subscription row
    # plan_id comes from public.plans table; subscription_service.activate_subscription needs it.
    # Here we pass plan_id from query/state if present; otherwise activate_subscription can still work
    # if caller provides correct plan_id in your Phase 5 wiring.
    subscribed = activate_subscription(
        institute_id=str(institute_id),
        plan_id=plan_id,
        plan_name=plan_name,
        billing_cycle=billing_cycle,
        razorpay_order_id=razorpay_order_id or payment_link_id,
        razorpay_payment_id=razorpay_payment_id,
        payment_link_id=payment_link_id,
    )

    if not subscribed:
        # Fallback: mark as failed if we cannot activate subscription deterministically.
        st.error("Failed to activate subscription. Missing plan_id for subscription activation.")
        st.session_state.page = "payment_failed"
        st.rerun()

    st.success("Payment verified and subscription activated successfully.")
    st.session_state.subscription_status = "active"
    if isinstance(st.session_state.get("current_institute"), dict):
        st.session_state.current_institute["subscription_status"] = "active"
    institute = st.session_state.get("current_institute")
    institute_name = (
        institute.get("name")
        if isinstance(institute, dict)
        else st.session_state.get("active_institute_name")
    )
    st.session_state["subscription_activation_popup"] = {
        "plan_name": plan_name,
        "institute_name": institute_name or "Your institute",
        "amount_text": f"INR {amount / 100:,.0f}",
        "payment_id": razorpay_payment_id,
    }
    st.query_params.clear()
    st.session_state.page = "institute_dashboard"
    st.session_state.institute_page = "institute_dashboard"
    st.rerun()


