-- SnapClass AI - Phase 2 Production preflight checks
-- Run on: staging first
-- Non-destructive: SELECT-only, adds no constraints/policies.

-- 0) List all public tables
select 'public_tables' as check_name, table_name
from information_schema.tables
where table_schema = 'public'
  and table_type = 'BASE TABLE'
order by table_name;

-- 1) Identity mapping: user_profiles ↔ auth.users
-- user_profiles.user_id MUST map to auth.users.id
select 'user_profiles_user_id_missing_in_auth' as check_name,
       count(*) as issue_count
from public.user_profiles up
where up.user_id is not null
  and not exists (
    select 1 from auth.users u where u.id = up.user_id
  );

select 'user_profiles_null_user_id' as check_name,
       count(*) as issue_count
from public.user_profiles up
where up.user_id is null;

select 'user_profiles_email_not_unique_ci' as check_name,
       count(*) as issue_count
from (
  select lower(email) as email_norm, count(*) c
  from public.user_profiles
  where email is not null
  group by lower(email)
) x
where x.c > 1;

-- 2) Identity mapping: teachers ↔ auth.users
select 'teachers_user_id_missing_in_auth' as check_name,
       count(*) as issue_count
from public.teachers t
where t.user_id is not null
  and not exists (
    select 1 from auth.users u where u.id = t.user_id
  );

select 'teachers_null_user_id' as check_name,
       count(*) as issue_count
from public.teachers t
where t.user_id is null;

select 'teachers_email_not_unique_ci' as check_name,
       count(*) as issue_count
from (
  select lower(email) as email_norm, count(*) c
  from public.teachers
  where email is not null
  group by lower(email)
) x
where x.c > 1;

-- 3) Identity mapping: students ↔ auth.users
select 'students_user_id_missing_in_auth' as check_name,
       count(*) as issue_count
from public.students s
where s.user_id is not null
  and not exists (
    select 1 from auth.users u where u.id = s.user_id
  );

select 'students_null_user_id' as check_name,
       count(*) as issue_count
from public.students s
where s.user_id is null;

select 'students_email_not_unique_ci' as check_name,
       count(*) as issue_count
from (
  select lower(email) as email_norm, count(*) c
  from public.students
  where email is not null
  group by lower(email)
) x
where x.c > 1;

-- 4) teacher_assignments mapping integrity
-- teacher_assignments.teacher_id must exist in teachers
select 'teacher_assignments_teacher_id_missing' as check_name,
       count(*) as issue_count
from public.teacher_assignments ta
where not exists (select 1 from public.teachers t where t.id = ta.teacher_id);

-- teacher_assignments.class_id must exist in classes
select 'teacher_assignments_class_id_missing' as check_name,
       count(*) as issue_count
from public.teacher_assignments ta
where ta.class_id is not null
  and not exists (select 1 from public.classes c where c.id = ta.class_id);

-- teacher_assignments.subject_id must exist in subjects
select 'teacher_assignments_subject_id_missing' as check_name,
       count(*) as issue_count
from public.teacher_assignments ta
where ta.subject_id is not null
  and not exists (select 1 from public.subjects s where s.id = ta.subject_id);

-- 5) subject_enrollments mapping integrity
select 'subject_enrollments_student_id_missing' as check_name,
       count(*) as issue_count
from public.subject_enrollments se
where not exists (select 1 from public.students s where s.id = se.student_id);

select 'subject_enrollments_subject_id_missing' as check_name,
       count(*) as issue_count
from public.subject_enrollments se
where not exists (select 1 from public.subjects s where s.id = se.subject_id);

-- 6) attendance_sessions + attendance_records mapping integrity
-- attendance_records.session_id must exist in attendance_sessions
select 'attendance_records_session_id_missing' as check_name,
       count(*) as issue_count
from public.attendance_records ar
where not exists (
  select 1 from public.attendance_sessions s where s.id = ar.session_id
);

-- attendance_sessions.teacher_id (if present) must exist in teachers
select 'attendance_sessions_teacher_id_missing' as check_name,
       count(*) as issue_count
from public.attendance_sessions s
where s.teacher_id is not null
  and not exists (select 1 from public.teachers t where t.id = s.teacher_id);

-- attendance_sessions.class_id (if present) must exist in classes
select 'attendance_sessions_class_id_missing' as check_name,
       count(*) as issue_count
from public.attendance_sessions s
where s.class_id is not null
  and not exists (select 1 from public.classes c where c.id = s.class_id);

-- attendance_sessions.subject_id (if present) must exist in subjects
select 'attendance_sessions_subject_id_missing' as check_name,
       count(*) as issue_count
from public.attendance_sessions s
where s.subject_id is not null
  and not exists (select 1 from public.subjects sub where sub.id = s.subject_id);

-- attendance_records.student_id must exist in students
select 'attendance_records_student_id_missing' as check_name,
       count(*) as issue_count
from public.attendance_records ar
where not exists (select 1 from public.students s where s.id = ar.student_id);

-- 7) Current pg_policies (only for visibility)
select 'current_pg_policies' as check_name,
       schemaname,
       tablename,
       policyname,
       permissive,
       roles,
       cmd,
       qual,
       with_check
from pg_policies
where schemaname = 'public'
order by tablename, policyname;

