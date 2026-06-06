-- Student Portal live-data diagnostic.
-- Replace the email below when diagnosing another student. This file only reads data.
with params as (
  select lower(trim('student@example.com')) as student_email
),
student_profile as (
  select up.*
  from public.user_profiles up
  join params p on lower(trim(up.email)) = p.student_email
),
student_row as (
  select s.*
  from public.students s
  join params p on lower(trim(s.email)) = p.student_email
),
student_class as (
  select c.*
  from public.classes c
  join student_row s on s.class_id = c.id
),
subjects_by_class as (
  select sub.*
  from public.subjects sub
  join student_row s on s.class_id = sub.class_id
),
student_enrollments as (
  select se.*
  from public.subject_enrollments se
  join student_row s on s.id = se.student_id
),
student_records as (
  select ar.*
  from public.attendance_records ar
  join student_row s on s.id = ar.student_id
),
joined_report_rows as (
  select
    ar.id as attendance_record_id,
    coalesce(ar.attendance_date, sess.attendance_date, sess.date) as attendance_date,
    ar.status,
    sub.subject_name,
    sub.name as subject_name_fallback,
    sub.subject_code,
    sub.code as subject_code_fallback,
    c.class_name,
    c.name as class_name_fallback,
    c.section,
    t.name as teacher_name,
    t.email as teacher_email
  from student_records ar
  left join public.attendance_sessions sess on sess.id = ar.session_id
  left join public.subjects sub on sub.id = coalesce(ar.subject_id, sess.subject_id)
  left join public.classes c on c.id = coalesce(ar.class_id, sess.class_id)
  left join public.teachers t on t.id::text = coalesce(sess.teacher_id::text, ar.marked_by)
),
students_missing_class_id as (
  select s.*
  from public.students s
  join params p on lower(trim(s.email)) = p.student_email
  where s.class_id is null
)
select '01_user_profiles_row' as check_name, jsonb_agg(to_jsonb(up)) as rows
from student_profile up
union all
select '02_student_by_email', jsonb_agg(to_jsonb(s))
from student_row s
union all
select '03_student_class_id', jsonb_agg(to_jsonb(c))
from student_class c
union all
select '04_subjects_by_class_id', jsonb_agg(to_jsonb(sub))
from subjects_by_class sub
union all
select '05_subject_enrollments', jsonb_agg(to_jsonb(se))
from student_enrollments se
union all
select '06_attendance_records', jsonb_agg(to_jsonb(ar))
from student_records ar
union all
select '07_attendance_sessions_joined_report_rows', jsonb_agg(to_jsonb(r))
from joined_report_rows r
union all
select '08_students_missing_class_id', jsonb_agg(to_jsonb(s))
from students_missing_class_id s;
