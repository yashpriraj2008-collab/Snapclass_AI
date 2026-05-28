"""Institute Admin dashboard — full version."""
import streamlit as st


from src.services.institute_service import init_institute_state, _db


from src.utils.session import nav_institute
from src.components.ui import db_status_banner


def show_institute_dashboard():
    init_institute_state()
    db_status_banner()
    inst     = st.session_state.get("current_institute") or {}
    inst_id  = st.session_state.get("active_institute_id","")
    admin_n  = st.session_state.get("admin_name", st.session_state.get("user_name","Admin"))
    inst_nm  = inst.get("name", st.session_state.get("active_institute_name","My Institute"))

    st.markdown(f"<h1>Welcome, {admin_n}! 🏫</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#6B7280;margin-top:-8px;'>{inst_nm} — Institute Overview</p>",
                unsafe_allow_html=True)

    def _count(table):
        db = _db()
        if db and inst_id:
            try: return len(db.table(table).select("id").eq("institute_id",inst_id).execute().data or [])
            except Exception: pass
        return len([x for x in st.session_state.get(table,[]) if x.get("institute_id")==inst_id])

    n_teachers = _count("teachers")
    n_students = _count("students")
    n_classes  = _count("classes")
    n_subjects = _count("subjects")

    c1,c2,c3,c4 = st.columns(4,gap="medium")
    for col,label,val,color,icon in [
        (c1,"Teachers",  n_teachers,"pink",  "👩‍🏫"),
        (c2,"Students",  n_students,"blue",  "👨‍🎓"),
        (c3,"Classes",   n_classes, "green", "🏫"),
        (c4,"Subjects",  n_subjects,"orange","📚"),
    ]:
        with col:
            st.markdown(f"""
            <div class="sc-stat {color}">
              <div class="sc-stat-icon">{icon}</div>
              <div class="sc-stat-label">{label}</div>
              <div class="sc-stat-value">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚡ Quick Actions")
    qa1,qa2,qa3,qa4 = st.columns(4,gap="medium")
    if qa1.button("➕ Add Teacher",  type="primary",use_container_width=True,key="qa_t"): nav_institute("teachers")
    if qa2.button("➕ Add Student",  type="primary",use_container_width=True,key="qa_s"): nav_institute("students")
    if qa3.button("➕ Add Class",    type="primary",use_container_width=True,key="qa_c"): nav_institute("classes_subjects")
    if qa4.button("➕ Add Subject",  type="primary",use_container_width=True,key="qa_sub"): nav_institute("classes_subjects")

    if not n_teachers and not n_students and not n_classes:
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown("""<div class="sc-alert info">ℹ️ <strong>Getting Started:</strong>
          Add Classes first → then Teachers → then Students.
          Use Quick Actions above or sidebar navigation.</div>""", unsafe_allow_html=True)

    # Institute info card
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown("#### 🏫 Institute Profile")
    st.markdown(f"""
    <div class="sc-card" style="padding:22px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
        <div>
          <h3 style="margin:0 0 6px;">{inst.get("name","—")}</h3>
          <p style="margin:0;color:#6B7280;">
            🏛️ {inst.get("institute_type","School")} &nbsp;•&nbsp;
            📍 {inst.get("city","—")}, {inst.get("state","—")} &nbsp;•&nbsp;
            📧 {inst.get("admin_email","—")}
          </p>
        </div>
        <div style="display:flex;gap:8px;">
          <span class="sc-badge primary">{inst.get("plan","Demo")}</span>
          <span class="sc-badge ok">{inst.get("status","active").title()}</span>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)
    if st.button("✏️ Edit Institute Profile", key="inst_edit_btn"):
        nav_institute("my_institute")
