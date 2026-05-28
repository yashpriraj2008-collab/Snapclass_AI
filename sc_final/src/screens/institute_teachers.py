"""Institute Teachers management page."""
import streamlit as st
from src.services.institute_service import init_institute_state, _db
from src.utils.session import nav_institute
import uuid




def show_teachers():
    init_institute_state()
    inst_id = st.session_state.get("active_institute_id","")
    st.markdown("### 👩‍🏫 Teachers")
    st.caption("Manage teachers in your institute")

    with st.expander("➕ Add New Teacher", expanded=False):
        with st.form("add_teacher_form"):
            c1,c2 = st.columns(2)
            t_name = c1.text_input("Teacher Name *")
            t_email= c2.text_input("Email")
            c3,c4 = st.columns(2)
            t_phone= c3.text_input("Phone")
            t_spec = c4.text_input("Specialization", placeholder="Mathematics")
            if st.form_submit_button("Add Teacher", type="primary"):
                if not t_name:
                    st.error("Name is required.")
                else:
                    record = {"id":str(uuid.uuid4()),"institute_id":inst_id,
                              "name":t_name,"email":t_email,"phone":t_phone,
                              "specialization":t_spec,"status":"active"}
                    db = _db()
                    if db and inst_id:
                        try:
                            db.table("teachers").insert(record).execute()
                            st.success(f"✅ {t_name} added to Supabase.")
                        except Exception as e:
                            st.exception(e)
                    else:
                        st.session_state.teachers.append(record)
                        st.success(f"✅ {t_name} added (demo mode).")
                    st.rerun()

    # List teachers
    teachers = []
    db = _db()
    if db and inst_id:
        try:
            teachers = db.table("teachers").select("*").eq("institute_id",inst_id).execute().data or []
        except Exception:
            teachers = [t for t in st.session_state.get("teachers",[]) if t.get("institute_id")==inst_id]
    else:
        teachers = [t for t in st.session_state.get("teachers",[]) if t.get("institute_id")==inst_id]

    if not teachers:
        st.info("No teachers added yet. Use the form above.")
        return

    search = st.text_input("🔍 Search", placeholder="Name or email…", key="t_search")
    if search:
        teachers = [t for t in teachers if search.lower() in t.get("name","").lower()
                    or search.lower() in t.get("email","").lower()]
    for t in teachers:
        st.markdown(f"""
        <div class="sc-subject-card">
          <h4 style="margin:0 0 4px;">👩‍🏫 {t.get("name","—")}</h4>
          <p style="margin:0;">✉️ {t.get("email","—")} &nbsp;•&nbsp;
             📞 {t.get("phone","—")} &nbsp;•&nbsp;
             📚 {t.get("specialization","—")}</p>
        </div>""", unsafe_allow_html=True)
