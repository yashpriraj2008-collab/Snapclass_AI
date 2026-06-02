-- Teacher assignment visibility diagnostics.
-- Replace the email below with the teacher email you are testing.
-- This file does not delete or update data.

-- 1) Teacher by email.
select
  id as teacher_id,
  institute_id,
  user_id,
  name,
  email,
  status
from public.teachers
where lower(email) = lower('kavitadevi@gmail.com');

-- 2) Active teacher assignments for that teacher.
select
  ta.*
from public.teacher_assignments ta
join public.teachers t
  on t.id = ta.teacher_id
where lower(t.email) = lower('kavitadevi@gmail.com')
  and coalesce(ta.status, 'active') = 'active'
order by ta.created_at desc nulls last;

-- 3) Subjects linked to assignment.
select
  ta.id as assignment_id,
  ta.teacher_id,
  ta.class_id,
  c.class_name,
  c.section,
  ta.subject_id,
  s.subject_name,
  s.name,
  s.subject_code,
  s.code,
  ta.status as assignment_status
from public.teacher_assignments ta
join public.teachers t
  on t.id = ta.teacher_id
left join public.classes c
  on c.id = ta.class_id
left join public.subjects s
  on s.id = ta.subject_id
where lower(t.email) = lower('kavitadevi@gmail.com')
  and coalesce(ta.status, 'active') = 'active'
order by c.class_name, c.section, s.subject_name;

-- 4) Class/subject/institute mismatch check.
select
  ta.id as assignment_id,
  t.email as teacher_email,
  t.institute_id as teacher_institute_id,
  ta.institute_id as assignment_institute_id,
  c.institute_id as class_institute_id,
  s.institute_id as subject_institute_id,
  ta.class_id,
  ta.subject_id,
  case
    when ta.subject_id is null then 'missing subject_id'
    when s.id is null then 'subject_id does not exist in public.subjects'
    when c.id is null then 'class_id does not exist in public.classes'
    when ta.institute_id is not null and t.institute_id is not null and ta.institute_id <> t.institute_id then 'assignment/teacher institute mismatch'
    when c.institute_id is not null and t.institute_id is not null and c.institute_id <> t.institute_id then 'class/teacher institute mismatch'
    when s.institute_id is not null and t.institute_id is not null and s.institute_id <> t.institute_id then 'subject/teacher institute mismatch'
    when s.class_id is not null and ta.class_id is not null and s.class_id <> ta.class_id then 'subject/class mismatch'
    else 'ok'
  end as visibility_check
from public.teacher_assignments ta
join public.teachers t
  on t.id = ta.teacher_id
left join public.classes c
  on c.id = ta.class_id
left join public.subjects s
  on s.id = ta.subject_id
where lower(t.email) = lower('kavitadevi@gmail.com')
order by visibility_check, ta.id;
