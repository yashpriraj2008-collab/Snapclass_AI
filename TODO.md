# TODO - SnapClass AI Debug & Fix (Classes/Subjects/Reports/AI Attendance)

## Step 1 — Codebase query audit
- [ ] Identify all Supabase reads/writes for: classes, subjects, reports, attendance, attendance_records, institutes
- [ ] Identify institute filtering logic per page

## Step 2 — Add debug logs to every Supabase request
- [ ] Implement central Supabase request logger (table/rpc/auth) OR wrap client calls
- [ ] Add console/st.write logs: query payload, returned data keys, and error objects

## Step 3 — Detect empty/null/permission denied responses
- [ ] Categorize every query result as: null/undefined/[]/permission denied
- [ ] Ensure all catches log error + query context

## Step 4 — Verify institute filtering
- [ ] For Classes, Subjects, Reports, log: user id, role, institute id
- [ ] Compare institute_id used by UI vs institute_id stored on rows

## Step 5 — RLS policy verification and missing policy generation
- [ ] Check SELECT access on: classes, subjects, students, teachers, institutes, attendance, attendance_records
- [ ] Generate/patch missing RLS policies for institute scoping

## Step 6 — Relationship verification
- [ ] Verify joins/foreign keys expectations:
  - [ ] classes.id
  - [ ] subjects.class_id
  - [ ] students.class_id
  - [ ] teachers.institute_id
  - [ ] subjects.institute_id

## Step 7 — React/Streamlit rendering hardening
- [ ] Add Loading/Empty/Error states instead of blank tables
- [ ] Add safe guards against missing fields

## Step 8 — Fix Reports module
- [ ] Trace report generation: attendance → attendance_sessions → attendance_records → students/classes/subjects
- [ ] Fix mapping where data becomes empty

## Step 9 — AI Attendance mapping fix
- [ ] Ensure AI Attendance writes consistent (class_id, subject_id, institute_id)
- [ ] Ensure sessionization uses same keys as report queries

## Step 10 — Verification
- [ ] Verify Classes page shows live rows
- [ ] Verify Subjects page shows live rows
- [ ] Verify Reports page shows non-empty table
- [ ] Verify AI Attendance can mark and is visible in Reports

