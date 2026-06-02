# SnapClass AI — Phase 1 Demo-Ready QA Test Plan

## Scope
Phase 1 user flows only:
- Teacher login → assigned class/subject → students → manual attendance → save to Supabase
- Student login → My Subjects → Attendance History → Reports/Analytics (using saved attendance)

## Required Pre-Checks
1. Run:
   - `python -m compileall app.py src`
   - `pip check`
   - `streamlit run app.py --server.port 8507`
2. Confirm Supabase secrets:
   - `.streamlit/secrets.toml` contains `SUPABASE_URL` and `SUPABASE_ANON_KEY`
   - No service_role key usage

## Test Accounts (DEMO)
- Teacher: `teacher.demo@test.com` (see `DEMO_ACCOUNTS.md`)
- Student: `student.demo@test.com` (see `DEMO_ACCOUNTS.md`)

## Teacher Flow Tests
1. Login as teacher.demo@test.com.
2. Verify `session_state` contains:
   - `auth_user_id`
   - `user_id`
   - `user_email`
   - `email`
   - `user_name`
   - `role`
   - `institute_id`
   - `teacher_id`
   - `logged_in`
   - `portal`
3. Verify Manual Attendance shows:
   - Class: **12-A**
   - Subject: **Physics**
   - Student: **Demo Student**
4. Mark Demo Student as **Present**.
5. Save attendance.
6. Verify Supabase writes:
   - `attendance_sessions` has a **new row** for the class+subject+date
   - `attendance_records` has **new rows** for the students

## Student Flow Tests
1. Logout and login as student.demo@test.com.
2. Verify:
   - **My Subjects** includes Physics
   - **Attendance History** shows the saved attendance entry
   - **Reports** shows the same saved attendance
   - Analytics reflects real saved attendance data (not demo constants)

## P0 Blocker Criteria (Fix only these)
- Missing `teacher_id` after teacher login
- Wrong teacher assignment lookup (teacher sees wrong classes/subjects)
- Students not loading under Manual Attendance
- Attendance not saving (no new Supabase rows)
- Student history not showing saved attendance
- Raw HTML visible in UI
- Hidden/unexpected errors
- Supabase RLS recursion errors

## Empty State Criteria
If any dataset is missing:
- show a clear `st.info()`/`st.warning()` empty state
- do not display stack traces
- no blank cards

## Exit Criteria
- All required tests pass
- No terminal/runtime errors on the critical path
- Manual attendance and student history are consistent

