-- Teacher Students visibility diagnostic.
-- Replace the email below before running, or keep the default for the reported case.
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
  left join public.classes c on c.id = ta.class_id
),
students_by_class_id as (
  select s.*
  from public.students s
  join assigned_classes ac on ac.class_id = s.class_id
  where lower(trim(coalesce(s.status, 'active'))) = 'active'
),
students_missing_class_id_same_class as (
  select s.*
  from public.students s
  join assigned_classes ac
    on lower(trim(coalesce(s.class_name, ''))) = lower(trim(coalesce(ac.class_name, '')))
   and lower(trim(coalesce(s.section, ''))) = lower(trim(coalesce(ac.section, '')))
  where s.class_id is null
    and lower(trim(coalesce(s.status, 'active'))) = 'active'
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
select '04_students_by_class_id', jsonb_agg(to_jsonb(s))
from students_by_class_id s
union all
select '05_students_same_class_section_missing_class_id', jsonb_agg(to_jsonb(s))
from students_missing_class_id_same_class s;
