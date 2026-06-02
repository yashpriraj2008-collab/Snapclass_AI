"""Pricing page."""

import streamlit as st

from src.components.navigation import go_to
from src.components.public_nav import render_public_nav
from src.database.client import read_app_secrets
from src.services.payment_service import create_razorpay_order, get_plan, is_razorpay_connected
from src.utils.user_guards import show_payment_not_configured


def go_to_plan(plan_code: str, plan_name: str | None = None) -> None:
    plan_code_norm = (plan_code or "").strip().lower()
    plan_name_norm = (plan_name or plan_code_norm).strip().title()

    st.session_state["selected_plan_code"] = plan_code_norm
    st.session_state["selected_plan"] = plan_code_norm  # backward compat
    st.session_state["selected_plan_name"] = plan_name_norm

    st.session_state["return_to"] = "pricing"
    st.session_state.page = "demo_signup"
    st.session_state.current_page = "demo_signup"
    st.rerun()



PLANS = [
    {
        "name": "Demo",
        "price": "Free",
        "period": "forever",
        "icon": "🌱",
        "color": "#6B7280",
        "grad": "linear-gradient(135deg,#6B7280,#9CA3AF)",
        "desc": "Try SnapClass AI with up to 30 students.",
        "features": [
            "✅ 1 Institute",
            "✅ 30 students",
            "✅ Manual attendance",
            "✅ Basic analytics",
            "❌ AI attendance",
            "❌ Email alerts",
        ],
        "cta": "Get Free Demo",
    },
    {
        "name": "Starter",
        "price": "₹499",
        "period": "/month",
        "icon": "⚡",
        "color": "#5B6CFF",
        "grad": "linear-gradient(135deg,#5B6CFF,#818cf8)",
        "desc": "For small schools and coaching centres.",
        "features": [
            "✅ 1 Institute",
            "✅ 200 students",
            "✅ Manual + AI attendance",
            "✅ Analytics & reports",
            "✅ CSV export",
            "✅ Email alerts",
        ],
        "cta": "Start Free Trial",
    },
    {
        "name": "Pro",
        "price": "₹999",
        "period": "/month",
        "icon": "🚀",
        "popular": True,
        "color": "#FF4FA3",
        "grad": "linear-gradient(135deg,#FF4FA3,#f472b6)",
        "desc": "For growing institutes up to 1000 students.",
        "features": [
            "✅ 1 Institute",
            "✅ 1000 students",
            "✅ All attendance modes",
            "✅ Full analytics",
            "✅ CSV + PDF export",
            "✅ Priority support",
        ],
        "cta": "Start Free Trial",
    },
    {
        "name": "Enterprise",
        "price": "₹2,499",
        "period": "/month",
        "icon": "🏢",
        "color": "#10B981",
        "grad": "linear-gradient(135deg,#10B981,#34d399)",
        "desc": "For large institutes and multi-branch schools.",
        "features": [
            "✅ Unlimited institutes",
            "✅ Unlimited students",
            "✅ All features",
            "✅ Custom branding",
            "✅ API access",
            "✅ Dedicated support",
        ],
        "cta": "Contact Sales",
    },
]


def render_pricing_faq() -> None:
    st.markdown("## ❓ Frequently Asked Questions")
    st.caption("Clear answers before an institute starts using SnapClass AI.")

    with st.expander("Is the Demo plan really free?", expanded=False):
        st.write(
            "Yes. Demo is free for testing SnapClass AI with limited students. "
            "It is useful for schools/coaching institutes who want to try the product first."
        )

    with st.expander("Do paid plans include a free trial?", expanded=False):
        st.write(
            "Yes. Starter and Pro can offer a 14-day free trial. "
            "After trial, payment is required to continue using paid features."
        )

    with st.expander("What happens after payment?", expanded=False):
        st.write(
            "After successful payment, the institute subscription should be activated in Supabase. "
            "The selected plan, payment id, subscription status, and expiry date should be saved."
        )

    with st.expander("Which plan should a small coaching institute choose?", expanded=False):
        st.write(
            "Starter is best for small coaching institutes. Pro is better for growing institutes "
            "that need more students, analytics, reports, and support."
        )

    with st.expander("Can I upgrade later?", expanded=False):
        st.write(
            "Yes. The institute can start with Demo or Starter and upgrade to Pro or Enterprise later."
        )


