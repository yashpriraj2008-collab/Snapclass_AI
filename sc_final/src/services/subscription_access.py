"""Subscription access helpers for admin portal gating."""
from __future__ import annotations

import datetime as dt
import html
import json
import os
from textwrap import dedent
from typing import Any
from urllib.parse import urlparse

import streamlit as st  # type: ignore[import]

from src.database.client import read_app_secrets
from src.services.admin_context import get_current_institute_id
from src.services.institute_service import _db, update_institute
from src.services.payment_service import (
    clean_phone,
    create_razorpay_payment_link,
    is_razorpay_connected,
)
from src.services.subscription_service import activate_subscription
from src.utils.user_guards import show_payment_not_configured


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _is_development() -> bool:
    env = str(os.getenv("APP_ENV") or read_app_secrets().get("APP_ENV") or "").strip().lower()
    return env == "development"


def _query_one(table: str, column: str, value: str) -> dict[str, Any]:
    db = _db()
    if not db or not value:
        return {}
    try:
        rows = db.table(table).select("*").eq(column, value).limit(1).execute().data or []
        return rows[0] if rows else {}
    except Exception:
        return {}


def get_current_subscription(institute_id: str | None = None) -> dict[str, Any]:
    """Return the current subscription row for the selected institute."""
    institute_id = str(
        institute_id
        or get_current_institute_id()
        or st.session_state.get("institute_id")
        or ""
    ).strip()
    return _query_one("subscriptions", "institute_id", institute_id)


