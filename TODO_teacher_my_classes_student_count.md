# TODO — Teacher My Classes student count fix

- [ ] Implement robust student counting for each assigned class on teacher_dashboard.py:
  - [ ] Count active students by students.class_id == class.id
  - [ ] If empty/zero, fallback count by students.class_name + students.section matching class
  - [ ] If still zero, count unique students via subject_enrollments joined to students for the selected subject
  - [ ] Ensure count is integer and unique student IDs only
- [ ] Remove raw debug UI outputs from _classes page (remove Developer Debug expander blocks)
- [ ] If no students found for a class, show clear message:
  "No students linked to this class yet. Ask admin to assign students or share subject join code."
- [ ] Fix join link for production:
  - [ ] Use APP_BASE_URL (already referenced in code) and remove localhost fallback where applicable
  - [ ] Ensure link becomes `${APP_BASE_URL}/?join-code=...`
- [ ] Quick sanity check by running Streamlit / lint if available

