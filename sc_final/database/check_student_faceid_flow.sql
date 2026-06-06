-- Student FaceID attendance flow diagnostic
-- Read-only checks. Replace/add student emails in params as needed.

with params(student_email) as (
    values
        ('yashraj@gmail.com'::text),
        ('yashrajkumar@gmail.com'::text)
)
select
    'student_by_email' as check_name,
    s.id as student_id,
    s.email,
    s.name,
    s.roll_no,
    s.institute_id,
    s.class_id,
    s.class_name,
    s.section,
    s.status
from public.students s
join params p on lower(s.email) = lower(p.student_email)
order by s.email;

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
    'student_class_id' as check_name,
    s.email,
    s.class_id,
    cls.class_name,
    cls.section
from current_students s
left join public.classes cls on cls.id = s.class_id
order by s.email;

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
    'subject_enrollments' as check_name,
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
    'subjects_classes_teachers' as check_name,
    s.email,
    subj.id as subject_id,
    subj.name as subject_name,
    subj.code as subject_code,
    cls.id as class_id,
    cls.class_name,
    cls.section,
    t.id as teacher_id,
    t.name as teacher_name,
    t.email as teacher_email
from current_students s
left join public.subject_enrollments se on se.student_id = s.id
left join public.subjects subj on subj.id = se.subject_id
left join public.classes cls on cls.id = subj.class_id
left join public.teachers t on t.id = subj.teacher_id
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
    'face_embeddings_by_student_id' as check_name,
    s.email,
    fe.id as face_embedding_id,
    fe.student_id,
    fe.user_email,
    fe.roll_no,
    fe.status,
    fe.created_at,
    fe.updated_at
from current_students s
left join public.face_embeddings fe on fe.student_id = s.id
order by s.email, fe.updated_at desc nulls last;

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
    'attendance_sessions_today' as check_name,
    s.email,
    sess.id as session_id,
    sess.institute_id,
    sess.teacher_id,
    sess.class_id,
    sess.subject_id,
    coalesce(sess.attendance_date, sess.date) as session_date,
    sess.mode,
    sess.status
from current_students s
left join public.subject_enrollments se on se.student_id = s.id
left join public.subjects subj on subj.id = se.subject_id
left join public.attendance_sessions sess
    on sess.subject_id = subj.id
   and sess.class_id = subj.class_id
   and coalesce(sess.attendance_date, sess.date) = current_date
order by s.email, sess.created_at desc nulls last;

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
    'attendance_records_today' as check_name,
    s.email,
    ar.id as record_id,
    ar.session_id,
    ar.student_id,
    ar.status,
    ar.marked_by,
    ar.attendance_date,
    ar.verification_method,
    ar.confidence,
    ar.marked_at
from current_students s
left join public.attendance_records ar
    on ar.student_id = s.id
   and coalesce(ar.attendance_date, ar.marked_at::date, ar.created_at::date) = current_date
order by s.email, ar.marked_at desc nulls last;
