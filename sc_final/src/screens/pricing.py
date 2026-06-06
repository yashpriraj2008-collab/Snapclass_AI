"""Pricing page."""

import streamlit as st

from src.components.navigation import go_to
from src.components.public_nav import render_public_nav


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
        "period": "Demo access",
        "icon": "🌱",
        "color": "#6B7280",
        "grad": "linear-gradient(135deg,#6B7280,#9CA3AF)",
        "desc": "Test SnapClass AI with limited features before subscribing.",
        "features": [
            "✅ 1 Institute",
            "✅ 30 students",
            "✅ Manual attendance",
            "✅ Basic analytics",
            "❌ AI attendance",
            "❌ Email alerts",
        ],
        "cta": "Try Demo",
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
        "cta": "Subscribe Now",
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
        "cta": "Subscribe Now",
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

    with st.expander("What is the Demo plan?", expanded=False):
        st.write(
            "Demo access is for testing SnapClass AI with limited students. "
            "It helps institutes try the product before subscribing to paid plans."
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
      <p style="color:#6B7280;">No trial required. Choose Demo for testing or select a paid plan to start using SnapClass AI.</p>
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
            if st.button(
                plan["cta"],
                key=f"pricing_{plan['name'].lower()}",
                type=btn_t,
                use_container_width=True,
            ):
                plan_name = plan["name"].strip().lower()

                # Demo: activate without payment
                if plan_name == "demo":
                    go_to_plan("demo", "Demo")

                # Paid self-serve plans: create institute, then continue to payment.
                elif plan_name in {"starter", "pro"}:
                    go_to_plan(plan_name, plan_name.title())

                elif plan_name == "enterprise":
                    st.session_state["selected_plan_code"] = "enterprise"
                    st.session_state["selected_plan_name"] = "Enterprise"
                    st.session_state["selected_plan"] = "enterprise"
                    st.session_state.page = "contact"
                    st.session_state.current_page = "contact"
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    render_pricing_faq()
