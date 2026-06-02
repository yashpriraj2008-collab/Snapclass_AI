-- SnapClass AI - Production constraints and indexes
--
-- Safe intent:
-- - Does not drop tables.
-- - Does not delete user data.
-- - Adds missing columns only when needed.
-- - Adds NOT VALID checks so existing bad rows do not block deployment; validate
--   after cleaning data.
--
-- Before running, check for duplicate rows that would block unique indexes.

-- Helpful duplicate checks.
select 'duplicate_students_email' as check_name, lower(email) as value, count(*)
from public.students
where email is not null and btrim(email) <> ''
group by lower(email)
having count(*) > 1;

select 'duplicate_teachers_email' as check_name, lower(email) as value, count(*)
from public.teachers
where email is not null and btrim(email) <> ''
group by lower(email)
having count(*) > 1;

select 'duplicate_subject_join_codes' as check_name, join_code as value, count(*)
from public.subject_join_codes
where join_code is not null and btrim(join_code) <> ''
group by join_code
having count(*) > 1;

-- Columns expected by production flows.
alter table public.students add column if not exists status text default 'active';
alter table public.teachers add column if not exists status text default 'active';
alter table public.subject_enrollments add column if not exists status text default 'active';
alter table public.attendance_sessions add column if not exists mode text default 'manual';
alter table public.attendance_records add column if not exists attendance_date date;
alter table public.attendance_records add column if not exists class_id uuid;
alter table public.attendance_records add column if not exists subject_id uuid;
alter table public.attendance_records add column if not exists marked_by uuid;

-- Unique indexes (guarded by column existence).
do $$
begin
  -- public.user_profiles
  if exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='user_profiles' and column_name='user_id'
  ) then
    execute 'create unique index if not exists ux_user_profiles_user_id on public.user_profiles(user_id)';
  end if;

  if exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='user_profiles' and column_name='email'
  ) then
    execute 'create unique index if not exists ux_user_profiles_email_ci '
         || 'on public.user_profiles(lower(email)) '
         || 'where email is not null and btrim(email) <> '''; 
  end if;

  -- public.teachers
  if exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='teachers' and column_name='user_id'
  ) then
    execute 'create unique index if not exists ux_teachers_user_id on public.teachers(user_id)';
  end if;

  if exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='teachers' and column_name='email'
  ) then
    execute 'create unique index if not exists ux_teachers_email_ci '
         || 'on public.teachers(lower(email)) '
         || 'where email is not null and btrim(email) <> '''; 
  end if;

  -- public.students
  if exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='students' and column_name='user_id'
  ) then
    execute 'create unique index if not exists ux_students_user_id on public.students(user_id)';
  end if;

  if exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='students' and column_name='email'
  ) then
    execute 'create unique index if not exists ux_students_email_ci '
         || 'on public.students(lower(email)) '
         || 'where email is not null and btrim(email) <> '''; 
  end if;

  -- teacher_assignments (teacher_id, class_id, subject_id)
  if exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='teacher_assignments' and column_name='teacher_id'
  ) and exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='teacher_assignments' and column_name='class_id'
  ) and exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='teacher_assignments' and column_name='subject_id'
  ) then
    execute 'create unique index if not exists ux_teacher_assignments_teacher_class_subject '
         || 'on public.teacher_assignments(teacher_id, class_id, subject_id)';
  end if;

  -- subject_enrollments (student_id, subject_id)
  if exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='subject_enrollments' and column_name='student_id'
  ) and exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='subject_enrollments' and column_name='subject_id'
  ) then
    execute 'create unique index if not exists ux_subject_enrollments_student_subject '
         || 'on public.subject_enrollments(student_id, subject_id)';
  end if;

  -- attendance unique for (session_id, student_id)
  if exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='attendance_records' and column_name='session_id'
  ) and exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='attendance_records' and column_name='student_id'
  ) then
    execute 'create unique index if not exists ux_attendance_records_session_student '
         || 'on public.attendance_records(session_id, student_id)';
  end if;

  -- attendance_sessions lookup
  if exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='attendance_sessions' and column_name='teacher_id'
  ) and exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='attendance_sessions' and column_name='class_id'
  ) and exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='attendance_sessions' and column_name='subject_id'
  ) and exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='attendance_sessions' and column_name='date'
  ) then
    execute 'create unique index if not exists ux_attendance_sessions_teacher_class_subject_date '
         || 'on public.attendance_sessions(teacher_id, class_id, subject_id, date)';
  end if;

  -- subject_join_codes join_code
  if exists (
    select 1 from information_schema.columns where table_schema='public' and table_name='subject_join_codes' and column_name='join_code'
  ) then
    execute 'create unique index if not exists ux_subject_join_codes_join_code '
         || 'on public.subject_join_codes(join_code) '
         || 'where join_code is not null and btrim(join_code) <> '''; 
  end if;
