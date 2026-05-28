import streamlit as st

from src.components.ui import db_status_banner


def render_founder_reports():
    db_status_banner()
    st.markdown("### 📄 Platform Reports")
    st.caption("Overview of all institutes, teachers, students, and attendance")

    from src.services.institute_service import _db

    db = _db()

    col1, col2, col3, col4 = st.columns(4)
    if db:
        try:
            n_inst = len(db.table("institutes").select("id").execute().data or [])
            n_teach = len(db.table("teachers").select("id").execute().data or [])
            n_stud = len(db.table("students").select("id").execute().data or [])
            n_att = len(db.table("attendance").select("id").execute().data or [])
        except Exception:
            n_inst = n_teach = n_stud = n_att = 0
    else:
        n_inst = n_teach = n_stud = n_att = 0

    col1.metric("Institutes", n_inst)
    col2.metric("Teachers", n_teach)
    col3.metric("Students", n_stud)
    col4.metric("Attendance Records", n_att)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏫 All Institutes")

    if db:
        try:
            data = (
                db.table("institutes")
                .select("name,institute_type,city,plan,status,admin_email")
                .execute()
                .data
                or []
            )
            if data:
                import pandas as pd

                df = pd.DataFrame(data)
                df.columns = ["Name", "Type", "City", "Plan", "Status", "Admin Email"]
                st.dataframe(df, use_container_width=True, hide_index=True)

                csv = df.to_csv(index=False).encode()
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    "institutes_report.csv",
                    "text/csv",
                    use_container_width=False,
                )
            else:
                st.info("No institute data yet.")
        except Exception as e:
            st.error(f"Error loading report: {e}")
    else:
        st.info("Connect Supabase to generate reports.")

