-- Phase 3 private RLS helper functions
-- Create a private schema and security definer helpers.
-- NOTE: Functions must be stable and security-definer.

-- Run on staging first.

begin;

create schema if not exists private;

-- Helper: current role
-- Assumes user role is stored in public.user_profiles.role
-- If your schema stores roles elsewhere, adjust.

create or replace function private.current_user_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(
    (select up.role from public.user_profiles up where up.user_id = auth.uid() limit 1),
    'student'
  )
$$;

-- Helper: current institute_id
create or replace function private.current_institute_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select up.institute_id
  from public.user_profiles up
  where up.user_id = auth.uid()
  limit 1
$$;

-- Helper: current teacher_id
create or replace function private.current_teacher_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select t.id
  from public.teachers t
  where t.user_id = auth.uid()
  limit 1
$$;

-- Helper: current student_id
create or replace function private.current_student_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select s.id
  from public.students s
  where s.user_id = auth.uid()
  limit 1
$$;

-- Founder check
create or replace function private.is_founder()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select (private.current_user_role() in ('founder','hq','super_admin'))
$$;

-- Institute admin check
create or replace function private.is_institute_admin(target_institute uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select private.current_user_role() in ('admin','institute_admin')
  and private.current_institute_id() = target_institute
$$;

-- Teacher can access class
create or replace function private.teacher_can_access_class(target_class_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists(
    select 1
    from public.teacher_assignments ta
    where ta.teacher_id = private.current_teacher_id()
      and ta.class_id = target_class_id
  )
$$;

-- Teacher can access subject
create or replace function private.teacher_can_access_subject(target_subject_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists(
    select 1
    from public.teacher_assignments ta
    where ta.teacher_id = private.current_teacher_id()
      and ta.subject_id = target_subject_id
  )
$$;

-- Student enrolled in subject
create or replace function private.student_enrolled_in_subject(target_subject_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists(
    select 1
    from public.subject_enrollments se
    where se.student_id = private.current_student_id()
      and se.subject_id = target_subject_id
  )
$$;

commit;


