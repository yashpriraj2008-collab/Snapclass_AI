-- SnapClass AI — Phase 2 Production RLS Policies
-- Run on: staging first
-- Do not apply automatically to main.
--
-- IMPORTANT rules:
-- - Avoid recursive policies
-- - Never query user_profiles inside a policy on user_profiles
-- - Use auth.uid() directly where possible
-- - Minimum RLS only (least privilege)

-- Enable RLS
ALTER TABLE public.institutes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teacher_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.classes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subject_join_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subject_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attendance_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attendance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.face_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Helper views for scoping to the authenticated user.
-- These only use teachers/students and auth.uid().
create or replace view public._prod2_auth_teachers as
select t.id
from public.teachers t
where t.user_id = auth.uid();

create or replace view public._prod2_auth_students as
select s.id
from public.students s
where s.user_id = auth.uid();

-- ============================================================
-- 1) user_profiles: users can select/update own profile
-- ============================================================
DROP POLICY IF EXISTS prod2_user_profiles_select_own ON public.user_profiles;
CREATE POLICY prod2_user_profiles_select_own
ON public.user_profiles
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

DROP POLICY IF EXISTS prod2_user_profiles_update_own ON public.user_profiles;
CREATE POLICY prod2_user_profiles_update_own
ON public.user_profiles
FOR UPDATE
TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- ============================================================
-- 2) teachers: teacher can select own teacher row
-- ============================================================
DROP POLICY IF EXISTS prod2_teachers_select_own ON public.teachers;
CREATE POLICY prod2_teachers_select_own
ON public.teachers
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

-- ============================================================
-- 3) students: student can select own student row
-- ============================================================
DROP POLICY IF EXISTS prod2_students_select_own ON public.students;
CREATE POLICY prod2_students_select_own
ON public.students
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

-- ============================================================
-- 4) teacher_assignments: teacher can select own assignments
-- ============================================================
DROP POLICY IF EXISTS prod2_teacher_assignments_select_own ON public.teacher_assignments;
CREATE POLICY prod2_teacher_assignments_select_own
ON public.teacher_assignments
FOR SELECT
TO authenticated
USING (teacher_id IN (SELECT id FROM public._prod2_auth_teachers));

-- ============================================================
-- 5) classes: teacher can select assigned classes; student can select own class
-- ============================================================
DROP POLICY IF EXISTS prod2_classes_select_teacher_assigned ON public.classes;
CREATE POLICY prod2_classes_select_teacher_assigned
ON public.classes
FOR SELECT
TO authenticated
USING (
  id IN (
    SELECT ta.class_id
    FROM public.teacher_assignments ta
    WHERE ta.teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  )
);

DROP POLICY IF EXISTS prod2_classes_select_student_own ON public.classes;
CREATE POLICY prod2_classes_select_student_own
ON public.classes
FOR SELECT
TO authenticated
USING (
  id IN (
    SELECT s.class_id
    FROM public.students s
    WHERE s.id IN (SELECT id FROM public._prod2_auth_students)
  )
);

-- ============================================================
-- 6) subjects: teacher can select assigned subjects; student can select enrolled subjects
-- ============================================================
DROP POLICY IF EXISTS prod2_subjects_select_teacher_assigned ON public.subjects;
CREATE POLICY prod2_subjects_select_teacher_assigned
ON public.subjects
FOR SELECT
TO authenticated
USING (
  id IN (
    SELECT ta.subject_id
    FROM public.teacher_assignments ta
    WHERE ta.teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  )
);

DROP POLICY IF EXISTS prod2_subjects_select_student_enrolled ON public.subjects;
CREATE POLICY prod2_subjects_select_student_enrolled
ON public.subjects
FOR SELECT
TO authenticated
USING (
  id IN (
    SELECT se.subject_id
    FROM public.subject_enrollments se
    WHERE se.student_id IN (SELECT id FROM public._prod2_auth_students)
      AND se.status = 'active'
  )
);

-- ============================================================
-- 7) subject_join_codes: teacher can manage codes for own subjects;
--    student can read active join code only for enrollment
-- ============================================================
DROP POLICY IF EXISTS prod2_subject_join_codes_teacher_manage ON public.subject_join_codes;
CREATE POLICY prod2_subject_join_codes_teacher_manage
ON public.subject_join_codes
FOR ALL
TO authenticated
USING (
  teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  AND subject_id IN (
    SELECT ta.subject_id
    FROM public.teacher_assignments ta
    WHERE ta.teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  )
)
WITH CHECK (
  teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  AND subject_id IN (
    SELECT ta.subject_id
    FROM public.teacher_assignments ta
    WHERE ta.teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  )
);

