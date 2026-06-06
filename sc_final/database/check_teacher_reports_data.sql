-- Diagnostics: Teacher Reports (live data)
-- Purpose: Verify the teacher identity, assignments, sessions, and joined report rows.
-- Do NOT modify/delete any production data.

-- 1) Teacher by email (replace :teacher_email)
-- NOTE: Supabase SQL editor may not support named params; replace the string literal manually.
select *
from public.teachers
where lower(email) = lower('teacher_email_here')
limit 1;

-- 2) Teacher assignments (replace :teacher_id)
select *
from public.teacher_assignments
where teacher_id = 'teacher_id_here'
order by created_at desc
limit 200;

-- 3) Assigned classes for that teacher
select
  ta.teacher_id,
  c.id as class_id,
  c.name as class_name,
  c.section,
  c.grade
from public.teacher_assignments ta
join public.classes c on c.id = ta.class_id
where ta.teacher_id = 'teacher_id_here'
  and coalesce(ta.status, 'active') = 'active'
order by c.grade asc nulls last, c.section asc nulls last, c.name asc
limit 200;

-- 4) Assigned subjects for that teacher
select
  ta.teacher_id,
  s.id as subject_id,
  s.name as subject_name,
  s.code as subject_code,
  s.class_id
from public.teacher_assignments ta
join public.subjects s on s.id = ta.subject_id
where ta.teacher_id = 'teacher_id_here'
  and coalesce(ta.status, 'active') = 'active'
order by s.class_id asc, s.name asc
limit 200;

-- 5) Attendance sessions for that teacher
select
  asess.id as session_id,
  asess.teacher_id,
  asess.institute_id,
  asess.class_id,
  asess.subject_id,
  coalesce(asess.attendance_date, asess.date) as attendance_date,
  asess.mode,
  asess.status,
  asess.created_at
from public.attendance_sessions asess
where asess.teacher_id = 'teacher_id_here'
order by coalesce(asess.attendance_date, asess.date) desc nulls last, asess.created_at desc
limit 200;

-- 6) Attendance records for those sessions (sample)
-- Uses recent sessions only.
with recent_sessions as (
  select id
  from public.attendance_sessions
  where teacher_id = 'teacher_id_here'
  order by coalesce(attendance_date, date) desc nulls last, created_at desc
  limit 50
)
select
  ar.id as record_id,
  ar.session_id,
  ar.student_id,
  ar.class_id,
  ar.subject_id,
  ar.status,
  ar.verification_method,
  ar.confidence,
  ar.marked_by,
  ar.marked_at,
  ar.attendance_date
from public.attendance_records ar
join recent_sessions rs on rs.id = ar.session_id
order by ar.marked_at desc
limit 200;

-- 7) Joined report rows (expected report table)
-- Produces rows with: date/class/subject/student/roll/status
with teacher_sessions as (
  select
    asess.id as session_id,
    coalesce(asess.attendance_date, asess.date) as attendance_date,
    asess.class_id,
    asess.subject_id,
    asess.status as session_status,
    asess.mode
  from public.attendance_sessions asess
  where asess.teacher_id = 'teacher_id_here'
)
select
  ts.attendance_date::text as date,
  c.name as class_name,
  c.section,
  s.name as subject_name,
  s.code as subject_code,
  st.name as student_name,
  st.roll_no,
  ar.status as attendance_status
from teacher_sessions ts
join public.attendance_records ar on ar.session_id = ts.session_id
join public.students st on st.id = ar.student_id
join public.classes c on c.id = coalesce(ar.class_id, ts.class_id)
join public.subjects s on s.id = coalesce(ar.subject_id, ts.subject_id)
where ar.status is not null
order by ts.attendance_date desc nulls last, c.name asc, c.section asc, s.name asc, st.roll_no asc
limit 500;

