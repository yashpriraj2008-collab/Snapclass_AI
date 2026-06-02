-- Phase 3 index creation
-- Add indexes needed for performance under explicit filter usage.
-- IMPORTANT: Check columns before creating indexes.

-- Helper function to safely create indexes if column exists
-- (We avoid creating functions to reduce risk; we use DO blocks.)

DO $$
BEGIN
  -- user_profiles.user_id, user_profiles.institute_id
  IF to_regclass('public.user_profiles') IS NOT NULL THEN
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='user_profiles' AND column_name='user_id'
    ) THEN
      IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='user_profiles_user_id_idx'
      ) THEN
        EXECUTE 'CREATE INDEX user_profiles_user_id_idx ON public.user_profiles (user_id)';
      END IF;
    END IF;

    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='user_profiles' AND column_name='institute_id'
    ) THEN
      IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='user_profiles_institute_id_idx'
      ) THEN
        EXECUTE 'CREATE INDEX user_profiles_institute_id_idx ON public.user_profiles (institute_id)';
      END IF;
    END IF;
  END IF;

  -- teachers.user_id, teachers.institute_id
  IF to_regclass('public.teachers') IS NOT NULL THEN
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='teachers' AND column_name='user_id'
    ) THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='teachers_user_id_idx') THEN
        EXECUTE 'CREATE INDEX teachers_user_id_idx ON public.teachers (user_id)';
      END IF;
    END IF;

    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='teachers' AND column_name='institute_id'
    ) THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='teachers_institute_id_idx') THEN
        EXECUTE 'CREATE INDEX teachers_institute_id_idx ON public.teachers (institute_id)';
      END IF;
    END IF;
  END IF;

  -- students.user_id, students.institute_id, students.class_id
  IF to_regclass('public.students') IS NOT NULL THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='students' AND column_name='user_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='students_user_id_idx') THEN
        EXECUTE 'CREATE INDEX students_user_id_idx ON public.students (user_id)';
      END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='students' AND column_name='institute_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='students_institute_id_idx') THEN
        EXECUTE 'CREATE INDEX students_institute_id_idx ON public.students (institute_id)';
      END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='students' AND column_name='class_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='students_class_id_idx') THEN
        EXECUTE 'CREATE INDEX students_class_id_idx ON public.students (class_id)';
      END IF;
    END IF;
  END IF;

  -- classes.institute_id
  IF to_regclass('public.classes') IS NOT NULL THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='classes' AND column_name='institute_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='classes_institute_id_idx') THEN
        EXECUTE 'CREATE INDEX classes_institute_id_idx ON public.classes (institute_id)';
      END IF;
    END IF;
  END IF;

  -- subjects.institute_id, subjects.class_id
  IF to_regclass('public.subjects') IS NOT NULL THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='subjects' AND column_name='institute_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='subjects_institute_id_idx') THEN
        EXECUTE 'CREATE INDEX subjects_institute_id_idx ON public.subjects (institute_id)';
      END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='subjects' AND column_name='class_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='subjects_class_id_idx') THEN
        EXECUTE 'CREATE INDEX subjects_class_id_idx ON public.subjects (class_id)';
      END IF;
    END IF;
  END IF;

  -- teacher_assignments.teacher_id, class_id, subject_id
  IF to_regclass('public.teacher_assignments') IS NOT NULL THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='teacher_assignments' AND column_name='teacher_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='teacher_assignments_teacher_id_idx') THEN
        EXECUTE 'CREATE INDEX teacher_assignments_teacher_id_idx ON public.teacher_assignments (teacher_id)';
      END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='teacher_assignments' AND column_name='class_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='teacher_assignments_class_id_idx') THEN
        EXECUTE 'CREATE INDEX teacher_assignments_class_id_idx ON public.teacher_assignments (class_id)';
      END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='teacher_assignments' AND column_name='subject_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='teacher_assignments_subject_id_idx') THEN
        EXECUTE 'CREATE INDEX teacher_assignments_subject_id_idx ON public.teacher_assignments (subject_id)';
      END IF;
    END IF;
  END IF;

  -- subject_enrollments.student_id, subject_id
  IF to_regclass('public.subject_enrollments') IS NOT NULL THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='subject_enrollments' AND column_name='student_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='subject_enrollments_student_id_idx') THEN
        EXECUTE 'CREATE INDEX subject_enrollments_student_id_idx ON public.subject_enrollments (student_id)';
      END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='subject_enrollments' AND column_name='subject_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='subject_enrollments_subject_id_idx') THEN
        EXECUTE 'CREATE INDEX subject_enrollments_subject_id_idx ON public.subject_enrollments (subject_id)';
      END IF;
    END IF;
  END IF;

  -- attendance_sessions.teacher_id, subject_id
  IF to_regclass('public.attendance_sessions') IS NOT NULL THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='attendance_sessions' AND column_name='teacher_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='attendance_sessions_teacher_id_idx') THEN
        EXECUTE 'CREATE INDEX attendance_sessions_teacher_id_idx ON public.attendance_sessions (teacher_id)';
      END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='attendance_sessions' AND column_name='subject_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='attendance_sessions_subject_id_idx') THEN
        EXECUTE 'CREATE INDEX attendance_sessions_subject_id_idx ON public.attendance_sessions (subject_id)';
      END IF;
    END IF;
  END IF;

  -- attendance_records.session_id, student_id
  IF to_regclass('public.attendance_records') IS NOT NULL THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='attendance_records' AND column_name='session_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='attendance_records_session_id_idx') THEN
        EXECUTE 'CREATE INDEX attendance_records_session_id_idx ON public.attendance_records (session_id)';
      END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='attendance_records' AND column_name='student_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='attendance_records_student_id_idx') THEN
        EXECUTE 'CREATE INDEX attendance_records_student_id_idx ON public.attendance_records (student_id)';
      END IF;
    END IF;
  END IF;

  -- face_embeddings.user_id, face_embeddings.student_id
  IF to_regclass('public.face_embeddings') IS NOT NULL THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='face_embeddings' AND column_name='user_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='face_embeddings_user_id_idx') THEN
        EXECUTE 'CREATE INDEX face_embeddings_user_id_idx ON public.face_embeddings (user_id)';
      END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='face_embeddings' AND column_name='student_id') THEN
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='face_embeddings_student_id_idx') THEN
        EXECUTE 'CREATE INDEX face_embeddings_student_id_idx ON public.face_embeddings (student_id)';
      END IF;
    END IF;
  END IF;

  RAISE NOTICE 'Phase 3 index creation completed.';
END $$;

