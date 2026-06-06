"""Admin portal — all pages."""
import streamlit as st
import plotly.express as px
from src.components.sidebar import institute_sidebar
from src.components.cards import stat_card, alert_card
from src.components.ui import db_status_banner
from src.database.queries import (get_students, get_teachers, get_subjects,
                                   get_platform_stats, get_institutes,
                                   add_institute, add_student, add_teacher, add_subject,
                                   delete_student, delete_teacher, delete_institute)
from src.services.demo_data import INSTITUTES as DEMO_INSTITUTES
from src.utils.session import check_route_access
import pandas as pd

def show_admin_portal() -> None:
    check_route_access()
    institute_sidebar()
    page = st.session_state.get("institute_page", "institute_dashboard")
    dispatch = {
        "institute_dashboard": _dashboard,
        "my_institute": _schools,
        "teachers":  _teachers,
        "students":  _students,
        "classes_subjects": _subjects_page,
        "analytics": _analytics,
        "reports":   _reports,
    }
    dispatch.get(page, _dashboard)()

def _dashboard() -> None:
    db_status_banner()
    st.markdown("<h1>Admin Dashboard 🏫</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6B7280;margin-top:-8px;'>Platform-wide overview</p>",
                unsafe_allow_html=True)

    stats    = get_platform_stats()
    students = get_students()
    low      = len(students[students.attendance<75]) if not students.empty else 0

    c1,c2,c3,c4 = st.columns(4, gap="medium")
    with c1: stat_card("Institutes",     stats["institutes"],         "Active schools",      "blue",   "🏫")
    with c2: stat_card("Teachers",       stats["teachers"],           "Registered teachers", "pink",   "👩‍🏫")
    with c3: stat_card("Students",       stats["students"],           "Enrolled students",   "green",  "👨‍🎓")
    with c4: stat_card("Platform Avg",   f"{stats['avg_attendance']}%","Across all",         "orange", "📈")

    st.markdown("<br>", unsafe_allow_html=True)
    if low > 0:
        alert_card(f"⚠️ {low} student(s) below 75% attendance.", "warning")

    institutes = get_institutes()
    inst_list  = institutes if isinstance(institutes, list) else institutes.to_dict("records")
    col_l,col_r = st.columns([1.4,1], gap="large")
    with col_l:
        st.markdown("#### 🏫 Institutes")
        for inst in inst_list:
            att  = inst.get("attendance",80)
            kind = "ok" if att>=75 else "warn"
            st.markdown(f'''
            <div class="sc-subject-card">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div><h4 style="margin:0 0 4px;">{inst.get("name","—")}</h4>
                <p style="margin:0;">📍 {inst.get("city","—")}</p></div>
                <span class="sc-badge {kind}">{att}%</span>
              </div>
            </div>''', unsafe_allow_html=True)
    with col_r:
        st.markdown("#### 📊 Distribution")
        if not students.empty:
            fig = px.pie(students, names="name", values="attendance",
                         color_discrete_sequence=["#5B6CFF","#FF4FA3","#10B981","#F59E0B","#38BDF8","#818cf8"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=0,b=0), height=240)
            st.plotly_chart(fig, use_container_width=True)

    if not students.empty:
        st.markdown("#### 👨‍🎓 All Students")
        st.dataframe(
            students[["roll","name","class_name","attendance"]].rename(
                columns={"roll":"Roll","name":"Name","class_name":"Class","attendance":"Att %"}),
            use_container_width=True, hide_index=True)

def _schools() -> None:
    db_status_banner()
    st.markdown("### 🏫 Schools & Institutes")
    with st.expander("➕ Add New Institute"):
        c1,c2 = st.columns(2)
        n = c1.text_input("Name", key="inst_n", placeholder="Sunrise Academy")
        c = c2.text_input("City", key="inst_c", placeholder="Mumbai")
        if st.button("Add", type="primary", key="add_inst"):
            if n and c:
                r = add_institute(n, c)
                st.success(r["message"]) if r["ok"] else st.error(r["message"])
            else:
                st.warning("Fill both fields.")

    institutes = get_institutes()
    inst_list  = institutes if isinstance(institutes,list) else institutes.to_dict("records")
    for inst in inst_list:
        att  = inst.get("attendance",80)
        kind = "ok" if att>=75 else "warn"
        col1,col2 = st.columns([4,1])
        with col1:
            st.markdown(f'''
            <div class="sc-subject-card">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div><h4 style="margin:0 0 4px;">{inst.get("name","—")}</h4>
                <p style="margin:0;">📍 {inst.get("city","—")}</p></div>
                <span class="sc-badge {kind}">{att}%</span>
              </div>
            </div>''', unsafe_allow_html=True)
        with col2:
            iid = str(inst.get("id",""))
            if iid and st.button("🗑️", key=f"di_{iid}"):
                r = delete_institute(iid)
                st.success(r["message"]) if r["ok"] else st.error(r["message"])
                st.rerun()

