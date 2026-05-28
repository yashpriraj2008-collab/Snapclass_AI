import streamlit as st

from src.components.ui import db_status_banner
from src.database.client import get_supabase


def render_founder_settings():
    db_status_banner()
    st.markdown("### ⚙️ Platform Settings")

    # Connection test
    st.markdown("#### 🔌 Supabase Connection")
    db = get_supabase()
    if db:
        try:
            db.table("institutes").select("id").limit(1).execute()
            st.success("✅ Supabase connected and working correctly.")
        except Exception as e:
            st.error(f"❌ Supabase connected but error: {e}")
    else:
        st.error("❌ Supabase not configured. Add keys to secrets.toml")
        st.code(
            """
# .streamlit/secrets.toml
SUPABASE_URL   = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
            """
        )

    st.markdown("#### 🔑 Founder Credentials")
    st.info("Change founder credentials in src/screens/founder_auth.py")
    st.code('FOUNDER_EMAIL    = "founder@snapclass.ai"\nFOUNDER_PASSWORD = "founder@123"')

    st.markdown("#### 📧 Email Settings")
    try:
        key = st.secrets.get("RESEND_API_KEY", "")
        if key and key != "re_your_key_here":
            st.success("✅ Resend API key configured.")
        else:
            st.warning("⚠️ RESEND_API_KEY not set. Add to secrets.toml")
    except Exception:
        st.warning("⚠️ Cannot read secrets.")

    st.markdown("#### 🗄️ Database Tables Check")
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
        st.info("Connect Supabase to check tables.")

