-- Phase 3 preflight checks
-- Purpose: Verify schema, identity mappings, FK/assignment/enrollment relationships,
-- and identify existing demo/open policies to avoid breaking production.

-- IMPORTANT:
-- Run on staging first.

set check_function_bodies = false;

-- 1) Quick table existence / column checks
-- (Skip failing parts by using IF EXISTS checks.)

-- user_profiles
do $$ begin
  if to_regclass('public.user_profiles') is null then
    raise notice 'Table public.user_profiles not found (expected in Phase 3).';
  end if;
end $$;

-- institutes
do $$ begin
  if to_regclass('public.institutes') is null then
    raise notice 'Table public.institutes not found (expected in Phase 3).';
  end if;
end $$;

-- teachers
do $$ begin
  if to_regclass('public.teachers') is null then
    raise notice 'Table public.teachers not found (expected in Phase 3).';
  end if;
end $$;

-- students
do $$ begin
  if to_regclass('public.students') is null then
    raise notice 'Table public.students not found (expected in Phase 3).';
  end if;
end $$;

-- classes
do $$ begin
  if to_regclass('public.classes') is null then
    raise notice 'Table public.classes not found (expected in Phase 3).';
  end if;
end $$;

-- subjects
do $$ begin
  if to_regclass('public.subjects') is null then
    raise notice 'Table public.subjects not found (expected in Phase 3).';
  end if;
end $$;

-- join/assignment/enrollment
do $$ begin
  if to_regclass('public.teacher_assignments') is null then
    raise notice 'Table public.teacher_assignments not found (expected in Phase 3).';
  end if;
end $$;

do $$ begin
  if to_regclass('public.subject_enrollments') is null then
    raise notice 'Table public.subject_enrollments not found (expected in Phase 3).';
  end if;
end $$;

do $$ begin
  if to_regclass('public.subject_join_codes') is null then
    raise notice 'Table public.subject_join_codes not found (expected in Phase 3).';
  end if;
end $$;

-- attendance
do $$ begin
  if to_regclass('public.attendance_sessions') is null then
    raise notice 'Table public.attendance_sessions not found (expected in Phase 3).';
  end if;
end $$;

do $$ begin
  if to_regclass('public.attendance_records') is null then
    raise notice 'Table public.attendance_records not found (expected in Phase 3).';
  end if;
end $$;

-- face embeddings
do $$ begin
  if to_regclass('public.face_embeddings') is null then
    raise notice 'Table public.face_embeddings not found (expected in Phase 3).';
  end if;
end $$;

-- 2) Identity mapping sanity checks
-- Expectation: teachers.user_id -> auth.users.id
-- Expectation: students.user_id/user_id (or user_id) -> auth.users.id

-- teachers mapping
do $$ begin
  if to_regclass('public.teachers') is not null then
    if not exists (
      select 1 from information_schema.columns
      where table_schema='public' and table_name='teachers' and column_name='user_id'
    ) then
      raise notice 'teachers.user_id column missing.';
    end if;
  end if;
end $$;

-- students mapping
do $$ begin
  if to_regclass('public.students') is not null then
    if not exists (
      select 1 from information_schema.columns
      where table_schema='public' and table_name='students' and column_name='user_id'
    ) then
      raise notice 'students.user_id column missing.';
    end if;
  end if;
end $$;

-- 3) Existing pg_policies - list potentially demo/open policies
-- Review output before dropping anything.

select
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
from pg_policies
where
  (policyname ilike '%demo%' or policyname ilike 'phase1_%' or policyname ilike '%open%')
order by schemaname, tablename, policyname;

-- 4) FK column presence checks (used by Phase 3 RLS and indexes)

-- Minimal required columns per table
-- teachers: teacher_id via teachers.id, plus user_id, institute_id
-- students: student_id via students.id, plus user_id, institute_id
-- classes: institute_id
-- subjects: institute_id, class_id
-- teacher_assignments: teacher_id, class_id, subject_id
-- subject_enrollments: student_id, subject_id
-- attendance_sessions: teacher_id, subject_id
-- attendance_records: session_id, student_id
-- face_embeddings: user_id, student_id

-- Print column existence notes only.

do $$ begin
  if to_regclass('public.teacher_assignments') is not null then
    perform 1 from information_schema.columns
      where table_schema='public' and table_name='teacher_assignments' and column_name='teacher_id';
    if not exists (select 1 from information_schema.columns where table_schema='public' and table_name='teacher_assignments' and column_name='teacher_id') then
      raise notice 'teacher_assignments.teacher_id missing';
    end if;
    if not exists (select 1 from information_schema.columns where table_schema='public' and table_name='teacher_assignments' and column_name='class_id') then
      raise notice 'teacher_assignments.class_id missing';
    end if;
    if not exists (select 1 from information_schema.columns where table_schema='public' and table_name='teacher_assignments' and column_name='subject_id') then
      raise notice 'teacher_assignments.subject_id missing';
    end if;
  end if;
end $$;

-- More checks can be added after preflight output is observed.

raise notice 'Phase 3 preflight completed. Review notices and pg_policies query output.';

