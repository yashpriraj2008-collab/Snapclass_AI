"""Institute Students management page."""
import streamlit as st, uuid, pandas as pd


from src.services.institute_service import init_institute_state, _db, list_institutes
from src.utils.session import nav_institute

def _get_classes(inst_id):
    db = _db()
    if db and inst_id:
        try: return db.table("classes").select("*").eq("institute_id",inst_id).execute().data or []
        except Exception: pass
    return [c for c in st.session_state.get("classes",[]) if c.get("institute_id")==inst_id]

def show_students():
    init_institute_state()
    inst_id = st.session_state.get("active_institute_id","")
    st.markdown("### 👨‍🎓 Students")
    st.caption("Manage students in your institute")

    classes  = _get_classes(inst_id)
    cls_map  = {f"{c.get('class_name','')} {c.get('section','')}".strip(): c.get("id","") for c in classes}

    with st.expander("➕ Add New Student", expanded=False):
        with st.form("add_student_form"):
            c1,c2 = st.columns(2)
            s_name  = c1.text_input("Student Name *")
            s_roll  = c2.text_input("Roll Number *")
            c3,c4 = st.columns(2)
            s_cls   = c3.selectbox("Class", list(cls_map.keys()) or ["(Add classes first)"])
            s_email = c4.text_input("Email")
            c5,c6 = st.columns(2)
            s_phone = c5.text_input("Phone")
            p_name  = c6.text_input("Parent Name")
            p_phone = st.text_input("Parent Phone")
            if st.form_submit_button("Add Student", type="primary"):
                if not s_name or not s_roll:
                    st.error("Name and Roll Number are required.")
                else:
                    class_id = cls_map.get(s_cls,"")
                    record = {"id":str(uuid.uuid4()),"institute_id":inst_id,"class_id":class_id,
                              "roll_no":s_roll,"name":s_name,"email":s_email,"phone":s_phone,
                              "parent_name":p_name,"parent_phone":p_phone,"status":"active"}
                    db = _db()
                    if db and inst_id:
                        try:
                            db.table("students").insert(record).execute()
                            st.success(f"✅ {s_name} added.")
                        except Exception as e:
                            st.exception(e)
                    else:
                        st.session_state.students.append(record)
                        st.success(f"✅ {s_name} added (demo mode).")
                    st.rerun()

    # List students
    students = []
    db = _db()
    if db and inst_id:
        try: students = db.table("students").select("*").eq("institute_id",inst_id).eq("status","active").execute().data or []
        except Exception: students = [s for s in st.session_state.get("students",[]) if s.get("institute_id")==inst_id]
    else:
        students = [s for s in st.session_state.get("students",[]) if s.get("institute_id")==inst_id]

    if not students:
        st.info("No students added yet.")
        return

    search = st.text_input("🔍 Search", placeholder="Name or roll…", key="s_search")
    if search:
        students = [s for s in students if search.lower() in s.get("name","").lower()
                    or search.lower() in s.get("roll_no","").lower()]
    df = pd.DataFrame([{"Roll":s.get("roll_no",""),"Name":s.get("name",""),
                        "Email":s.get("email",""),"Parent":s.get("parent_name",""),
                        "Status":s.get("status","active")} for s in students])
    st.dataframe(df, use_container_width=True, hide_index=True)
