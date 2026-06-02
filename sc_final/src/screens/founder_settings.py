import streamlit as st

from src.components.ui import db_status_banner
from src.database.client import read_app_secrets, supabase_secrets_ready
from src.services.email_service import send_test_email
from src.utils.user_guards import show_email_not_configured, show_supabase_not_configured


def render_founder_settings():
    db_status_banner()
    st.markdown("### ⚙️ Platform Settings")

    # Connection test
    st.markdown("#### 🔌 Supabase Connection")
    ok = supabase_secrets_ready()
    if ok:
        try:
            from src.database.client import get_supabase

            db = get_supabase()
            if db:
                db.table("institutes").select("id").limit(1).execute()
                st.success("✅ Supabase connected and working correctly.")
        except Exception:
            st.error("Supabase connected, but the health check failed.")
            with st.expander("Developer Debug", expanded=False):
                st.code("Check Supabase tables and RLS policies.")
    else:
        show_supabase_not_configured()

    st.markdown("#### 🔑 Founder Access")
    st.info("Production founder access must use a real Supabase Auth user mapped to role `founder` in `user_profiles`.")

    st.markdown("#### 📧 Email Settings")
    secrets = read_app_secrets()
    key = str(secrets.get("RESEND_API_KEY", "") or "").strip()
    sender = str(secrets.get("SENDER_EMAIL", "") or "").strip()
    if key and key != "re_your_key_here":
        if sender:
            st.success(f"Sender configured: {sender}")
        else:
            st.warning("SENDER_EMAIL is not set. Add a verified Resend sender before production email.")
        test_email = st.text_input(
            "Send test email to",
            value=st.session_state.get("user_email", "") or "",
            key="founder_test_email_to",
        )
        if st.button("Send Test Email", key="founder_send_test_email"):
            if not test_email:
                st.warning("Enter a recipient email first.")
            else:
                result = send_test_email(
                    test_email,
                    sender_user_id=st.session_state.get("auth_user_id") or st.session_state.get("user_id"),
                )
                if result.get("ok"):
                    st.success("Test email sent and logged.")
                else:
                    st.warning(result.get("message") or "Test email could not be sent.")
        st.success("✅ Resend API key configured.")
    else:
        show_email_not_configured()

    st.markdown("#### 🗄️ Database Tables Check")
    ok = supabase_secrets_ready()
    if ok:
        from src.database.client import get_supabase

        db = get_supabase()
        if db:
            tables = [
                "institutes",
                "school_codes",
                "teachers",
                "students",
                "classes",
                "subjects",
                "attendance",
            ]
            for table in tables:
                try:
                    db.table(table).select("id").limit(1).execute()
                    st.markdown(f"✅ `{table}` — OK")
                except Exception:
                    st.markdown(f"❌ `{table}` — Missing or error")
    else:
        show_supabase_not_configured()
