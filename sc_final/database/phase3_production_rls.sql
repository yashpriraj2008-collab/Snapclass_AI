-- Phase 3 production RLS policies
-- Enable RLS and define policies for core tables.

begin;

-- Enable RLS
DO $$
BEGIN
  IF to_regclass('public.user_profiles') IS NOT NULL THEN
    EXECUTE 'alter table public.user_profiles enable row level security';
  END IF;
  IF to_regclass('public.institutes') IS NOT NULL THEN
    EXECUTE 'alter table public.institutes enable row level security';
  END IF;
  IF to_regclass('public.teachers') IS NOT NULL THEN
    EXECUTE 'alter table public.teachers enable row level security';
  END IF;
  IF to_regclass('public.students') IS NOT NULL THEN
    EXECUTE 'alter table public.students enable row level security';
  END IF;
  IF to_regclass('public.classes') IS NOT NULL THEN
    EXECUTE 'alter table public.classes enable row level security';
  END IF;
  IF to_regclass('public.subjects') IS NOT NULL THEN
    EXECUTE 'alter table public.subjects enable row level security';
  END IF;
  IF to_regclass('public.teacher_assignments') IS NOT NULL THEN
    EXECUTE 'alter table public.teacher_assignments enable row level security';
  END IF;
  IF to_regclass('public.subject_enrollments') IS NOT NULL THEN
    EXECUTE 'alter table public.subject_enrollments enable row level security';
  END IF;
  IF to_regclass('public.subject_join_codes') IS NOT NULL THEN
    EXECUTE 'alter table public.subject_join_codes enable row level security';
  END IF;
  IF to_regclass('public.attendance_sessions') IS NOT NULL THEN
    EXECUTE 'alter table public.attendance_sessions enable row level security';
  END IF;
  IF to_regclass('public.attendance_records') IS NOT NULL THEN
    EXECUTE 'alter table public.attendance_records enable row level security';
  END IF;
  IF to_regclass('public.face_embeddings') IS NOT NULL THEN
    EXECUTE 'alter table public.face_embeddings enable row level security';
  END IF;
END $$;

-- user_profiles
DO $$
BEGIN
  IF to_regclass('public.user_profiles') IS NOT NULL THEN
    EXECUTE 'drop policy if exists user_profiles_select_self on public.user_profiles';
    EXECUTE 'create policy user_profiles_select_self on public.user_profiles for select using ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id) OR user_id = auth.uid())'
      || ')';
  END IF;
END $$;

-- institutes
DO $$
BEGIN
  IF to_regclass('public.institutes') IS NOT NULL THEN
    EXECUTE 'drop policy if exists institutes_select on public.institutes';
    EXECUTE 'create policy institutes_select on public.institutes for select using (private.is_founder() OR id = private.current_institute_id() OR private.is_institute_admin(id))';
  END IF;
END $$;

-- teachers
DO $$
BEGIN
  IF to_regclass('public.teachers') IS NOT NULL THEN
    EXECUTE 'drop policy if exists teachers_select on public.teachers';
    EXECUTE 'create policy teachers_select on public.teachers for select using ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id) OR user_id = auth.uid())'
      || ')';

    EXECUTE 'drop policy if exists teachers_insert on public.teachers';
    EXECUTE 'create policy teachers_insert on public.teachers for insert with check ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id))'
      || ')';

    EXECUTE 'drop policy if exists teachers_update on public.teachers';
    EXECUTE 'create policy teachers_update on public.teachers for update using ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id))'
      || ') with check ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id))'
      || ')';

    EXECUTE 'drop policy if exists teachers_delete on public.teachers';
    EXECUTE 'create policy teachers_delete on public.teachers for delete using ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id))'
      || ')';
  END IF;
END $$;

-- students
DO $$
BEGIN
  IF to_regclass('public.students') IS NOT NULL THEN
    EXECUTE 'drop policy if exists students_select on public.students';
    EXECUTE 'create policy students_select on public.students for select using ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id) OR (user_id = auth.uid()))'
      || ')';

    EXECUTE 'drop policy if exists students_insert on public.students';
    EXECUTE 'create policy students_insert on public.students for insert with check ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id))'
      || ')';

    EXECUTE 'drop policy if exists students_update on public.students';
    EXECUTE 'create policy students_update on public.students for update using ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id))'
      || ') with check ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id))'
      || ')';

    EXECUTE 'drop policy if exists students_delete on public.students';
    EXECUTE 'create policy students_delete on public.students for delete using ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id))'
      || ')';
  END IF;
END $$;

-- classes
DO $$
BEGIN
  IF to_regclass('public.classes') IS NOT NULL THEN
    EXECUTE 'drop policy if exists classes_select on public.classes';
    EXECUTE 'create policy classes_select on public.classes for select using ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id) OR private.teacher_can_access_class(id))'
      || ')';
  END IF;
END $$;

-- subjects
DO $$
BEGIN
  IF to_regclass('public.subjects') IS NOT NULL THEN
    EXECUTE 'drop policy if exists subjects_select on public.subjects';
    EXECUTE 'create policy subjects_select on public.subjects for select using ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id) OR private.teacher_can_access_subject(id) OR private.student_enrolled_in_subject(id))'
      || ')';
  END IF;
