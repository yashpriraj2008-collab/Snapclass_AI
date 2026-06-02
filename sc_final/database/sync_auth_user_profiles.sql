-- Sync existing teachers/students to public.user_profiles after Auth users exist.
--
-- Use this after manually creating Supabase Auth users with the same email as
-- public.teachers.email or public.students.email.
--
-- Important:
-- - public.user_profiles.id must be auth.users.id.
-- - This script does not create Auth users.
-- - This script does not drop foreign keys or weaken Auth schema.

create extension if not exists pgcrypto;

create table if not exists public.user_profiles (
  id uuid primary key
);

alter table public.user_profiles add column if not exists user_id uuid;
alter table public.user_profiles add column if not exists email text;
alter table public.user_profiles add column if not exists role text;
alter table public.user_profiles add column if not exists institute_id uuid;
alter table public.user_profiles add column if not exists status text default 'active';
alter table public.user_profiles add column if not exists created_at timestamptz default now();
alter table public.user_profiles add column if not exists updated_at timestamptz default now();

-- Teachers: update existing profiles by email when the Auth user exists.
with matched_teachers as (
  select
    u.id as auth_user_id,
    lower(u.email) as email,
    t.institute_id
  from auth.users u
  join public.teachers t
    on lower(t.email) = lower(u.email)
  where u.email is not null
),
updated_teacher_profiles as (
  update public.user_profiles p
  set
    id = mt.auth_user_id,
    user_id = mt.auth_user_id,
    email = mt.email,
    role = 'teacher',
    institute_id = mt.institute_id,
    status = 'active',
    updated_at = now()
  from matched_teachers mt
  where lower(p.email) = mt.email
  returning p.id
)
insert into public.user_profiles (
  id,
  user_id,
  email,
  role,
  institute_id,
  status,
  created_at,
  updated_at
)
select
  mt.auth_user_id,
  mt.auth_user_id,
  mt.email,
  'teacher',
  mt.institute_id,
  'active',
  now(),
  now()
from matched_teachers mt
where not exists (
  select 1
  from public.user_profiles p
  where p.id = mt.auth_user_id or lower(p.email) = mt.email
);

-- Students: update existing profiles by email when the Auth user exists.
with matched_students as (
  select
    u.id as auth_user_id,
    lower(u.email) as email,
    s.institute_id
  from auth.users u
  join public.students s
    on lower(s.email) = lower(u.email)
  where u.email is not null
),
updated_student_profiles as (
  update public.user_profiles p
  set
    id = ms.auth_user_id,
    user_id = ms.auth_user_id,
    email = ms.email,
    role = 'student',
    institute_id = ms.institute_id,
    status = 'active',
    updated_at = now()
  from matched_students ms
  where lower(p.email) = ms.email
  returning p.id
)
insert into public.user_profiles (
  id,
  user_id,
  email,
  role,
  institute_id,
  status,
  created_at,
  updated_at
)
select
  ms.auth_user_id,
  ms.auth_user_id,
  ms.email,
  'student',
  ms.institute_id,
  'active',
  now(),
  now()
from matched_students ms
where not exists (
  select 1
  from public.user_profiles p
  where p.id = ms.auth_user_id or lower(p.email) = ms.email
);

notify pgrst, 'reload schema';
