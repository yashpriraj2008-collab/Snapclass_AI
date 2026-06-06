-- Student Portal visibility diagnostic
-- Replace the email below with the student account being tested.
-- Read-only checks; do not run repairs from this file.

with params as (
    select 'yashrajkumar@gmail.com'::text as student_email
),
current_student as (
    select s.*
    from public.students s
    join params p on lower(s.email) = lower(p.student_email)
)
select
    'student_by_email' as check_name,
    id,
    institute_id,
    name,
    email,
    roll_no,
    class_id,
    class_name,
    section,
    status
from current_student;

with params as (
    select 'yashrajkumar@gmail.com'::text as student_email
),
current_student as (
    select s.*
    from public.students s
    join params p on lower(s.email) = lower(p.student_email)
)
select
    'subject_enrollments_for_student' as check_name,
    se.id as enrollment_id,
    se.student_id,
    se.subject_id,
    se.status as enrollment_status,
    subj.name as subject_name,
    subj.code as subject_code,
    se.created_at
from public.subject_enrollments se
join current_student s on s.id = se.student_id
left join public.subjects subj on subj.id = se.subject_id
order by se.created_at desc nulls last;

with params as (
    select 'yashrajkumar@gmail.com'::text as student_email
),
current_student as (
    select s.*
    from public.students s
    join params p on lower(s.email) = lower(p.student_email)
)
select
    'available_subject_join_codes_for_student_class' as check_name,
    sjc.id as join_code_id,
    sjc.code as subject_join_code,
    sjc.subject_id,
    subj.name as subject_name,
    subj.code as subject_code,
    subj.class_id,
    cls.class_name,
    cls.section,
    sjc.is_active,
    sjc.expires_at
from current_student s
join public.subjects subj
    on subj.class_id = s.class_id
left join public.classes cls
    on cls.id = subj.class_id
left join public.subject_join_codes sjc
    on sjc.subject_id = subj.id
order by sjc.created_at desc nulls last;

with params as (
    select 'yashrajkumar@gmail.com'::text as student_email
),
current_student as (
    select s.*
    from public.students s
    join params p on lower(s.email) = lower(p.student_email)
)
select
    'attendance_records_for_student' as check_name,
    ar.id as record_id,
    ar.session_id,
    ar.student_id,
    ar.status,
    ar.marked_by,
    ar.attendance_date,
    ar.created_at
from public.attendance_records ar
join current_student s on s.id = ar.student_id
order by coalesce(ar.attendance_date, ar.created_at::date) desc,
         ar.created_at desc nulls last;

with params as (
    select 'yashrajkumar@gmail.com'::text as student_email
),
current_student as (
    select s.*
    from public.students s
    join params p on lower(s.email) = lower(p.student_email)
)
select
    'student_report_rows' as check_name,
    coalesce(ar.attendance_date, ats.date, ar.created_at::date) as attendance_day,
    cls.class_name,
    cls.section,
    subj.name as subject_name,
    subj.code as subject_code,
    ar.status,
    coalesce(t.name, ar.marked_by::text) as marked_by,
    ats.mode,
    ar.id as record_id,
    ats.id as session_id
from public.attendance_records ar
join current_student s on s.id = ar.student_id
left join public.attendance_sessions ats on ats.id = ar.session_id
left join public.subjects subj on subj.id = ats.subject_id
left join public.classes cls on cls.id = ats.class_id
left join public.teachers t on t.id = ats.teacher_id
order by coalesce(ar.attendance_date, ats.date, ar.created_at::date) desc,
         ar.created_at desc nulls last;
