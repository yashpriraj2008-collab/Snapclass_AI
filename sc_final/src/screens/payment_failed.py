"""Payment failed page.

Phase 5 Part A (Streamlit-only demo):
- This page should mark the payment/order as failed (no subscription activation).
- For now, it provides wiring hooks; full DB integration will be completed
  after Phase 5 services are aligned.
"""

from __future__ import annotations

import streamlit as st


def show_payment_failed() -> None:
    st.title("❌ Payment Failed")
    st.caption("Your payment was not completed. No subscription was activated.")

    q = st.query_params
    order_id = q.get("razorpay_order_id") or q.get("order_id") or ""
    payment_id = q.get("razorpay_payment_id") or q.get("payment_id") or ""
    reason = q.get("reason") or q.get("message") or ""

    if order_id or payment_id:
        st.info(f"Order: {order_id or '—'}\nPayment: {payment_id or '—'}")
    if reason:
        st.write(f"Reason: {reason}")

    st.warning("No plan changes were made. You can try again from Pricing.")

    if st.button("Go to Pricing", key="to_pricing_from_failed"):
        st.session_state.page = "pricing"
        st.rerun()

