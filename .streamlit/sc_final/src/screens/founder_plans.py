import streamlit as st

from src.components.ui import db_status_banner


def render_founder_plans():
    db_status_banner()
    st.markdown("### 💳 Plans & Pricing")
    st.caption("Manage subscription plans for institutes")

    plans = [
        ("Demo", "Free", 50, 1, False),
        ("Starter", "₹499/mo", 200, 5, False),
        ("Pro", "₹999/mo", 1000, 20, True),
        ("Enterprise", "₹2499/mo", 9999, 99, True),
    ]
    cols = st.columns(4, gap="medium")
    for col, (name, price, max_s, max_t, ai) in zip(cols, plans):
        with col:
            st.markdown(
                f"""
            <div class="sc-card" style="text-align:center;padding:24px;">
              <h3 style="margin:0 0 8px;">{name}</h3>
              <div style="font-size:1.4rem;font-weight:800;color:#5B6CFF;
                          margin-bottom:12px;">{price}</div>
              <p style="color:#6B7280;font-size:.85rem;margin:0;">
                👨‍🎓 Up to {max_s} students<br>
                👩‍🏫 Up to {max_t} teachers<br>
                🤖 AI Attendance: {"✅" if ai else "❌"}
              </p>
            </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏫 Institute Plans Overview")

    from src.services.institute_service import _db

    db = _db()
    if db:
        try:
            data = (
                db.table("institutes")
                .select("name,plan,status")
                .execute()
                .data
                or []
            )
            if data:
                import pandas as pd

                df = pd.DataFrame(data)[["name", "plan", "status"]]
                df.columns = ["Institute", "Plan", "Status"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No institutes with plans yet.")
        except Exception:
            st.info("No plan data available.")
    else:
        st.info("Connect Supabase to see plan assignments.")

