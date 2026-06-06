-- SnapClass AI performance indexes.
-- Run in Supabase SQL Editor after confirming these tables exist.

create index if not exists idx_students_lower_email
on public.students (lower(email));

create index if not exists idx_students_class_id
on public.students (class_id);

create index if not exists idx_teachers_lower_email
on public.teachers (lower(email));

create index if not exists idx_user_profiles_lower_email
on public.user_profiles (lower(email));

create index if not exists idx_subjects_class_id
on public.subjects (class_id);

create index if not exists idx_subjects_subject_code
on public.subjects (subject_code);

create index if not exists idx_subject_enrollments_student_id
on public.subject_enrollments (student_id);

create index if not exists idx_subject_enrollments_subject_id
on public.subject_enrollments (subject_id);

create index if not exists idx_subject_join_codes_join_code
on public.subject_join_codes (join_code);

create index if not exists idx_teacher_assignments_teacher_id
on public.teacher_assignments (teacher_id);

create index if not exists idx_teacher_assignments_class_id
on public.teacher_assignments (class_id);

create index if not exists idx_attendance_records_student_id
on public.attendance_records (student_id);

create index if not exists idx_attendance_records_session_id
on public.attendance_records (session_id);

create index if not exists idx_attendance_sessions_class_id
on public.attendance_sessions (class_id);

create index if not exists idx_attendance_sessions_subject_id
on public.attendance_sessions (subject_id);

create index if not exists idx_attendance_sessions_date
on public.attendance_sessions (date);
