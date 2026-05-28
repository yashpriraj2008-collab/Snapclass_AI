"""Student portal — all pages."""
import streamlit as st
import plotly.express as px
from src.components.sidebar import student_sidebar
from src.components.ui import db_status_banner
from src.utils.session import nav_student, check_route_access
from src.utils.helpers import attendance_color
from src.services.demo_data import ATTENDANCE_TREND, NOTIFICATIONS

def show_student_portal():
    check_route_access()
    student_sidebar()
    p = st.session_state.get("student_page","dashboard")
    if   p == "dashboard":     _dashboard()
    elif p == "faceid":
        from src.screens.student_faceid import show_faceid; show_faceid()
    elif p == "subjects":      _subjects()
    elif p == "history":       _history()
    elif p == "analytics":     _analytics()
    elif p == "reports":       _reports()

    elif p == "profile":       _profile()
    else:                      _dashboard()

def _get_subjects():
    try:
        from src.database.queries import get_subjects
        return get_subjects()
    except Exception:
        from src.services.demo_data import SUBJECTS
        return SUBJECTS

def _get_stats():
    try:
        from src.database.queries import get_attendance_stats_for_student
        from src.services.student_identity import resolve_student_identity
        from src.database.client import get_supabase

        supabase = get_supabase()
        resolved = resolve_student_identity(supabase) if supabase else None
        # stats helper accepts roll_no in this repo.
        roll = st.session_state.get("roll_no") or st.session_state.get("user_roll", "SC001")
        return get_attendance_stats_for_student(str(roll))

    except Exception:
        return {"pct":85.7,"present":36,"absent":6,"total":42}

# Old student-specific notification bell removed.
# Notification UI is now rendered globally from src/components/notifications.py



