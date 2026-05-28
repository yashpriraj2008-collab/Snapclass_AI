# TODO — SnapClass AI Institute Hierarchy + Assignment Flow

## Phase 1 (Admin control)
- [ ] Inspect/align DB schema for: institutes/classes/subjects/teachers/students + teacher_assignments + student_subjects.
- [ ] Add/ensure `teacher_assignments` table exists.
- [ ] Create Admin page: **Teacher Assignments** (create assignments with class_teacher / subject_teacher).
- [ ] Update `teacher_dashboard.py` to fetch only assigned classes/subjects (no “all classes”).

## Phase 2 (Teacher → Student management)
- [ ] Add Class Teacher-only student add UI (restricted to assigned class).
- [ ] Generate admission_no.
- [ ] Create Supabase Auth user with temporary password and store mapping in `user_profiles`.
- [ ] Auto-enroll student into all subjects for that class via `student_subjects`.

## Phase 3 (Attendance permission)
- [ ] Implement/align `attendance_sessions` + `attendance_records` persistence (or migrate existing attendance writes).
- [ ] Save attendance with: session_id, teacher_id, class_id, subject_id, student_id, status.
- [ ] Enforce teacher can only mark assigned class/subject.

## Phase 4 (Student login + portal)
- [ ] Ensure student login uses admission_no + password (Supabase Auth).
- [ ] Update Student portal to show only enrolled subjects + own attendance.
- [ ] Disable join-code self enrollment for MVP.

## Verification
- [ ] Run: `python -m compileall app.py src`
- [ ] Manual flow test: Admin → assignments → class teacher adds student → subject teacher marks attendance → student sees only own records.

