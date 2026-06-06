# TODO - Manual Attendance UX fix (Streamlit rerun)

- [ ] Replace teacher manual attendance UI in `sc_final/src/screens/teacher_dashboard.py` to use a single `st.form` with Class + Subject + Date.
- [ ] Ensure students list + marking UI only appears *after* clicking **Load Students**.
- [ ] Persist selected `class_id`, `subject_id`, `date` in `st.session_state` after Load Students.
- [ ] Remove step-by-step expanding UI/any debug-only expanders from the production flow.
- [ ] Ensure empty states match requirements (no class / no subject / no students).
- [ ] Add bulk actions (Mark all Present/Absent), per-student status radios, and **Save Attendance**.
- [ ] Use `st.cache_data` for class/subject/student fetches to improve speed.
- [ ] Confirm dropdown text visibility; rely on global CSS, and only add inline CSS if missing.
- [ ] Run a quick Streamlit smoke check / lint check.

