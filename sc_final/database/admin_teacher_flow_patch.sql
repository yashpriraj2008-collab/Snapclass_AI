-- Admin Teacher Flow Patch
-- Purpose: support Admin Add Teacher + Assign Teacher without changing RLS.
-- Safe to run in Supabase SQL Editor. Does not drop data or policies.

create extension if not exists pgcrypto;

create table if not exists public.teachers (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid,
  user_id uuid,
  name text,
  email text,
  phone text,
  teacher_code text,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.teachers add column if not exists institute_id uuid;
alter table public.teachers add column if not exists user_id uuid;
alter table public.teachers add column if not exists name text;
alter table public.teachers add column if not exists email text;
alter table public.teachers add column if not exists phone text;
alter table public.teachers add column if not exists teacher_code text;
alter table public.teachers add column if not exists invite_code text;
alter table public.teachers add column if not exists invite_status text default 'pending';
alter table public.teachers add column if not exists status text default 'active';
alter table public.teachers add column if not exists created_at timestamptz default now();
alter table public.teachers add column if not exists updated_at timestamptz default now();

update public.teachers
set teacher_code = coalesce(nullif(teacher_code, ''), nullif(invite_code, ''))
where teacher_code is null or teacher_code = '';

create table if not exists public.user_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  email text not null,
  role text not null,
  institute_id uuid,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.user_profiles alter column id set default gen_random_uuid();
alter table public.user_profiles add column if not exists user_id uuid;
alter table public.user_profiles add column if not exists email text;
alter table public.user_profiles add column if not exists full_name text;
alter table public.user_profiles add column if not exists role text;
alter table public.user_profiles add column if not exists institute_id uuid;
alter table public.user_profiles add column if not exists status text default 'active';
alter table public.user_profiles add column if not exists created_at timestamptz default now();
alter table public.user_profiles add column if not exists updated_at timestamptz default now();

create table if not exists public.teacher_assignments (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid,
  teacher_id uuid,
  class_id uuid,
  subject_id uuid,
  assignment_type text default 'subject_teacher',
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.teacher_assignments add column if not exists institute_id uuid;
alter table public.teacher_assignments add column if not exists teacher_id uuid;
alter table public.teacher_assignments add column if not exists class_id uuid;
alter table public.teacher_assignments add column if not exists subject_id uuid;
alter table public.teacher_assignments add column if not exists assignment_type text default 'subject_teacher';
alter table public.teacher_assignments add column if not exists status text default 'active';
alter table public.teacher_assignments add column if not exists created_at timestamptz default now();
alter table public.teacher_assignments add column if not exists updated_at timestamptz default now();

alter table public.classes add column if not exists institute_id uuid;
alter table public.classes add column if not exists status text default 'active';
alter table public.classes add column if not exists created_at timestamptz default now();
alter table public.classes add column if not exists updated_at timestamptz default now();

alter table public.subjects add column if not exists institute_id uuid;
alter table public.subjects add column if not exists class_id uuid;
alter table public.subjects add column if not exists status text default 'active';
alter table public.subjects add column if not exists created_at timestamptz default now();
alter table public.subjects add column if not exists updated_at timestamptz default now();

create index if not exists idx_admin_teacher_flow_teachers_institute on public.teachers(institute_id);
create index if not exists idx_admin_teacher_flow_teachers_email_lower on public.teachers(lower(email));
create index if not exists idx_admin_teacher_flow_teachers_code on public.teachers(teacher_code);
create index if not exists idx_admin_teacher_flow_profiles_email_lower on public.user_profiles(lower(email));
create index if not exists idx_admin_teacher_flow_profiles_user_id on public.user_profiles(user_id);
create index if not exists idx_admin_teacher_flow_profiles_institute on public.user_profiles(institute_id);
create index if not exists idx_admin_teacher_flow_assignments_institute on public.teacher_assignments(institute_id);
create index if not exists idx_admin_teacher_flow_assignments_teacher on public.teacher_assignments(teacher_id);
create index if not exists idx_admin_teacher_flow_assignments_class on public.teacher_assignments(class_id);
create index if not exists idx_admin_teacher_flow_assignments_subject on public.teacher_assignments(subject_id);

do $$
begin
  if not exists (
    select 1
    from public.teachers
    where email is not null and institute_id is not null
    group by institute_id, lower(email)
    having count(*) > 1
  ) then
    create unique index if not exists uq_admin_teacher_flow_teacher_email_per_institute
      on public.teachers(institute_id, lower(email))
      where email is not null;
  else
    raise notice 'Skipped unique teacher email index because duplicate teacher emails exist.';
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from public.user_profiles
    where email is not null
    group by lower(email)
    having count(*) > 1
  ) then
    create unique index if not exists uq_admin_teacher_flow_profile_email
      on public.user_profiles(lower(email))
      where email is not null;
  else
    raise notice 'Skipped unique user_profiles email index because duplicate profile emails exist.';
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from public.teacher_assignments
    where teacher_id is not null and class_id is not null and subject_id is not null
    group by teacher_id, class_id, subject_id
    having count(*) > 1
  ) then
    create unique index if not exists uq_admin_teacher_flow_assignment
      on public.teacher_assignments(teacher_id, class_id, subject_id)
      where teacher_id is not null and class_id is not null and subject_id is not null;
  else
    raise notice 'Skipped unique teacher assignment index because duplicate assignments exist.';
  end if;
end $$;