end$$;

-- (non-unique indexes)


-- Lookup indexes (guarded).
do $$
begin
  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='students' and column_name='email') then
    execute 'create index if not exists idx_students_email on public.students(lower(email)) where email is not null';
  end if;
  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='teachers' and column_name='email') then
    execute 'create index if not exists idx_teachers_email on public.teachers(lower(email)) where email is not null';
  end if;
  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='teacher_assignments' and column_name='teacher_id') then
    execute 'create index if not exists idx_teacher_assignments_teacher_id on public.teacher_assignments(teacher_id)';
  end if;
  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='teacher_assignments' and column_name='class_id') then
    execute 'create index if not exists idx_teacher_assignments_class_id on public.teacher_assignments(class_id)';
  end if;
  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='teacher_assignments' and column_name='subject_id') then
    execute 'create index if not exists idx_teacher_assignments_subject_id on public.teacher_assignments(subject_id)';
  end if;
  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='subject_enrollments' and column_name='student_id') then
    execute 'create index if not exists idx_subject_enrollments_student_id on public.subject_enrollments(student_id)';
  end if;
  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='subject_enrollments' and column_name='subject_id') then
    execute 'create index if not exists idx_subject_enrollments_subject_id on public.subject_enrollments(subject_id)';
  end if;
  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='attendance_records' and column_name='student_id') then
    execute 'create index if not exists idx_attendance_records_student_id on public.attendance_records(student_id)';
  end if;

  -- attendance lookup for class/subject/date/session/student
  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='attendance_sessions' and column_name='teacher_id')
     and exists (select 1 from information_schema.columns where table_schema='public' and table_name='attendance_sessions' and column_name='class_id')
     and exists (select 1 from information_schema.columns where table_schema='public' and table_name='attendance_sessions' and column_name='subject_id')
     and exists (select 1 from information_schema.columns where table_schema='public' and table_name='attendance_sessions' and column_name='date') then
    execute 'create index if not exists idx_attendance_sessions_scope_date on public.attendance_sessions(teacher_id, class_id, subject_id, date)';
  end if;

  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='attendance_records' and column_name='session_id')
     and exists (select 1 from information_schema.columns where table_schema='public' and table_name='attendance_records' and column_name='class_id') then
    execute 'create index if not exists idx_attendance_records_session_class on public.attendance_records(session_id, class_id)';
  end if;

  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='attendance_records' and column_name='subject_id') then
    execute 'create index if not exists idx_attendance_records_session_subject on public.attendance_records(session_id, subject_id)';
  end if;

  if exists (select 1 from information_schema.columns where table_schema='public' and table_name='attendance_records' and column_name='attendance_date') then
    execute 'create index if not exists idx_attendance_records_date on public.attendance_records(attendance_date)';
  end if;
end$$;


-- Check constraints. NOT VALID keeps this safe for existing data; validate later.
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'attendance_records_status_check_prod'
      and conrelid = 'public.attendance_records'::regclass
  ) then
    alter table public.attendance_records
      add constraint attendance_records_status_check_prod
      check (status in ('present','absent','late')) not valid;
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'students_status_check_prod'
      and conrelid = 'public.students'::regclass
  ) then
    alter table public.students
      add constraint students_status_check_prod
      check (status in ('active','inactive')) not valid;
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'teachers_status_check_prod'
      and conrelid = 'public.teachers'::regclass
  ) then
    alter table public.teachers
      add constraint teachers_status_check_prod
      check (status in ('active','inactive')) not valid;
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'subject_enrollments_status_check_prod'
      and conrelid = 'public.subject_enrollments'::regclass
  ) then
    alter table public.subject_enrollments
      add constraint subject_enrollments_status_check_prod
      check (status in ('active','inactive')) not valid;
  end if;
end $$;
