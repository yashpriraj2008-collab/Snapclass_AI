-- Attendance Visibility System - Phase 5 Schema Patch
-- Run this in Supabase SQL Editor

-- 1. Add marked_method to attendance_records if missing
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'attendance_records' AND column_name = 'marked_method'
  ) THEN
    ALTER TABLE public.attendance_records
    ADD COLUMN marked_method text DEFAULT 'manual'
      CHECK (marked_method IN ('ai', 'manual', 'faceid'));
  END IF;
END $$;

-- 2. Create attendance_percentage helper view (or table if preferred)
CREATE TABLE IF NOT EXISTS public.attendance_percentage (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES public.students(id) ON DELETE CASCADE,
  total_classes integer DEFAULT 0,
  present_count integer DEFAULT 0,
  percentage numeric DEFAULT 0,
  updated_at timestamptz DEFAULT now(),
  UNIQUE(student_id)
);

-- 3. Notifications table for attendance events
CREATE TABLE IF NOT EXISTS public.attendance_notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id uuid REFERENCES public.students(id) ON DELETE CASCADE,
  session_id uuid REFERENCES public.attendance_sessions(id) ON DELETE CASCADE,
  title text NOT NULL DEFAULT 'Attendance Updated',
  message text NOT NULL,
  type text DEFAULT 'attendance',
  is_read boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

-- 4. Enable realtime for attendance_records and attendance_notifications
-- Note: Requires supabase-realtime extension
DO $$
BEGIN
  -- Check if realtime is already enabled for these tables
  IF NOT EXISTS (
    SELECT 1 FROM pg_publication_tables
    WHERE pubname = 'supabase_realtime'
    AND tablename = 'attendance_records'
  ) THEN
    ALTER PUBLICATION supabase_realtime ADD TABLE public.attendance_records;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_publication_tables
    WHERE pubname = 'supabase_realtime'
    AND tablename = 'attendance_notifications'
  ) THEN
    ALTER PUBLICATION supabase_realtime ADD TABLE public.attendance_notifications;
  END IF;
END $$;

-- 5. RLS for notifications
ALTER TABLE public.attendance_notifications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "notifications_select_own" ON public.attendance_notifications;
CREATE POLICY "notifications_select_own" ON public.attendance_notifications
  FOR SELECT
  TO authenticated, anon
  USING (true);

DROP POLICY IF EXISTS "notifications_insert" ON public.attendance_notifications;
CREATE POLICY "notifications_insert" ON public.attendance_notifications
  FOR INSERT
  TO authenticated, anon
  WITH CHECK (true);

DROP POLICY IF EXISTS "notifications_update" ON public.attendance_notifications;
CREATE POLICY "notifications_update" ON public.attendance_notifications
  FOR UPDATE
  TO authenticated, anon
  USING (true)
  WITH CHECK (true);

-- 6. Indexes for performance
CREATE INDEX IF NOT EXISTS idx_attendance_records_student_date
  ON public.attendance_records(student_id, attendance_date DESC);

CREATE INDEX IF NOT EXISTS idx_attendance_records_session_student
  ON public.attendance_records(session_id, student_id);

CREATE INDEX IF NOT EXISTS idx_attendance_notifications_student
  ON public.attendance_notifications(student_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_attendance_records_method
  ON public.attendance_records(marked_method);

-- 7. Function to auto-calculate attendance percentage
CREATE OR REPLACE FUNCTION public.calculate_attendance_percentage(p_student_id uuid)
RETURNS numeric
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_total integer;
  v_present integer;
  v_pct numeric;
BEGIN
  SELECT COUNT(*), COUNT(*) FILTER (WHERE status IN ('present', 'late'))
  INTO v_total, v_present
  FROM public.attendance_records
  WHERE student_id = p_student_id;

  v_pct := CASE WHEN v_total > 0
    THEN ROUND((v_present::numeric / v_total::numeric) * 100, 1)
    ELSE 0
  END;

  INSERT INTO public.attendance_percentage (student_id, total_classes, present_count, percentage, updated_at)
  VALUES (p_student_id, v_total, v_present, v_pct, now())
  ON CONFLICT (student_id)
  DO UPDATE SET
    total_classes = v_total,
    present_count = v_present,
    percentage = v_pct,
    updated_at = now();

  RETURN v_pct;
END;
$$;

-- 8. Function to create attendance notification
CREATE OR REPLACE FUNCTION public.create_attendance_notification()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_student_name text;
  v_subject_name text;
  v_session_status text;
  v_session_subject_id uuid;
BEGIN
  -- Get student name
  SELECT name INTO v_student_name FROM public.students WHERE id = NEW.student_id;

  -- Get session info
  SELECT subject_id, status
  INTO v_session_subject_id, v_session_status
  FROM public.attendance_sessions
  WHERE id = NEW.session_id;

  -- Get subject name
  SELECT name INTO v_subject_name FROM public.subjects WHERE id = v_session_subject_id;

  -- Insert notification
  INSERT INTO public.attendance_notifications (
    student_id,
    session_id,
    title,
    message,
    type
  ) VALUES (
    NEW.student_id,
    NEW.session_id,
    'Attendance Updated',
    CASE
      WHEN NEW.status IN ('present', 'late') THEN
        'You were marked ' || NEW.status || ' in ' || COALESCE(v_subject_name, 'a subject') || '.'
      ELSE
        'You were marked ' || NEW.status || ' in ' || COALESCE(v_subject_name, 'a subject') || '.'
    END,
    'attendance'
  );

  -- Update percentage
  PERFORM public.calculate_attendance_percentage(NEW.student_id);

  RETURN NEW;
END;
$$;

-- 9. Trigger to auto-create notification on attendance insert/update
DROP TRIGGER IF EXISTS trg_attendance_notification ON public.attendance_records;
CREATE TRIGGER trg_attendance_notification
  AFTER INSERT OR UPDATE OF status
  ON public.attendance_records
  FOR EACH ROW
  EXECUTE FUNCTION public.create_attendance_notification();