def get_latest_payment_order(institute_id: str | None = None) -> dict[str, Any]:
    """Return the newest payment order for diagnostics and development testing."""
    institute_id = str(
        institute_id
        or get_current_institute_id()
        or st.session_state.get("institute_id")
        or ""
    ).strip()
    db = _db()
    if not db or not institute_id:
        return {}
    try:
        rows = (
            db.table("payment_orders")
            .select("*")
            .eq("institute_id", institute_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else {}
    except Exception:
        return {}


def _plan_by_id(plan_id: str) -> dict[str, Any]:
    return _query_one("plans", "id", str(plan_id or "").strip())


def _plan_by_code(plan_code: str) -> dict[str, Any]:
    return _query_one("plans", "plan_code", _norm(plan_code))


def _plan_code(institute: dict[str, Any] | None, subscription: dict[str, Any] | None) -> str:
    institute = institute or {}
    subscription = subscription or {}
    plan = _plan_by_id(str(subscription.get("plan_id") or ""))
    return _norm(
        plan.get("plan_code")
        or subscription.get("plan_code")
        or st.session_state.get("selected_plan_code")
        or institute.get("plan")
        or "pro"
    )


def _plan_label(institute: dict[str, Any] | None, subscription: dict[str, Any] | None) -> str:
    code = _plan_code(institute, subscription)
    plan = _plan_by_id(str((subscription or {}).get("plan_id") or "")) or _plan_by_code(code)
    name = plan.get("display_name") or plan.get("name") or code.replace("_", " ").title()
    text = str(name or "Selected").strip()
    return text if text.lower().endswith("plan") else f"{text} Plan"


def _status_label(status: str) -> str:
    labels = {
        "active": "Active",
        "demo": "Active",
        "pending": "Payment Pending",
        "pending_payment": "Payment Pending",
        "payment_pending": "Payment Pending",
        "expired": "Expired",
        "cancelled": "Cancelled",
    }
    value = _norm(status)
    return labels.get(value, value.replace("_", " ").title() if value else "Unknown")


def _inject_payment_page_css() -> None:
    st.markdown(
        dedent(
            """
        <style>
        .snap-payment-hero {
          padding: 26px;
          margin: 12px 0 18px;
          border: 1px solid #e0e7ff;
          border-radius: 22px;
          background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 55%, #fdf2f8 100%);
          box-shadow: 0 18px 45px rgba(79, 70, 229, 0.10);
        }
        .snap-payment-eyebrow {
          color: #4f46e5;
          font-size: 13px;
          font-weight: 800;
          letter-spacing: .08em;
          text-transform: uppercase;
        }
        .snap-payment-title {
          margin: 7px 0 8px;
          color: #111827;
          font-size: 28px;
          line-height: 1.15;
        }
        .snap-payment-copy {
          max-width: 760px;
          margin: 0;
          color: #4b5563;
          font-size: 15px;
          line-height: 1.65;
        }
        .snap-payment-status {
          display: inline-flex;
          margin-top: 16px;
          padding: 7px 12px;
          border-radius: 999px;
          background: #fef3c7;
          color: #92400e;
          font-size: 13px;
          font-weight: 800;
        }
        .snap-payment-step {
          min-height: 132px;
          padding: 18px;
          border: 1px solid #e5e7eb;
          border-radius: 16px;
          background: #ffffff;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        }
        .snap-payment-step-number {
          display: inline-flex;
          width: 30px;
          height: 30px;
          align-items: center;
          justify-content: center;
          border-radius: 9px;
          background: #eef2ff;
          color: #4f46e5;
          font-weight: 900;
        }
        .snap-payment-step h4 {
          margin: 12px 0 5px;
          color: #111827;
        }
        .snap-payment-step p {
          margin: 0;
          color: #6b7280;
          font-size: 13px;
          line-height: 1.5;
        }
        .snap-checkout-ready {
          padding: 20px;
          margin: 16px 0 10px;
          border: 1px solid #bbf7d0;
          border-radius: 18px;
          background: #f0fdf4;
        }
        .snap-checkout-ready h3 {
          margin: 0 0 6px;
          color: #166534;
        }
        .snap-checkout-ready p {
          margin: 0;
          color: #3f6212;
        }
        .snap-lock-card {
          padding: 24px;
          border: 1px solid #e2e8f0;
          border-radius: 20px;
          background: #ffffff;
          box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
        }
        .snap-lock-card h3 {
          margin: 10px 0 6px;
          color: #0f172a;
          font-size: 19px;
        }
        .snap-lock-card p {
          margin: 0;
          color: #64748b;
          font-size: 14px;
          line-height: 1.55;
        }
        .snap-lock-icon {
          display: inline-flex;
          width: 42px;
          height: 42px;
          align-items: center;
          justify-content: center;
          border-radius: 13px;
          background: #eef2ff;
          color: #4f46e5;
          font-weight: 900;
        }
        .snap-billing-summary {
          padding: 22px;
          min-height: 166px;
          border-radius: 20px;
          border: 1px solid #ddd6fe;
          background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);
          box-shadow: 0 18px 42px rgba(79, 70, 229, 0.10);
        }
        .snap-billing-summary .label {
          color: #6d28d9 !important;
          font-size: 12px;
          font-weight: 800;
          letter-spacing: .08em;
          text-transform: uppercase;
        }
        .snap-billing-summary .value {
          margin-top: 7px;
          color: #111827 !important;
          font-size: 24px;
          font-weight: 850;
        }
        .snap-billing-price {
          margin-top: 18px;
          color: #475569 !important;
          font-size: 14px;
          font-weight: 650;
        }
        .snap-billing-status {
          display: inline-flex;
          margin-top: 12px;
          padding: 6px 10px;
          border-radius: 999px;
          background: #fef3c7;
          color: #92400e !important;
          font-size: 12px;
          font-weight: 850;
        }
        .snap-billing-detail {
          padding: 18px;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          background: #ffffff;
        }
        .snap-billing-detail strong {
          display: block;
          margin-bottom: 5px;
          color: #0f172a;
        }
        .snap-billing-detail span {
          color: #64748b;
          font-size: 14px;
        }
        </style>
        """
        ).strip(),
        unsafe_allow_html=True,
    )


def _safe_razorpay_url(value: Any) -> str:
    """Allow only HTTPS checkout links returned by Razorpay."""
    url = str(value or "").strip()
    try:
        parsed = urlparse(url)
    except Exception:
        return ""
    hostname = str(parsed.hostname or "").lower()
    allowed_host = hostname == "rzp.io" or hostname.endswith(".razorpay.com")
    return url if parsed.scheme == "https" and allowed_host else ""


def _render_payment_step(number: int, title: str, description: str) -> None:
    st.markdown(
        dedent(
            f"""
            <div class="snap-payment-step">
              <span class="snap-payment-step-number">{number}</span>
              <h4>{html.escape(title)}</h4>
              <p>{html.escape(description)}</p>
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def _valid_indian_mobile(value: Any) -> bool:
    phone = clean_phone(str(value or ""))
    return len(phone) == 10 and phone[:1] in {"6", "7", "8", "9"}


def _render_payment_contact_form(
    institute: dict[str, Any],
    institute_id: str,
) -> bool:
    """Render a payment contact repair form and return whether checkout can continue."""
    current_phone = str(institute.get("admin_phone") or "").strip()
    if _valid_indian_mobile(current_phone):
        return True

    st.warning(
        "Add a valid Indian mobile number before opening Razorpay checkout. "
        "Use a 10-digit number starting with 6, 7, 8, or 9."
    )
    with st.form("payment_contact_update_form", border=True):
        st.markdown("#### Update payment contact")
        st.caption(
            "This number is saved to your institute profile and used only as the Razorpay contact."
        )
        phone = st.text_input(
            "Admin mobile number",
            value=clean_phone(current_phone),
            placeholder="9876543210",
            max_chars=10,
        )
        submitted = st.form_submit_button(
            "Save mobile number",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return False

    cleaned = clean_phone(phone)
    if not _valid_indian_mobile(cleaned):
        st.error("Enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.")
        return False
    if not institute_id:
        st.error("Institute information is missing. Please log in again.")
        return False

    result = update_institute(institute_id, {"admin_phone": cleaned})
    if not result.get("ok"):
        st.error(result.get("message") or "Mobile number could not be saved.")
        return False

    institute["admin_phone"] = cleaned
    st.session_state.current_institute = institute
    st.success("Mobile number updated. You can now continue to secure payment.")
    st.rerun()
    return True


def is_subscription_active(
    subscription: dict[str, Any] | None = None,
    institute: dict[str, Any] | None = None,
) -> bool:
    institute = institute or {}
    subscription = subscription or {}
    institute_subscription_status = _norm(institute.get("subscription_status"))
    subscription_status = _norm(subscription.get("status"))
    return (
        institute_subscription_status == "active"
        or subscription_status == "active"
    )


def can_access_admin_portal(
    institute: dict[str, Any] | None,
    subscription: dict[str, Any] | None = None,
) -> bool:
    institute = institute or {}
    if subscription is None:
        subscription = get_current_subscription(str(institute.get("id") or ""))
    return is_subscription_active(subscription, institute)


def start_razorpay_payment(plan_code: str, institute_id: str) -> None:
    """Create Razorpay Payment Link and show a link button to open it.

    IMPORTANT: For Streamlit MVP reliability, we avoid embedded Razorpay JS checkout.
    """
    user_id = st.session_state.get("user_id") or st.session_state.get("auth_user_id")
    if not institute_id or not user_id:
        st.warning("Please login again before payment.")
        return

    if not is_razorpay_connected():
        show_payment_not_configured()
        return

    result = create_razorpay_payment_link(
        plan_code=plan_code,
        institute_id=str(institute_id),
        user_id=str(user_id),
    )

    if not result.get("ok"):
        st.error(result.get("error") or "Could not create Razorpay checkout.")
        return

    checkout_url = _safe_razorpay_url(result.get("payment_link_url"))
    if not checkout_url:
        st.error("Razorpay returned an invalid checkout link. Please try again.")
        return

    st.session_state.razorpay_checkout_url = checkout_url
    _inject_payment_page_css()
    st.markdown(
        """
        <div class="snap-checkout-ready">
          <h3>Secure checkout is ready</h3>
          <p>Razorpay will open in a new tab. Keep SnapClass open so you can return after payment.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "Continue to Razorpay",
        checkout_url,
        type="primary",
        use_container_width=True,
    )
    st.caption("Your subscription unlocks only after SnapClass verifies the payment.")
    st.stop()



def mark_subscription_active_dev_only(institute_id: str | None = None) -> tuple[bool, str]:
    """Local development unlock helper. Hidden unless APP_ENV=development."""
    if not _is_development():
        return False, "Dev payment unlock is disabled outside APP_ENV=development."

    institute_id = str(institute_id or get_current_institute_id() or st.session_state.get("institute_id") or "").strip()
    db = _db()
    if not db or not institute_id:
        return False, "Supabase is not configured."

    try:
        institute = _query_one("institutes", "id", institute_id)
        subscription = get_current_subscription(institute_id)
        latest_order = get_latest_payment_order(institute_id)
        plan_code = _plan_code(institute, subscription)
        plan = (
            _plan_by_id(str(subscription.get("plan_id") or latest_order.get("plan_id") or ""))
            or _plan_by_code(plan_code)
        )
        plan_id = str(plan.get("id") or subscription.get("plan_id") or latest_order.get("plan_id") or "")
        plan_name = str(
            plan.get("display_name")
            or plan.get("name")
            or latest_order.get("plan_name")
            or institute.get("plan")
            or plan_code.title()
        ).strip()
        if not plan_id:
            return False, "Selected plan could not be resolved."

        dev_payment_id = str(
            latest_order.get("razorpay_payment_id")
            or f"dev_payment_{int(dt.datetime.now(dt.timezone.utc).timestamp())}"
        )
        ok = activate_subscription(
            institute_id=institute_id,
            plan_id=plan_id,
            plan_name=plan_name,
            billing_cycle=str(
                latest_order.get("billing_cycle")
                or subscription.get("billing_cycle")
                or plan.get("billing_cycle")
                or "monthly"
            ),
            razorpay_order_id=str(
                latest_order.get("order_id")
                or latest_order.get("razorpay_order_id")
                or latest_order.get("razorpay_payment_link_id")
                or ""
            ),
            payment_link_id=str(latest_order.get("razorpay_payment_link_id") or ""),
            razorpay_payment_id=dev_payment_id,
        )
        if not ok:
            return False, "Subscription activation failed. Check the payment schema and diagnostics."

        st.session_state.subscription_status = "active"
        if isinstance(st.session_state.get("current_institute"), dict):
            st.session_state.current_institute["status"] = "active"
            st.session_state.current_institute["subscription_status"] = "active"
        return True, ""
    except Exception as exc:
        return False, str(exc)


def render_admin_context_bar(
    institute: dict[str, Any] | None,
    subscription: dict[str, Any] | None = None,
    payment_pending: bool = False,
) -> None:
    """Render the admin portal context exactly once per admin page."""
    from src.components.ui import render_portal_badge

    institute = institute or {}
    subscription = subscription or {}
    institute_name = (
        institute.get("name")
        or st.session_state.get("active_institute_name")
        or "No institute selected"
    )
    status_source = (
        "pending_payment"
        if payment_pending
        else subscription.get("status") or institute.get("subscription_status") or ""
    )
    render_portal_badge(
        role="Admin",
        institute_name=str(institute_name),
        plan=_plan_label(institute, subscription),
        status=_status_label(str(status_source)),
    )


@st.dialog("Subscription activated", width="small")
def _subscription_activation_dialog(payload: dict[str, Any]) -> None:
    plan_name = str(payload.get("plan_name") or "Selected plan")
    institute_name = str(payload.get("institute_name") or "Your institute")
    amount_text = str(payload.get("amount_text") or "")

    st.success("Payment verified successfully.")
    st.markdown(f"### {html.escape(plan_name)} is now active")
    st.write(
        f"{institute_name} can now access teachers, students, classes, "
        "attendance, analytics, and reports."
    )
    if amount_text:
        st.caption(f"Payment received: {amount_text}")
    if st.button(
        "Open Admin Dashboard",
        type="primary",
        use_container_width=True,
        key="subscription_activation_open_dashboard",
    ):
        st.session_state.pop("subscription_activation_popup", None)
        st.session_state.page = "institute_dashboard"
        st.session_state.institute_page = "institute_dashboard"
        st.rerun()


def render_subscription_activation_popup() -> None:
    """Show the verified-payment success dialog once on the unlocked dashboard."""
    payload = st.session_state.get("subscription_activation_popup")
    if isinstance(payload, dict) and payload:
        _subscription_activation_dialog(payload)


def render_payment_pending_dashboard(
    institute: dict[str, Any] | None,
    subscription: dict[str, Any] | None = None,
) -> None:
    """Backward-compatible entry point for the single locked billing workspace."""
    render_billing_workspace(institute, subscription)


def render_billing_workspace(
    institute: dict[str, Any] | None,
    subscription: dict[str, Any] | None = None,
) -> None:
    """Render the complete subscription and checkout workspace."""
    institute = institute or {}
    subscription = subscription or get_current_subscription(str(institute.get("id") or ""))
    institute_id = str(institute.get("id") or get_current_institute_id() or st.session_state.get("institute_id") or "")
    institute_name = institute.get("name") or st.session_state.get("active_institute_name") or "Institute"
    plan_code = _plan_code(institute, subscription)
    plan_name = _plan_label(institute, subscription)
    plan = _plan_by_id(str(subscription.get("plan_id") or "")) or _plan_by_code(plan_code)
    amount_paise = int(plan.get("amount_paise") or subscription.get("amount_paise") or 0)
    amount_text = f"INR {amount_paise / 100:,.0f}" if amount_paise else "Configured in Razorpay"
    billing_cycle = str(
        plan.get("billing_cycle")
        or subscription.get("billing_cycle")
        or "monthly"
    ).replace("_", " ").title()
    payment_status = _status_label(
        str(subscription.get("payment_status") or subscription.get("status") or "pending")
    )

    _inject_payment_page_css()
    st.markdown("## Billing & Subscription")
    st.caption(f"Manage the subscription and secure payment for {institute_name}.")
    render_admin_context_bar(institute, subscription, payment_pending=True)

    summary, details = st.columns([1, 1.45], gap="large")
    with summary:
        st.markdown(
            f"""
            <div class="snap-billing-summary">
              <div class="label">Selected subscription</div>
              <div class="value">{html.escape(plan_name)}</div>
              <div class="snap-billing-price">{html.escape(amount_text)} / {html.escape(billing_cycle)}</div>
              <div class="snap-billing-status">{html.escape(payment_status)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with details:
        d1, d2 = st.columns(2, gap="medium")
        with d1:
            st.markdown(
                '<div class="snap-billing-detail"><strong>Secure checkout</strong>'
                '<span>Payment is processed by Razorpay. SnapClass does not store card or UPI credentials.</span></div>',
                unsafe_allow_html=True,
            )
        with d2:
            st.markdown(
                '<div class="snap-billing-detail"><strong>Verified activation</strong>'
                '<span>Workspace access unlocks only after server-side payment verification succeeds.</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("### Payment process")
    step_1, step_2, step_3 = st.columns(3, gap="medium")
    with step_1:
        _render_payment_step(1, "Confirm contact", "Review the mobile number used for Razorpay checkout.")
    with step_2:
        _render_payment_step(2, "Pay securely", "Open Razorpay and complete an available payment method.")
    with step_3:
        _render_payment_step(3, "Verify access", "Return to SnapClass while payment activation is verified.")

    st.markdown("### Checkout")
    payment_contact_ready = _render_payment_contact_form(institute, institute_id)
    if payment_contact_ready:
        if st.button(
            f"Pay securely for {plan_name}",
            type="primary",
            use_container_width=True,
            key="payment_gate_pay_now",
        ):
            try:
                start_razorpay_payment(plan_code, institute_id)
            except ValueError as exc:
                st.error(str(exc))
                st.info("Open My Institute from the sidebar to review your admin contact details.")
    st.caption("Secure payment powered by Razorpay. Access remains locked until verification succeeds.")

    if _is_development():
        if st.button("DEV ONLY: Mark Payment Success", use_container_width=True, key="admin_payment_pending_dev_success"):
            ok, error = mark_subscription_active_dev_only(institute_id)
            if ok:
                st.success("Payment marked as successful for local testing.")
                st.session_state.page = "institute_dashboard"
                st.session_state.institute_page = "institute_dashboard"
                st.rerun()
            st.error(error or "Payment could not be marked successful.")

    latest_order = get_latest_payment_order(institute_id)
    with st.expander("Subscription diagnostics", expanded=False):
        st.json(
            {
                "institute_id": institute_id or None,
                "plan": plan_name,
                "institute.subscription_status": institute.get("subscription_status"),
                "subscription.status": subscription.get("status"),
                "latest payment_order.status": latest_order.get("status"),
            }
        )

    st.stop()


def render_payment_pending_page(
    institute: dict[str, Any] | None,
    subscription: dict[str, Any] | None = None,
) -> None:
    """Backward-compatible name for the locked payment gate."""
    render_payment_pending_dashboard(institute, subscription)