def show_pricing() -> None:
    render_public_nav(show_links=False)

    if st.button("← Back to Home", key="pr_back"):
        go_to("landing")

    st.markdown(
        """<div style="text-align:center;padding:30px 0 20px;">
      <h1 style="font-family:Poppins,sans-serif;">Simple, Transparent Pricing</h1>
      <p style="color:#6B7280;">14-day free trial on all paid plans. No credit card required.</p>
    </div>""",
        unsafe_allow_html=True,
    )

    cols = st.columns(4, gap="large")
    for col, plan in zip(cols, PLANS):
        with col:
            pop = plan.get("popular", False)
            pop_html = (
                '<div style="background:#FF4FA3;color:white;font-size:.7rem;font-weight:700;'
                'padding:3px 10px;border-radius:999px;display:inline-block;margin-bottom:10px;">'
                "⭐ POPULAR</div>"
                if pop
                else '<div style="height:24px;"></div>'
            )
            border = f"border:2px solid {plan['color']};" if pop else "border:1px solid #E5E7EB;"
            feats = "".join(
                f"<div style='padding:5px 0;font-size:.84rem;border-bottom:1px solid #F3F4F6;'>{feature}</div>"
                for feature in plan["features"]
            )
            st.markdown(
                f"""
            <div class="sc-card" style="{border}text-align:center;padding:26px;">
              {pop_html}
              <div style="width:56px;height:56px;border-radius:18px;background:{plan['grad']};
                display:flex;align-items:center;justify-content:center;font-size:1.6rem;
                margin:0 auto 14px;box-shadow:0 6px 16px rgba(0,0,0,.1);">{plan['icon']}</div>
              <h3 style="margin:0 0 4px;">{plan['name']}</h3>
              <div style="font-size:1.8rem;font-weight:900;color:{plan['color']};margin:8px 0 4px;">
                {plan['price']} <span style="font-size:.9rem;color:#6B7280;font-weight:500;">{plan['period']}</span>
              </div>
              <p style="color:#6B7280;font-size:.83rem;margin:0 0 16px;">{plan['desc']}</p>
              <div style="text-align:left;margin-bottom:18px;">{feats}</div>
            </div>""",
                unsafe_allow_html=True,
            )

            btn_t = "primary" if pop else "secondary"
            if st.button(plan["cta"], key=f"pricing_{plan['name'].lower()}", type=btn_t, use_container_width=True):
                plan_name = plan["name"].strip().lower()

                # Demo: activate without payment
                if plan_name == "demo":
                    go_to_plan("demo", "Demo")

                # Starter/Pro: create Razorpay order (test mode) and open checkout
                elif plan_name in {"starter", "pro"}:
                    institute_id = st.session_state.get("institute_id")
                    user_id = st.session_state.get("user_id") or st.session_state.get("auth_user_id")
                    if not institute_id or not user_id:
                        # Persist selected plan; user will continue on signup.
                        go_to_plan(plan_name, plan_name.title())
                        return

                    if not is_razorpay_connected():
                        show_payment_not_configured()
                        return

                    # Context must be set when institute admin is logged in.
                    if plan_name == "starter":
                        plan_code = "starter"
                    else:
                        plan_code = "pro"

                    # Persist selection for the signup screen in case user returns.
                    st.session_state["selected_plan_code"] = plan_code
                    st.session_state["selected_plan_name"] = plan_name.title()

                    try:
                        order = create_razorpay_order(
                            plan_code=plan_code,
                            institute_id=str(institute_id),
                            user_id=str(user_id),
                        )

                    except Exception:
                        st.warning("Razorpay order could not be created. Please check payment configuration.")
                        with st.expander("Developer Debug", expanded=False):
                            st.code("Payment order creation failed.")
                        return

                    order_id = order["order_id"]
                    amount = order["amount"]
                    currency = order["currency"]
                    key_id = order["key_id"]

                    # Razorpay checkout UI.
                    # Note: Razorpay checkout JS needs an order_id; signature will be verified on success page.
                    secrets = read_app_secrets()
                    import razorpay

                    client = razorpay.Client(auth=(key_id, secrets.get("RAZORPAY_KEY_SECRET")))

                    # Create a checkout link via embedded modal is out of scope here.
                    # For Phase 5 Part A demo, we route to success page and pass query params.
                    st.session_state.page = "payment_success"
                    st.session_state.current_page = "payment_success"
                    st.query_params["razorpay_order_id"] = order_id
                    st.query_params["amount"] = str(amount)
                    st.query_params["currency"] = currency
                    st.query_params["plan_code"] = plan_code
                    st.query_params["plan_id"] = str(order.get("plan_id") or "")
                    st.rerun()

# Enterprise: contact sales
                elif plan_name == "enterprise":
                    # Enterprise: contact sales only (no signup form)
                    st.session_state["selected_plan_code"] = "enterprise"
                    st.session_state["selected_plan_name"] = "Enterprise"
                    st.session_state["selected_plan"] = "enterprise"  # backward compat
                    st.session_state.page = "contact"
                    st.session_state.current_page = "contact"
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    render_pricing_faq()
