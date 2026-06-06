-- Student My Subjects visibility diagnostic
-- Read-only checks. Replace/add emails in params as needed.

with params(student_email) as (
    values
        ('yashraj@gmail.com'::text),
        ('yashrajkumar@gmail.com'::text)
)
select
    'student_by_email' as check_name,
    s.id,
    s.institute_id,
    s.name,
    s.email,
    s.roll_no,
    s.class_id,
    s.class_name,
    s.section,
    s.status
from public.students s
join params p on lower(s.email) = lower(p.student_email)
order by s.email;

select
    'active_subject_join_codes' as check_name,
    sjc.id,
    sjc.join_code,
    sjc.subject_id,
    sjc.is_active,
    sjc.expires_at,
    subj.name as subject_name,
    subj.code as subject_code,
    subj.class_id,
    subj.teacher_id
from public.subject_join_codes sjc
left join public.subjects subj on subj.id = sjc.subject_id
where sjc.is_active = true
order by sjc.created_at desc nulls last;

with params(student_email) as (
    values
        ('yashraj@gmail.com'::text),
        ('yashrajkumar@gmail.com'::text)
),
current_students as (
    select s.*
    from public.students s
    join params p on lower(s.email) = lower(p.student_email)
)
select
    'subject_enrollments_by_student_id' as check_name,
    s.email,
    se.id as enrollment_id,
    se.student_id,
    se.subject_id,
    se.join_code,
    se.status,
    se.created_at,
    se.updated_at
from current_students s
left join public.subject_enrollments se on se.student_id = s.id
order by s.email, se.created_at desc nulls last;

with params(student_email) as (
    values
        ('yashraj@gmail.com'::text),
        ('yashrajkumar@gmail.com'::text)
),
current_students as (
    select s.*
    from public.students s
    join params p on lower(s.email) = lower(p.student_email)
)
select
    'subjects_linked_to_enrollments' as check_name,
    s.email,
    se.id as enrollment_id,
    se.status as enrollment_status,
    subj.id as subject_id,
    subj.name as subject_name,
    subj.code as subject_code,
    subj.class_id,
    subj.teacher_id
from current_students s
left join public.subject_enrollments se on se.student_id = s.id
left join public.subjects subj on subj.id = se.subject_id
order by s.email, subj.name;

with params(student_email) as (
    values
        ('yashraj@gmail.com'::text),
        ('yashrajkumar@gmail.com'::text)
),
current_students as (
    select s.*
    from public.students s
    join params p on lower(s.email) = lower(p.student_email)
)
select
    'classes_linked_to_subjects' as check_name,
    s.email,
    subj.name as subject_name,
    subj.code as subject_code,
    cls.id as class_id,
    cls.class_name,
    cls.section
from current_students s
left join public.subject_enrollments se on se.student_id = s.id
left join public.subjects subj on subj.id = se.subject_id
left join public.classes cls on cls.id = subj.class_id
order by s.email, subj.name;

with params(student_email) as (
    values
        ('yashraj@gmail.com'::text),
        ('yashrajkumar@gmail.com'::text)
),
current_students as (
    select s.*
    from public.students s
    join params p on lower(s.email) = lower(p.student_email)
)
select
    'teachers_linked_to_subjects' as check_name,
    s.email,
    subj.name as subject_name,
    subj.code as subject_code,
    t.id as teacher_id,
    t.name as teacher_name,
    t.email as teacher_email
from current_students s
left join public.subject_enrollments se on se.student_id = s.id
left join public.subjects subj on subj.id = se.subject_id
left join public.teachers t on t.id = subj.teacher_id
order by s.email, subj.name;
