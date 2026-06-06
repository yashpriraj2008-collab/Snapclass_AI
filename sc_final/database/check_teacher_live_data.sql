-- Teacher live data diagnostic.
-- Replace the email if needed. This file only reads data.
with params as (
  select lower(trim('kavitadevi@gmail.com')) as teacher_email
),
teacher_row as (
  select t.*
  from public.teachers t
  join params p on lower(trim(t.email)) = p.teacher_email
),
active_assignments as (
  select ta.*
  from public.teacher_assignments ta
  join teacher_row t on t.id = ta.teacher_id
  where lower(trim(coalesce(ta.status, 'active'))) = 'active'
),
assigned_classes as (
  select
    c.*
  from active_assignments ta
  join public.classes c on c.id = ta.class_id
),
assigned_subjects as (
  select
    s.*
  from active_assignments ta
  join public.subjects s on s.id = ta.subject_id
),
students_in_assigned_classes as (
  select st.*
  from public.students st
  join active_assignments ta on ta.class_id = st.class_id
  where lower(trim(coalesce(st.status, 'active'))) = 'active'
),
teacher_sessions as (
  select sess.*
  from public.attendance_sessions sess
  join teacher_row t on t.id = sess.teacher_id
),
teacher_records as (
  select ar.*
  from public.attendance_records ar
  join teacher_sessions sess on sess.id = ar.session_id
),
students_missing_class_id_same_class as (
  select st.*
  from public.students st
  join assigned_classes c
    on lower(trim(coalesce(st.class_name, ''))) in (
      lower(trim(coalesce(c.class_name, ''))),
      lower(trim(coalesce(c.name, ''))),
      lower(trim(coalesce(c.grade, ''))),
      lower(trim(concat_ws('-', nullif(coalesce(c.class_name, c.name, c.grade), ''), nullif(c.section, ''))))
    )
   and (
      lower(trim(coalesce(st.section, ''))) = lower(trim(coalesce(c.section, '')))
      or coalesce(st.section, '') = ''
   )
  where st.class_id is null
    and lower(trim(coalesce(st.status, 'active'))) = 'active'
)
select '01_teacher_by_email' as check_name, jsonb_agg(to_jsonb(t)) as rows
from teacher_row t
union all
select '02_active_teacher_assignments', jsonb_agg(to_jsonb(a))
from active_assignments a
union all
select '03_assigned_classes', jsonb_agg(to_jsonb(c))
from assigned_classes c
union all
select '04_assigned_subjects', jsonb_agg(to_jsonb(s))
from assigned_subjects s
union all
select '05_students_in_assigned_classes', jsonb_agg(to_jsonb(st))
from students_in_assigned_classes st
union all
select '06_attendance_sessions', jsonb_agg(to_jsonb(sess))
from teacher_sessions sess
union all
select '07_attendance_records', jsonb_agg(to_jsonb(ar))
from teacher_records ar
union all
select '08_students_same_class_section_missing_class_id', jsonb_agg(to_jsonb(st))
from students_missing_class_id_same_class st;