DROP POLICY IF EXISTS prod2_subject_join_codes_student_read_enrolled_active ON public.subject_join_codes;
CREATE POLICY prod2_subject_join_codes_student_read_enrolled_active
ON public.subject_join_codes
FOR SELECT
TO authenticated
USING (
  is_active = true
  AND subject_id IN (
    SELECT se.subject_id
    FROM public.subject_enrollments se
    WHERE se.student_id IN (SELECT id FROM public._prod2_auth_students)
      AND se.status = 'active'
  )
);

-- ============================================================
-- 8) subject_enrollments: student can select/insert own enrollment
-- ============================================================
DROP POLICY IF EXISTS prod2_subject_enrollments_student_select_own ON public.subject_enrollments;
CREATE POLICY prod2_subject_enrollments_student_select_own
ON public.subject_enrollments
FOR SELECT
TO authenticated
USING (student_id IN (SELECT id FROM public._prod2_auth_students));

DROP POLICY IF EXISTS prod2_subject_enrollments_student_insert_own ON public.subject_enrollments;
CREATE POLICY prod2_subject_enrollments_student_insert_own
ON public.subject_enrollments
FOR INSERT
TO authenticated
WITH CHECK (student_id IN (SELECT id FROM public._prod2_auth_students));

-- ============================================================
-- 9) attendance_sessions:
--    teacher can insert/select sessions for assigned subjects/classes
-- ============================================================
DROP POLICY IF EXISTS prod2_attendance_sessions_teacher_select_insert_assigned ON public.attendance_sessions;
CREATE POLICY prod2_attendance_sessions_teacher_select_insert_assigned
ON public.attendance_sessions
FOR ALL
TO authenticated
USING (
  teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  AND class_id IN (
    SELECT ta.class_id
    FROM public.teacher_assignments ta
    WHERE ta.teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  )
  AND subject_id IN (
    SELECT ta.subject_id
    FROM public.teacher_assignments ta
    WHERE ta.teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  )
)
WITH CHECK (
  teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  AND class_id IN (
    SELECT ta.class_id
    FROM public.teacher_assignments ta
    WHERE ta.teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  )
  AND subject_id IN (
    SELECT ta.subject_id
    FROM public.teacher_assignments ta
    WHERE ta.teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  )
);

DROP POLICY IF EXISTS prod2_attendance_sessions_student_select_linked ON public.attendance_sessions;
CREATE POLICY prod2_attendance_sessions_student_select_linked
ON public.attendance_sessions
FOR SELECT
TO authenticated
USING (
  id IN (
    SELECT ar.session_id
    FROM public.attendance_records ar
    WHERE ar.student_id IN (SELECT id FROM public._prod2_auth_students)
  )
);

-- ============================================================
-- 10) attendance_records:
--    teacher can insert/select records for assigned sessions; student can select own
-- ============================================================
DROP POLICY IF EXISTS prod2_attendance_records_teacher_crud_assigned_sessions ON public.attendance_records;
CREATE POLICY prod2_attendance_records_teacher_crud_assigned_sessions
ON public.attendance_records
FOR ALL
TO authenticated
USING (
  session_id IN (
    SELECT s.id
    FROM public.attendance_sessions s
    WHERE s.teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  )
)
WITH CHECK (
  session_id IN (
    SELECT s.id
    FROM public.attendance_sessions s
    WHERE s.teacher_id IN (SELECT id FROM public._prod2_auth_teachers)
  )
);

DROP POLICY IF EXISTS prod2_attendance_records_student_select_own ON public.attendance_records;
CREATE POLICY prod2_attendance_records_student_select_own
ON public.attendance_records
FOR SELECT
TO authenticated
USING (student_id IN (SELECT id FROM public._prod2_auth_students));

-- ============================================================
-- 11) face_embeddings:
--    student can manage only own embedding
-- ============================================================
DROP POLICY IF EXISTS prod2_face_embeddings_student_manage_own ON public.face_embeddings;
CREATE POLICY prod2_face_embeddings_student_manage_own
ON public.face_embeddings
FOR ALL
TO authenticated
USING (student_id IN (SELECT id FROM public._prod2_auth_students))
WITH CHECK (student_id IN (SELECT id FROM public._prod2_auth_students));