def _teachers() -> None:
    db_status_banner()
    st.markdown("### 👩‍🏫 Teachers")
    with st.expander("➕ Add New Teacher"):
        c1,c2 = st.columns(2)
        n  = c1.text_input("Name",    key="t_n",  placeholder="Teacher name")
        e  = c2.text_input("Email",   key="t_e",  placeholder="teacher@example.com")
        c3,c4 = st.columns(2)
        s  = c3.text_input("Subject", key="t_s",  placeholder="Mathematics")
        cl = c4.text_input("Class",   key="t_cl", placeholder="Grade 12-A")
        if st.button("Add", type="primary", key="add_teacher"):
            if n and s:
                r = add_teacher(n, e, s, cl)
                st.success(r["message"]) if r["ok"] else st.error(r["message"])
            else:
                st.warning("Fill Name and Subject.")

    teachers = get_teachers()
    if not teachers.empty:
        st.dataframe(
            teachers[["name","subject","class_name","email"]].rename(
                columns={"name":"Name","subject":"Subject","class_name":"Class","email":"Email"}),
            use_container_width=True, hide_index=True)

def _students() -> None:
    db_status_banner()
    st.markdown("### 👨‍🎓 Students")
    search = st.text_input("🔍 Search", key="admin_search", placeholder="Name, roll, class…")

    with st.expander("➕ Add New Student"):
        c1,c2 = st.columns(2)
        n  = c1.text_input("Name",        key="s_n",  placeholder="Yashraj Mehta")
        e  = c2.text_input("Email",       key="s_e",  placeholder="student@email.com")
        c3,c4 = st.columns(2)
        r  = c3.text_input("Roll Number", key="s_r",  placeholder="SC009")
        cl = c4.text_input("Class",       key="s_cl", placeholder="12-A")
        if st.button("Add", type="primary", key="add_student"):
            if n and r:
                res = add_student(n, e, r, cl)
                st.success(res["message"]) if res["ok"] else st.error(res["message"])
            else:
                st.warning("Fill Name and Roll Number.")

    df = get_students()
    if search and not df.empty:
        df = df[df.name.str.contains(search,case=False)|
                df.roll.str.contains(search,case=False)|
                df.class_name.str.contains(search,case=False)]
    if not df.empty:
        st.dataframe(
            df[["roll","name","class_name","attendance","email"]].rename(
                columns={"roll":"Roll","name":"Name","class_name":"Class",
                         "attendance":"Att %","email":"Email"}),
            use_container_width=True, hide_index=True)

def _subjects_page() -> None:
    db_status_banner()
    st.markdown("### 📚 Subjects & Classes")
    with st.expander("➕ Add New Subject"):
        c1,c2,c3 = st.columns(3)
        n  = c1.text_input("Subject Name", key="subj_n", placeholder="Mathematics")
        t  = c2.text_input("Teacher",      key="subj_t", placeholder="Dr. Sharma")
        cl = c3.text_input("Class",        key="subj_c", placeholder="12-A")
        if st.button("Add", type="primary", key="add_subj"):
            if n and cl:
                r = add_subject(n, cl, t)
                st.success(r["message"]) if r["ok"] else st.error(r["message"])
            else:
                st.warning("Fill Subject Name and Class.")

    subjects = get_subjects()
    if not subjects.empty:
        st.dataframe(
            subjects[["subject","teacher","class_name","total","present","attendance"]].rename(
                columns={"subject":"Subject","teacher":"Teacher","class_name":"Class",
                         "total":"Total","present":"Present","attendance":"Att %"}),
            use_container_width=True, hide_index=True)

def _analytics() -> None:
    db_status_banner()
    st.markdown("### 📊 Platform Analytics")
    students = get_students()
    subjects = get_subjects()
    inst_df  = pd.DataFrame(DEMO_INSTITUTES)

    col1,col2 = st.columns(2)
    with col1:
        if not students.empty:
            fig = px.bar(students, x="name", y="attendance",
                         color="attendance", color_continuous_scale=["#EF4444","#F59E0B","#10B981"],
                         title="Student Attendance")
            fig.add_hline(y=75, line_dash="dash", line_color="#EF4444")
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              margin=dict(l=0,r=0,t=40,b=0), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.bar(inst_df, x="name", y="attendance", title="Institute Attendance",
                      color_discrete_sequence=["#5B6CFF"])
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig2, use_container_width=True)

    if not subjects.empty:
        fig3 = px.bar(subjects, x="subject", y="attendance",
                      color="attendance", color_continuous_scale=["#EF4444","#F59E0B","#10B981"],
                      title="Subject Attendance")
        fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(l=0,r=0,t=40,b=0), coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

def _reports() -> None:
    db_status_banner()
    st.markdown("### 📄 Platform Reports")
    students = get_students()
    if not students.empty:
        st.markdown("**All Students**")
        d = students[["roll","name","class_name","attendance"]].rename(
            columns={"roll":"Roll","name":"Name","class_name":"Class","attendance":"Att %"})
        st.dataframe(d, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download CSV", d.to_csv(index=False).encode(),
                           "all_students.csv","text/csv")

    inst_df = pd.DataFrame(DEMO_INSTITUTES)
    st.markdown("**Institutes Summary**")
    st.dataframe(inst_df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download Institutes CSV", inst_df.to_csv(index=False).encode(),
                       "institutes.csv","text/csv")
