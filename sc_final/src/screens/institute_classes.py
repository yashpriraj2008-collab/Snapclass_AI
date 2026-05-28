"""Classes & Subjects management for institute admin."""
import streamlit as st, uuid, pandas as pd


from src.services.institute_service import init_institute_state, _db





def show_classes_subjects():
    init_institute_state()
    inst_id = st.session_state.get("active_institute_id","")
    st.markdown("### 📚 Classes & Subjects")

    tab_cls, tab_sub = st.tabs(["🏫 Classes","📖 Subjects"])

    def get_classes():
        db = _db()
        if db and inst_id:
            try: return db.table("classes").select("*").eq("institute_id",inst_id).execute().data or []
            except Exception: pass
        return [c for c in st.session_state.get("classes",[]) if c.get("institute_id")==inst_id]

    def get_subjects():
        db = _db()
        if db and inst_id:
            try: return db.table("subjects").select("*").eq("institute_id",inst_id).execute().data or []
            except Exception: pass
        return [s for s in st.session_state.get("subjects",[]) if s.get("institute_id")==inst_id]

    with tab_cls:
        with st.expander("➕ Add Class", expanded=False):
            with st.form("add_class_form"):
                c1,c2,c3 = st.columns(3)
                cls_name = c1.text_input("Class Name *", placeholder="Grade 10")
                section  = c2.text_input("Section",      placeholder="A")
                acad_yr  = c3.text_input("Academic Year",placeholder="2025-26")
                if st.form_submit_button("Add Class", type="primary"):
                    if not cls_name:
                        st.error("Class name required.")
                    else:
                        record = {"id":str(uuid.uuid4()),"institute_id":inst_id,
                                  "class_name":cls_name,"section":section,"academic_year":acad_yr}
                        db = _db()
                        if db and inst_id:
                            try:
                                db.table("classes").insert(record).execute()
                                st.success(f"✅ Class {cls_name} added.")
                            except Exception as e:
                                st.exception(e)
                        else:
                            st.session_state.classes.append(record)
                            st.success(f"✅ {cls_name} added (demo mode).")
                        st.rerun()
        classes = get_classes()
        if classes:
            st.dataframe(pd.DataFrame([{"Class":c.get("class_name",""),"Section":c.get("section",""),
                          "Academic Year":c.get("academic_year","")} for c in classes]),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No classes yet. Add one above.")

    with tab_sub:
        classes  = get_classes()
        cls_map  = {f"{c.get('class_name','')} {c.get('section','')}".strip(): c.get("id","") for c in classes}
        with st.expander("➕ Add Subject", expanded=False):
            with st.form("add_subject_form"):
                c1,c2,c3 = st.columns(3)

                # Required: if no classes exist, show exact empty-state text
                if not cls_map:
                    st.info("Please add a class first before adding subjects.")
                else:
                    # Required: Class dropdown should show "ClassName - Section" and store class_id internally
                    class_options = {
                        f"{c.get('class_name','')} - {c.get('section','')}".strip(): c.get('id')
                        for c in classes
                        if c.get('id')
                    }
                    selected_class_label = c1.selectbox(
                        "Class *",
                        list(class_options.keys()),
                        index=None,
                        placeholder="Select class",
                        key="subject_class_select",
                    )
                    selected_class_id = class_options.get(selected_class_label) if selected_class_label else None

                    s_name = c2.text_input("Subject Name *", placeholder="Mathematics")
                    s_code = c3.text_input("Subject Code", placeholder="MATH-10")

                    if st.form_submit_button("Add Subject", type="primary"):
                        if not selected_class_id:
                            st.error("Select a class.")
                        elif not s_name:
                            st.error("Subject name required.")
                        else:
                            record = {
                                "id": str(uuid.uuid4()),
                                "institute_id": inst_id,
                                "class_id": selected_class_id,
                                "subject_name": s_name,
                                "subject_code": s_code,
                            }
                            db = _db()
                            saved_to_supabase = False
                            if db and inst_id:
                                try:
                                    db.table("subjects").insert(record).execute()
                                    saved_to_supabase = True
                                    st.success(f"✅ {s_name} added.")
                                except Exception as e:
                                    st.exception(e)
                            else:
                                st.session_state.subjects.append(record)
                                st.warning("Subject saved locally (Supabase not connected).")

                            st.rerun()
        subjects = get_subjects()
        if subjects:
            st.dataframe(pd.DataFrame([{"Subject":s.get("subject_name","") ,
                          "Code":s.get("subject_code","") ,
                          "Class ID":s.get("class_id","")} for s in subjects]),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No subjects yet.")
