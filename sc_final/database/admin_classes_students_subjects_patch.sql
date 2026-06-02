-- Admin Classes, Subjects, and Students Flow Patch
-- Safe Supabase schema support for admin setup flow.
-- Does not drop data, expose secrets, or change RLS policies.

create extension if not exists pgcrypto;

create table if not exists public.classes (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid,
  teacher_id uuid,
  class_name text,
  section text,
  academic_year text,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.classes add column if not exists institute_id uuid;
alter table public.classes add column if not exists teacher_id uuid;
alter table public.classes add column if not exists class_name text;
alter table public.classes add column if not exists section text;
alter table public.classes add column if not exists academic_year text;
alter table public.classes add column if not exists status text default 'active';
alter table public.classes add column if not exists created_at timestamptz default now();
alter table public.classes add column if not exists updated_at timestamptz default now();

create table if not exists public.subjects (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid,
  class_id uuid,
  teacher_id uuid,
  name text,
  subject_name text,
  subject_code text,
  class_name text,
  section text,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.subjects add column if not exists institute_id uuid;
alter table public.subjects add column if not exists class_id uuid;
alter table public.subjects add column if not exists teacher_id uuid;
alter table public.subjects add column if not exists name text;
alter table public.subjects add column if not exists subject_name text;
alter table public.subjects add column if not exists subject_code text;
alter table public.subjects add column if not exists class_name text;
alter table public.subjects add column if not exists section text;
alter table public.subjects add column if not exists status text default 'active';
alter table public.subjects add column if not exists created_at timestamptz default now();
alter table public.subjects add column if not exists updated_at timestamptz default now();

create table if not exists public.students (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid,
  class_id uuid,
  name text,
  email text,
  roll_no text,
  class_name text,
  section text,
  phone text,
  parent_name text,
  parent_phone text,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.students add column if not exists institute_id uuid;
alter table public.students add column if not exists class_id uuid;
alter table public.students add column if not exists name text;
alter table public.students add column if not exists email text;
alter table public.students add column if not exists roll_no text;
alter table public.students add column if not exists class_name text;
alter table public.students add column if not exists section text;
alter table public.students add column if not exists phone text;
alter table public.students add column if not exists parent_name text;
alter table public.students add column if not exists parent_phone text;
alter table public.students add column if not exists status text default 'active';
alter table public.students add column if not exists student_code text;
alter table public.students add column if not exists invite_status text default 'pending';
alter table public.students add column if not exists created_at timestamptz default now();
alter table public.students add column if not exists updated_at timestamptz default now();

create table if not exists public.user_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  email text,
  role text,
  institute_id uuid,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.user_profiles alter column id set default gen_random_uuid();
alter table public.user_profiles add column if not exists user_id uuid;
alter table public.user_profiles add column if not exists email text;
alter table public.user_profiles add column if not exists role text;
alter table public.user_profiles add column if not exists institute_id uuid;
alter table public.user_profiles add column if not exists status text default 'active';
alter table public.user_profiles add column if not exists created_at timestamptz default now();
alter table public.user_profiles add column if not exists updated_at timestamptz default now();

create index if not exists idx_admin_classes_institute on public.classes(institute_id);
create index if not exists idx_admin_subjects_institute on public.subjects(institute_id);
create index if not exists idx_admin_subjects_class on public.subjects(class_id);
create index if not exists idx_admin_students_institute on public.students(institute_id);
create index if not exists idx_admin_students_class on public.students(class_id);
create index if not exists idx_admin_students_email_lower on public.students(lower(email));
create index if not exists idx_admin_profiles_email_lower on public.user_profiles(lower(email));
create index if not exists idx_admin_profiles_institute on public.user_profiles(institute_id);

do $$
begin
  if not exists (
    select 1
    from public.classes
    where institute_id is not null
    group by institute_id, lower(coalesce(class_name, '')), lower(coalesce(section, '')), lower(coalesce(academic_year, ''))
    having count(*) > 1
  ) then
    create unique index if not exists uq_admin_classes_identity
      on public.classes(institute_id, lower(coalesce(class_name, '')), lower(coalesce(section, '')), lower(coalesce(academic_year, '')));
  else
    raise notice 'Skipped unique classes index because duplicate classes exist.';
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from public.students
    where email is not null
    group by lower(email)
    having count(*) > 1
  ) then
    create unique index if not exists uq_admin_students_email
      on public.students(lower(email))
      where email is not null;
  else
    raise notice 'Skipped unique students email index because duplicate emails exist.';
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from public.students
    where class_id is not null and roll_no is not null
    group by class_id, lower(roll_no)
    having count(*) > 1
  ) then
    create unique index if not exists uq_admin_students_class_roll
      on public.students(class_id, lower(roll_no))
      where class_id is not null and roll_no is not null;
  else
    raise notice 'Skipped unique students class/roll index because duplicate rolls exist.';
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from public.subjects
    where class_id is not null and subject_code is not null
    group by class_id, lower(subject_code)
    having count(*) > 1
  ) then
    create unique index if not exists uq_admin_subjects_class_code
      on public.subjects(class_id, lower(subject_code))
      where class_id is not null and subject_code is not null;
  else
    raise notice 'Skipped unique subjects class/code index because duplicate subject codes exist.';
  end if;
end $$;
