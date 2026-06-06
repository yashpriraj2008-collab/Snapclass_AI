-- Manual Attendance student visibility diagnostic.
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
    c.id as class_id,
    coalesce(c.class_name, c.name, c.grade) as class_name,
    c.section,
    c.institute_id
  from active_assignments ta
  join public.classes c on c.id = ta.class_id
),
students_by_class_id as (
  select
    st.*,
    ac.class_name as assigned_class_name,
    ac.section as assigned_section
  from public.students st
  join assigned_classes ac on ac.class_id = st.class_id
  where lower(trim(coalesce(st.status, 'active'))) = 'active'
),
students_matching_class_section_missing_or_wrong_class_id as (
  select
    st.*,
    ac.class_id as expected_class_id,
    ac.class_name as assigned_class_name,
    ac.section as assigned_section
  from public.students st
  join assigned_classes ac
    on lower(trim(coalesce(st.class_name, ''))) = lower(trim(coalesce(ac.class_name, '')))
   and lower(trim(coalesce(st.section, ''))) = lower(trim(coalesce(ac.section, '')))
  where coalesce(st.class_id::text, '') <> ac.class_id::text
    and lower(trim(coalesce(st.status, 'active'))) = 'active'
)
select '01_teacher_by_email' as check_name, jsonb_agg(to_jsonb(t)) as rows
from teacher_row t
union all
select '02_active_teacher_assignments', jsonb_agg(to_jsonb(a))
from active_assignments a
union all
select '03_assigned_class_id', jsonb_agg(to_jsonb(c))
from assigned_classes c
union all
select '04_students_by_class_id', jsonb_agg(to_jsonb(st))
from students_by_class_id st
union all
select '05_students_matching_class_section_missing_or_wrong_class_id', jsonb_agg(to_jsonb(st))
from students_matching_class_section_missing_or_wrong_class_id st;
