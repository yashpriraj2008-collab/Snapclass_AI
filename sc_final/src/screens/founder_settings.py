import streamlit as st

from src.components.avatar import render_profile_photo_section
from src.components.ui import db_status_banner
from src.database.client import get_supabase_client, read_app_secrets, supabase_secrets_ready
from src.services.email_service import send_test_email
from src.services.profile_photo_service import fetch_user_profile
from src.utils.user_guards import (
    show_email_not_configured,
    show_supabase_not_configured,
)


def require_founder():
    user = st.session_state.get("user") or {}
    role = user.get("role")
    # Also support app code that stores role directly in session_state.
    session_role = st.session_state.get("role")
    effective_role = role or session_role

    if effective_role not in {"founder", "super_admin"}:
        st.error("You do not have permission to view this page.")
        st.stop()


def render_founder_settings():
    require_founder()
    db_status_banner()
    st.markdown("### ⚙️ Platform Settings")


    founder_db = get_supabase_client()
    founder_email = str(
        st.session_state.get("user_email")
        or st.session_state.get("email")
        or ""
    ).strip().lower()
    founder_profile = fetch_user_profile(founder_db, founder_email)
    founder_name = (
        founder_profile.get("full_name")
        or st.session_state.get("user_name")
        or "Founder"
    )
    founder_user = {
        **founder_profile,
        "name": founder_name,
        "full_name": founder_name,
        "email": founder_profile.get("email") or founder_email,
        "role": founder_profile.get("role") or "founder",
        "profile_photo_url": founder_profile.get("profile_photo_url") or "",
    }
    if founder_db:
        render_profile_photo_section(founder_db, founder_user, key_prefix="founder_profile")

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
    from src.services.email_service import is_email_configured

    if is_email_configured():
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
        st.success("✅ Resend email service configured.")
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