END $$;

-- teacher_assignments
DO $$
BEGIN
  IF to_regclass('public.teacher_assignments') IS NOT NULL THEN
    EXECUTE 'drop policy if exists teacher_assignments_select on public.teacher_assignments';
    EXECUTE 'create policy teacher_assignments_select on public.teacher_assignments for select using ('
      || '(private.is_founder() OR private.is_institute_admin((select institute_id from public.teachers t where t.id=teacher_id limit 1)) OR teacher_id = private.current_teacher_id())'
      || ')';
  END IF;
END $$;

-- subject_enrollments
DO $$
BEGIN
  IF to_regclass('public.subject_enrollments') IS NOT NULL THEN
    EXECUTE 'drop policy if exists subject_enrollments_select on public.subject_enrollments';
    EXECUTE 'create policy subject_enrollments_select on public.subject_enrollments for select using ('
      || '(private.is_founder() OR private.is_institute_admin((select institute_id from public.students s where s.id=student_id limit 1)) OR student_id = private.current_student_id())'
      || ')';
  END IF;
END $$;

-- subject_join_codes
DO $$
BEGIN
  IF to_regclass('public.subject_join_codes') IS NOT NULL THEN
    EXECUTE 'drop policy if exists subject_join_codes_select on public.subject_join_codes';
    EXECUTE 'create policy subject_join_codes_select on public.subject_join_codes for select using ('
      || '(private.is_founder() OR private.is_institute_admin(institute_id) OR (exists (select 1 from public.teacher_assignments ta where ta.subject_id = subject_join_codes.subject_id and ta.teacher_id = private.current_teacher_id())))'
      || ')';
  END IF;
END $$;

-- attendance_sessions
DO $$
BEGIN
  IF to_regclass('public.attendance_sessions') IS NOT NULL THEN
    EXECUTE 'drop policy if exists attendance_sessions_select on public.attendance_sessions';
    EXECUTE 'create policy attendance_sessions_select on public.attendance_sessions for select using ('
      || '(private.is_founder() OR private.is_institute_admin((select institute_id from public.teachers t where t.id=attendance_sessions.teacher_id limit 1)) OR attendance_sessions.teacher_id = private.current_teacher_id())'
      || ')';

    EXECUTE 'drop policy if exists attendance_sessions_insert on public.attendance_sessions';
    EXECUTE 'create policy attendance_sessions_insert on public.attendance_sessions for insert with check ('
      || '(private.is_founder() OR private.is_institute_admin((select institute_id from public.teachers t where t.id=attendance_sessions.teacher_id limit 1)) OR attendance_sessions.teacher_id = private.current_teacher_id())'
      || ')';
  END IF;
END $$;

-- attendance_records
DO $$
BEGIN
  IF to_regclass('public.attendance_records') IS NOT NULL THEN
    EXECUTE 'drop policy if exists attendance_records_select on public.attendance_records';
    EXECUTE 'create policy attendance_records_select on public.attendance_records for select using ('
      || '(private.is_founder() OR private.is_institute_admin((select institute_id from public.students s where s.id=attendance_records.student_id limit 1)) OR attendance_records.student_id = private.current_student_id() OR exists (select 1 from public.attendance_sessions asn where asn.id = attendance_records.session_id and asn.teacher_id = private.current_teacher_id()))'
      || ')';

    EXECUTE 'drop policy if exists attendance_records_insert on public.attendance_records';
    EXECUTE 'create policy attendance_records_insert on public.attendance_records for insert with check ('
      || '(private.is_founder() OR exists (select 1 from public.attendance_sessions asn where asn.id = attendance_records.session_id and asn.teacher_id = private.current_teacher_id()))'
      || ')';
  END IF;
END $$;

-- face_embeddings
DO $$
BEGIN
  IF to_regclass('public.face_embeddings') IS NOT NULL THEN
    EXECUTE 'drop policy if exists face_embeddings_select on public.face_embeddings';
    EXECUTE 'create policy face_embeddings_select on public.face_embeddings for select using ('
      || '(private.is_founder() OR user_id = auth.uid() OR student_id = private.current_student_id())'
      || ')';

    EXECUTE 'drop policy if exists face_embeddings_insert on public.face_embeddings';
    EXECUTE 'create policy face_embeddings_insert on public.face_embeddings for insert with check (user_id = auth.uid() OR student_id = private.current_student_id())';

    EXECUTE 'drop policy if exists face_embeddings_update on public.face_embeddings';
    EXECUTE 'create policy face_embeddings_update on public.face_embeddings for update using (user_id = auth.uid() OR student_id = private.current_student_id()) with check (user_id = auth.uid() OR student_id = private.current_student_id())';

    EXECUTE 'drop policy if exists face_embeddings_delete on public.face_embeddings';
    EXECUTE 'create policy face_embeddings_delete on public.face_embeddings for delete using (user_id = auth.uid() OR student_id = private.current_student_id())';
  END IF;
END $$;

commit;