def _dashboard():
    db_status_banner()
    name = (st.session_state.get("user_name","") or "Student").replace(" Demo","").strip()
    roll = st.session_state.get("user_roll","SC001")
    st.markdown(
        f"""
        <div class="student-dashboard-page">
          <h1 style="margin-top:10px;">Welcome back, {name}! 👋</h1>
          <p style='color:#6B7280;margin-top:-6px;'>Your attendance overview</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    subj  = _get_subjects()
    stats = _get_stats()
    overall = stats.get("pct") or (round(subj.present.sum()/subj.total.sum()*100,1) if not subj.empty else 0)

    c1,c2,c3,c4 = st.columns(4,gap="medium")
    for col,label,val,color,icon in [
        (c1,"Overall Attendance",f"{overall}%","blue","📈"),
        (c2,"Total Subjects",len(subj),"pink","📚"),
        (c3,"Classes Attended",stats.get("present",0),"green","✅"),
        (c4,"Classes Absent",stats.get("absent",0),"orange","❌"),
    ]:
        with col:
            st.markdown(f"""<div class="sc-stat {color}">
              <div class="sc-stat-icon">{icon}</div>
              <div class="sc-stat-label">{label}</div>
              <div class="sc-stat-value">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1.4,1], gap="large")
    with col_l:
        st.markdown("#### 📈 Attendance Trend")
        fig = px.line(ATTENDANCE_TREND, x="month", y="attendance", markers=True,
                      color_discrete_sequence=["#5B6CFF"])
        fig.add_hline(y=75, line_dash="dash", line_color="#EF4444",
                      annotation_text="75% Min", annotation_position="left")
        fig.update_layout(
            template="plotly_white",
            font=dict(color="#111827", size=14),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=55, r=30, t=30, b=55),
            height=220,
        )

        fig.update_xaxes(
            title_font=dict(color="#334155", size=13),
            tickfont=dict(color="#334155", size=12),
            gridcolor="#e5e7eb",
            linecolor="#94a3b8",
            zerolinecolor="#e5e7eb",
        )
        fig.update_yaxes(
            title_font=dict(color="#334155", size=13),
            tickfont=dict(color="#334155", size=12),
            gridcolor="#e5e7eb",
            linecolor="#94a3b8",
            zerolinecolor="#e5e7eb",
        )
        fig.update_traces(line_width=3, marker_size=8)
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        st.markdown("#### 🕐 Today's Classes")
        for subj_n,time,teacher,status in [
            ("Mathematics","9:00 AM","Dr. Sharma","Present"),
            ("Physics","11:00 AM","Prof. Gupta","Upcoming"),
            ("Chemistry","2:00 PM","Dr. Patel","Upcoming"),
        ]:
            color_m = {"Present":"#10B981","Upcoming":"#5B6CFF","Absent":"#EF4444"}.get(status,"#6B7280")
            badge   = {"Present":"ok","Upcoming":"primary","Absent":"danger"}.get(status,"info")
            st.markdown(f"""<div class="sc-class-item">
              <div><div style="font-weight:600;font-size:.88rem;">{subj_n}</div>
              <div style="color:#6B7280;font-size:.78rem;">{teacher} • {time}</div></div>
              <span class="sc-badge {badge}">{status}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if not subj.empty:
        low = subj[subj.attendance<75]
        if not low.empty:
            st.markdown("#### ⚠️ Low Attendance Warnings")
            for _,row in low.iterrows():
                kind = "danger" if row.attendance<60 else "warning"
                c1,c2 = st.columns([5,1])
                with c1:
                    st.markdown(f"""<div class="sc-alert {kind}">
                      ⚠️ <strong>{row.subject}</strong> — {row.attendance}% — below 75% minimum
                    </div>""", unsafe_allow_html=True)
                with c2:
                    if st.button("📧", key=f"alert_{row.subject}", help="Send email alert"):
                        try:
                            from src.services.email_service import send_low_attendance_alert
                            r = send_low_attendance_alert(
                                st.session_state.get("user_email",""),
                                name, row.subject, row.attendance)
                            st.success("✅ Alert sent!") if r.get("ok") else st.warning(r.get("message",""))
                        except: st.warning("Email not configured")

    if st.button("🪪 Mark FaceID Attendance", type="primary", key="goto_faceid"):
        nav_student("faceid")

def _subjects():
    db_status_banner()
    st.markdown("### 📚 My Subjects")
    st.caption("View all your enrolled subjects and track attendance")
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Enrollment: enroll in subject via join code ---
    st.markdown("## ➕ Enroll in Subject")

    try:
        from src.database.client import get_supabase

        supabase = get_supabase()
    except Exception:
        supabase = None

    if supabase is None:
        st.warning("Supabase is not connected. Enrolment will not work.")
    else:
        join_code_input = st.text_input(
            "Enter subject join code",
            placeholder="e.g., SC-ABC12",
            key="enroll_join_code",
        )

        if st.button("Enroll", type="primary", key="enroll_btn"):
            from src.services.student_identity import resolve_student_identity
            from src.services.subject_service import enroll_student_with_code

            # Resolve student_id from session (and Supabase if needed).
            resolved_id = resolve_student_identity(supabase)
            if not resolved_id:
                st.error(
                    "Student identity missing. Login again so the app can map your email/roll number to your Supabase student_id."
                )
                st.stop()

            ok, msg = enroll_student_with_code(supabase, resolved_id, join_code_input)
            if ok:
                st.success("✅ Enrolled successfully!")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


    # --- My Subjects (from enrolments) ---
    subj_rows = []
    try:
        from src.services.subject_service import get_student_enrolled_subjects

        from src.services.student_identity import resolve_student_identity

        resolved_id = None
        if supabase is not None:
            resolved_id = resolve_student_identity(supabase)

        if supabase is not None and resolved_id:
            subj_rows = get_student_enrolled_subjects(supabase, resolved_id) or []

    except Exception as e:
        st.caption(f"[debug] enrolled subjects fetch failed: {e}")

    if not subj_rows:
        st.info("No subjects found.")
        return

    # Normalize to pandas-like rows for the existing card renderer
    # (existing code expects a DataFrame with columns: subject, teacher, total, present, attendance)
    # We'll render minimal info using whatever columns exist.
    import pandas as pd

    subj_df = pd.DataFrame(subj_rows)
    if "subject" not in subj_df.columns:
        # Map likely columns from your `subjects` table
        subj_df["subject"] = subj_df.get("name")
    if "teacher" not in subj_df.columns:
        subj_df["teacher"] = subj_df.get("teacher_name") or subj_df.get("teacher_email") or "—"
    if "total" not in subj_df.columns:
        subj_df["total"] = 0
    if "present" not in subj_df.columns:
        subj_df["present"] = 0
    if "attendance" not in subj_df.columns:
        subj_df["attendance"] = 0

    subj = subj_df


    GRADS = [
        ("linear-gradient(135deg,#5B6CFF,#818cf8)","#DCFCE7","#16A34A"),
        ("linear-gradient(135deg,#FF4FA3,#f472b6)","#FEF9C3","#CA8A04"),
        ("linear-gradient(135deg,#10B981,#34d399)","#DCFCE7","#16A34A"),
        ("linear-gradient(135deg,#F59E0B,#fbbf24)","#FEF9C3","#CA8A04"),
        ("linear-gradient(135deg,#38BDF8,#7dd3fc)","#DCFCE7","#16A34A"),
        ("linear-gradient(135deg,#8B5CF6,#a78bfa)","#FEE2E2","#DC2626"),
    ]
    cols = st.columns(3, gap="large")
    for idx,(_,row) in enumerate(subj.iterrows()):
        grad,badge_bg,badge_c = GRADS[idx%len(GRADS)]
        kind   = attendance_color(row.attendance)
        bar_c  = {"ok":"#10B981","warn":"#F59E0B","danger":"#EF4444"}.get(kind,"#5B6CFF")
        badge_t= {"ok":"Good","warn":"Low","danger":"Critical"}.get(kind,"—")
        bkg    = {"ok":"#DCFCE7","warn":"#FEF9C3","danger":"#FEE2E2"}.get(kind,"#EEF0FF")
        bclr   = {"ok":"#16A34A","warn":"#CA8A04","danger":"#DC2626"}.get(kind,"#5B6CFF")
        bar_e  = {"ok":"#34d399","warn":"#fbbf24","danger":"#f87171"}.get(kind,"#818cf8")
        with cols[idx%3]:
            st.markdown(f"""
            <div style="background:white;border-radius:20px;padding:22px;
              border:1px solid #E5E7EB;margin-bottom:20px;
              box-shadow:0 4px 16px rgba(0,0,0,.06);">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;">
                <div style="width:52px;height:52px;border-radius:16px;background:{grad};
                  display:flex;align-items:center;justify-content:center;font-size:1.5rem;
                  box-shadow:0 4px 12px rgba(0,0,0,.12);">📖</div>
                <span style="background:{bkg};color:{bclr};padding:4px 12px;
                  border-radius:999px;font-size:.74rem;font-weight:700;">{badge_t}</span>
              </div>
              <div style="font-weight:800;font-size:1.05rem;margin-bottom:4px;">{row.subject}</div>
              <div style="color:#6B7280;font-size:.82rem;margin-bottom:14px;">👤 {row.teacher}</div>
              <div style="background:linear-gradient(135deg,#FF4FA3,#f472b6);color:white;
                border-radius:10px;padding:8px 12px;display:flex;justify-content:space-between;
                margin-bottom:8px;font-size:.83rem;">
                <span>📅 Total Classes</span><strong>{row.total}</strong></div>
              <div style="background:#ECFDF5;border-radius:10px;padding:8px 12px;
                display:flex;justify-content:space-between;margin-bottom:14px;font-size:.83rem;">
                <span style="color:#059669;">✅ Attended</span>
                <strong style="color:#059669;">{row.present}</strong></div>
              <div style="display:flex;justify-content:space-between;font-size:.82rem;
                color:#6B7280;margin-bottom:6px;">
                <span>Attendance</span>
                <strong style="color:{bar_c};">{row.attendance}%</strong></div>
              <div style="background:#F3F4F6;border-radius:999px;height:8px;overflow:hidden;">
                <div style="width:{min(row.attendance,100)}%;
                  background:linear-gradient(90deg,{bar_c},{bar_e});
                  height:8px;border-radius:999px;"></div>
              </div>
            </div>""", unsafe_allow_html=True)

def _history():
    db_status_banner()

    import pandas as pd
    import streamlit as st

    # Supabase client is created inside db_status_banner() sometimes; safest is to re-init here.
    try:
        from src.database.client import get_supabase

        supabase = get_supabase()
    except Exception:
        supabase = None

    if supabase is None:
        st.warning("Supabase not connected. Attendance History may be unavailable.")
        return

    st.markdown("## 📋 Attendance History")

    # Resolve student_id via shared resolver.
    from src.services.student_identity import resolve_student_identity

    resolved_id = resolve_student_identity(supabase)
    if not resolved_id:
        st.warning("Student identity missing. Please login again so the app can map your email/roll number."
                   )
        return

    try:
        query = supabase.table("attendance").select("*").eq("student_id", resolved_id)
        result = query.order("attendance_date", desc=True).execute()
        rows = result.data or []

        if not rows:
            st.info("No attendance history found yet.")
            st.caption("Once your teacher marks attendance, records will appear here.")
            return


        df = pd.DataFrame(rows)

        rename_map = {
            "attendance_date": "Date",
            "date": "Date",
            "class_name": "Class",
            "subject_name": "Subject",
            "subject": "Subject",
            "status": "Status",
            "marked_by": "Marked By",
            "created_at": "Saved At",
        }

        df = df.rename(columns=rename_map)

        visible_cols = [
            col
            for col in [
                "Date",
                "Class",
                "Subject",
                "Status",
                "Marked By",
                "Saved At",
            ]
            if col in df.columns
        ]

        st.dataframe(
            df[visible_cols] if visible_cols else df,
            use_container_width=True,
            hide_index=True,
        )

        if "Status" in df.columns:
            present_count = (df["Status"].astype(str).str.lower() == "present").sum()
            total_count = len(df)
            percentage = round((present_count / total_count) * 100, 2) if total_count else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Records", total_count)
            c2.metric("Present", present_count)
            c3.metric("Attendance %", f"{percentage}%")

    except Exception as e:
        st.error("Could not load attendance history.")
        st.exception(e)


def _analytics():
    db_status_banner()
    st.markdown("### 📊 Analytics")
    subj = _get_subjects()
    if subj.empty: st.info("No data yet."); return
    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(subj, x="subject", y="attendance",
                     color="attendance", color_continuous_scale=["#EF4444","#F59E0B","#10B981"],
                     title="Subject-wise Attendance %")
        fig.add_hline(y=75, line_dash="dash", line_color="#EF4444")
        fig.update_layout(
            template="plotly_white",
            font=dict(color="#111827"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=40,b=0),
            coloraxis_showscale=False,
        )

        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = px.pie(subj, names="subject", values="attendance", title="Attendance Share",
                      color_discrete_sequence=["#5B6CFF","#FF4FA3","#10B981","#F59E0B","#38BDF8","#818cf8"])
        fig2.update_layout(
            template="plotly_white",
            font=dict(color="#111827"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0,r=0,t=40,b=0),
        )

        st.plotly_chart(fig2, use_container_width=True)

def _reports():
    db_status_banner()
    st.markdown("### 📄 Reports")

    # Resolve student_id via shared resolver.
    try:
        from src.database.client import get_supabase

        supabase = get_supabase()
    except Exception:
        supabase = None

    if not supabase:
        st.info("No attendance report found yet.")
        return

    from src.services.student_identity import resolve_student_identity

    resolved_id = resolve_student_identity(supabase)
    if not resolved_id:
        st.info("No attendance report found yet.")
        return

    import pandas as pd

    # Prefer attendance_records if table exists; fall back to attendance.
    rows = []
    try:
        rows = (
            supabase.table("attendance_records")
            .select("*")
            .eq("student_id", resolved_id)
            .order("attendance_date", desc=True)
            .execute()
            .data
            or []
        )
    except Exception:
        rows = []

    if not rows:
        try:
            rows = (
                supabase.table("attendance")
                .select("*")
                .eq("student_id", resolved_id)
                .order("attendance_date", desc=True)
                .execute()
                .data
                or []
            )
        except Exception:
            rows = []

    if not rows:
        st.info("No attendance report found yet.")
        st.caption("Once your teacher marks attendance, reports will be available here.")
        return

    df = pd.DataFrame(rows)

    # Normalize columns for display.
    rename_map = {
        "attendance_date": "Date",
        "date": "Date",
        "class_name": "Class",
        "subject_name": "Subject",
        "subject": "Subject",
        "status": "Status",
        "marked_by": "Marked By",
        "created_at": "Saved At",
    }
    df = df.rename(columns=rename_map)

    visible_cols = [
        c
        for c in [
            "Date",
            "Class",
            "Subject",
            "Status",
            "Marked By",
            "Saved At",
        ]
        if c in df.columns
    ]

    st.dataframe(
        df[visible_cols] if visible_cols else df,
        use_container_width=True,
        hide_index=True,
    )

    csv = (df[visible_cols] if visible_cols else df).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV",
        csv,
        "my_attendance_records.csv",
        "text/csv",
        use_container_width=True,
    )






def _profile():
    st.markdown("### 👤 My Profile")
    name = (st.session_state.get("user_name","") or "Student").replace(" Demo","").strip()
    c1,c2 = st.columns([1,2], gap="large")
    with c1:
        st.markdown(f"""<div class="sc-card" style="text-align:center;padding:32px;">
          <div style="font-size:4rem;margin-bottom:12px;">👨‍🎓</div>
          <h3 style="margin:0;">{name}</h3>
          <p style="color:#6B7280;margin:4px 0;">Student</p>
          <span class="sc-badge primary">{st.session_state.get("user_roll","SC001")}</span>
        </div>""", unsafe_allow_html=True)
    with c2:
        n = st.text_input("Full Name",   value=name, key="p_name")
        st.text_input("Email",  value=st.session_state.get("user_email",""),key="p_email",disabled=True)
        r = st.text_input("Roll Number", value=st.session_state.get("user_roll",""), key="p_roll")
        if st.button("Save Profile", type="primary", key="save_profile"):
            st.session_state.user_name = n
            st.session_state.user_roll = r
            st.success("✅ Profile updated.")
