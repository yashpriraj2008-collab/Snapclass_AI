-- SnapClass AI — DEMO seed data
-- Runs in Supabase SQL editor.
-- This seed is intentionally minimal for Phase-1 demo QA.

-- NOTE:
-- 1) If you already have tables + RLS policies enabled, ensure the executing role
--    can insert demo rows (use a service-role only in your SQL editor).
-- 2) The app primarily uses public.user_profiles, public.teachers, public.students,
--    public.classes, public.subjects, public.subject_enrollments (via join codes),
--    and attendance_sessions/attendance_records.

-- Create a demo institute
insert into public.institutes (id, name, city)
values ('inst_demo_1', 'SnapClass AI Demo Institute', 'Demo City')
on conflict (id) do nothing;

-- Demo teacher profile/auth user_id placeholder
-- Replace these IDs if your auth.users IDs differ.
-- (If you rely on auth, you must use the actual auth.users.id.)

-- DEMO TEACHER
insert into public.user_profiles (id, email, full_name, role, institute_id, subject, roll_no, class_name, user_id, status)
values (
  'auth_teacher_demo_1',
  'teacher.demo@test.com',
  'Demo Teacher',
  'teacher',
  'inst_demo_1',
  null,
  null,
  null,
  'auth_teacher_demo_1',
  'active'
)
on conflict (id) do nothing;

insert into public.teachers (id, user_id, email, name, institute_id, subject)
values (
  'teacher_demo_row_1',
  'auth_teacher_demo_1',
  'teacher.demo@test.com',
  'Demo Teacher',
  'inst_demo_1',
  'Physics'
)
on conflict (id) do nothing;

-- DEMO STUDENT
insert into public.user_profiles (id, email, full_name, role, institute_id, subject, roll_no, class_name, user_id, status)
values (
  'auth_student_demo_1',
  'student.demo@test.com',
  'Demo Student',
  'student',
  'inst_demo_1',
  null,
  'SC001',
  '12-A',
  'auth_student_demo_1',
  'active'
)
on conflict (id) do nothing;

insert into public.students (id, email, name, roll_no, class_name, section, class_id, institute_id, status)
values (
  'student_demo_row_1',
  'student.demo@test.com',
  'Demo Student',
  'SC001',
  '12-A',
  'A',
  null,
  'inst_demo_1',
  'active'
)
on conflict (id) do nothing;

-- Demo class 12-A
insert into public.classes (id, name, section, grade, class_name, time, students, institute_id)
values (
  'class_demo_12a',
  '12',
  'A',
  '12',
  '12-A',
  '10:00 AM',
  null,
  'inst_demo_1'
)
on conflict (id) do nothing;

-- Attach student to class (if schema expects class_id instead of class_name)
update public.students
set class_id = 'class_demo_12a'
where id = 'student_demo_row_1';

-- Demo subject Physics for class 12-A
insert into public.subjects (id, name, subject_name, code, class_id, class_name, teacher_id, institute_id, teacher_email, created_at)
values (
  'subject_demo_physics_1',
  'Physics',
  'Physics',
  'PHYS-101',
  'class_demo_12a',
  '12-A',
  'teacher_demo_row_1',
  'inst_demo_1',
  'teacher.demo@test.com',
  now()
)
on conflict (id) do nothing;

-- Ensure teacher assignments exist for teacher_service lookup
-- If your schema uses a join table like teacher_assignments, insert accordingly.
-- The app calls get_teacher_assignments(supabase, teacher_id) (see src/services/teacher_service.py).
-- Add rows below if that table exists.

-- Try common name: public.teacher_assignments
insert into public.teacher_assignments (teacher_id, class_id, subject_id, institute_id, created_at)
values ('teacher_demo_row_1', 'class_demo_12a', 'subject_demo_physics_1', 'inst_demo_1', now())
on conflict do nothing;

-- Student enrollment for Physics (for My Subjects)
insert into public.subject_enrollments (student_id, subject_id, join_code, status)
values (
  'student_demo_row_1',
  'subject_demo_physics_1',
  'SC-DEMO',
  'active'
)
on conflict do nothing;

-- Note: attendance_sessions/attendance_records are created when teacher marks attendance.

