-- SnapClass AI - Production schema/data preflight
--
-- Run this BEFORE removing demo policies or applying production RLS.
-- This script is intentionally non-destructive: it adds missing columns,
-- restores the core attendance FK used by PostgREST embeds, and returns
-- checks that must be green before production RLS.

create extension if not exists pgcrypto;

alter table public.user_profiles
  add column if not exists status text default 'active';

alter table public.attendance_sessions
  add column if not exists institute_id uuid references public.institutes(id) on delete set null,
  add column if not exists teacher_id uuid references public.teachers(id) on delete set null,
  add column if not exists class_id uuid references public.classes(id) on delete set null,
  add column if not exists subject_id uuid references public.subjects(id) on delete set null,
  add column if not exists mode text default 'manual',
  add column if not exists updated_at timestamptz default now();

alter table public.attendance_records
  add column if not exists marked_by uuid,
  add column if not exists marked_at timestamptz default now(),
  add column if not exists attendance_date date,
  add column if not exists class_id uuid references public.classes(id) on delete set null,
  add column if not exists subject_id uuid references public.subjects(id) on delete set null,
  add column if not exists updated_at timestamptz default now();

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'attendance_records_session_id_fkey'
      and conrelid = 'public.attendance_records'::regclass
  ) then
    alter table public.attendance_records
      add constraint attendance_records_session_id_fkey
      foreign key (session_id)
      references public.attendance_sessions(id)
      on delete cascade;
  end if;
end $$;

create index if not exists idx_user_profiles_email on public.user_profiles(email);
create index if not exists idx_user_profiles_role on public.user_profiles(role);
create index if not exists idx_user_profiles_institute_id on public.user_profiles(institute_id);
create index if not exists idx_attendance_records_session_id on public.attendance_records(session_id);
create index if not exists idx_attendance_records_student_id on public.attendance_records(student_id);
create index if not exists idx_attendance_sessions_teacher_scope
  on public.attendance_sessions(teacher_id, class_id, subject_id);

-- Preflight report. Any "missing_*" rows must be fixed before production RLS.
select 'missing_demo_founder_profile' as check_name, count(*) as issue_count
from public.user_profiles
where lower(email) = 'founder@snapclass.ai' and role = 'founder'
having count(*) = 0
union all
select 'missing_demo_teacher_profile', count(*)
from public.user_profiles
where lower(email) = 'teacher.demo@test.com' and role = 'teacher' and institute_id is not null
having count(*) = 0
union all
select 'missing_demo_student_profile', count(*)
from public.user_profiles
where lower(email) = 'student.demo@test.com' and role = 'student' and institute_id is not null
having count(*) = 0
union all
select 'teacher_email_not_mapped', count(*)
from public.teachers
where lower(email) = 'teacher.demo@test.com'
having count(*) = 0
union all
select 'student_email_not_mapped', count(*)
from public.students
where lower(email) = 'student.demo@test.com'
having count(*) = 0
union all
select 'missing_teacher_assignment', count(*)
from public.teacher_assignments ta
join public.teachers t on t.id = ta.teacher_id
where lower(t.email) = 'teacher.demo@test.com'
having count(*) = 0
union all
select 'missing_attendance_fk', count(*)
from pg_constraint
where conname = 'attendance_records_session_id_fkey'
  and conrelid = 'public.attendance_records'::regclass
having count(*) = 0;

