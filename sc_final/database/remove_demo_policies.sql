-- SnapClass AI — Remove demo allow-all RLS policies (safe)
--
-- IMPORTANT:
-- - This file ONLY removes demo-style allow-all policies.
-- - It does NOT change production policies.
-- - Run in Supabase SQL Editor.
--
-- Known demo policies in this repo:
-- - sc_final/database/fix_core_attendance_rls.sql
--     attendance_sessions_*_all
--     attendance_records_*_all
--
-- Your task also mentioned potential names:
-- - demo_allow_all_teacher_assignments
-- - demo_allow_all_attendance_sessions
-- - demo_allow_all_attendance_records
--
-- This script drops them IF they exist.

-- attendance_sessions allow-all (demo)
DROP POLICY IF EXISTS allow_all ON public.attendance_sessions;
DROP POLICY IF EXISTS attendance_sessions_select_all ON public.attendance_sessions;
DROP POLICY IF EXISTS attendance_sessions_insert_all ON public.attendance_sessions;
DROP POLICY IF EXISTS attendance_sessions_update_all ON public.attendance_sessions;
DROP POLICY IF EXISTS attendance_sessions_delete_all ON public.attendance_sessions;

-- attendance_records allow-all (demo)
DROP POLICY IF EXISTS allow_all ON public.attendance_records;
DROP POLICY IF EXISTS attendance_records_select_all ON public.attendance_records;
DROP POLICY IF EXISTS attendance_records_insert_all ON public.attendance_records;
DROP POLICY IF EXISTS attendance_records_update_all ON public.attendance_records;
DROP POLICY IF EXISTS attendance_records_delete_all ON public.attendance_records;

-- Named demo policies (if your DB uses these exact names)
DROP POLICY IF EXISTS allow_all ON public.institutes;
DROP POLICY IF EXISTS allow_all ON public.school_codes;
DROP POLICY IF EXISTS allow_all ON public.teachers;
DROP POLICY IF EXISTS allow_all ON public.students;
DROP POLICY IF EXISTS allow_all ON public.classes;
DROP POLICY IF EXISTS allow_all ON public.subjects;
DROP POLICY IF EXISTS allow_all ON public.teacher_assignments;
DROP POLICY IF EXISTS allow_all ON public.subject_join_codes;
DROP POLICY IF EXISTS allow_all ON public.subject_enrollments;
DROP POLICY IF EXISTS allow_all ON public.user_profiles;
DROP POLICY IF EXISTS allow_all ON public.face_embeddings;
DROP POLICY IF EXISTS allow_all ON public.attendance;
DROP POLICY IF EXISTS allow_all ON public.notifications;

DROP POLICY IF EXISTS attendance_select_all ON public.attendance;
DROP POLICY IF EXISTS attendance_insert_all ON public.attendance;
DROP POLICY IF EXISTS attendance_update_all ON public.attendance;
DROP POLICY IF EXISTS attendance_delete_all ON public.attendance;

DROP POLICY IF EXISTS demo_allow_all_teacher_assignments ON public.teacher_assignments;
DROP POLICY IF EXISTS demo_allow_all_attendance_sessions ON public.attendance_sessions;
DROP POLICY IF EXISTS demo_allow_all_attendance_records ON public.attendance_records;

-- Any other explicitly named demo_allow_all policies in public schema.
do $$
declare
  p record;
begin
  for p in
    select schemaname, tablename, policyname
    from pg_policies
    where schemaname = 'public'
      and policyname like 'demo_allow_all%'
  loop
    execute format('drop policy if exists %I on %I.%I', p.policyname, p.schemaname, p.tablename);
  end loop;
end $$;

-- Confirm no obvious demo policies remain in public schema.
select schemaname, tablename, policyname, cmd, qual, with_check
from pg_policies
where schemaname = 'public'
  and (
    policyname ilike '%allow_all%'
    or policyname ilike '%demo%'
    or qual = 'true'
    or with_check = 'true'
  )
order by tablename, policyname;

