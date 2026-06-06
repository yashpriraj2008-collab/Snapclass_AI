-- Harden the existing master identity table.
-- Passwords remain exclusively in Supabase Auth; do not add password_hash here.

alter table public.user_profiles
  add column if not exists full_name text,
  add column if not exists phone text,
  add column if not exists status text default 'active',
  add column if not exists created_at timestamptz default now(),
  add column if not exists updated_at timestamptz default now();

update public.user_profiles
set role = case
  when lower(trim(role)) = 'institute_admin' then 'admin'
  when lower(trim(role)) = 'super_admin' then 'founder'
  when lower(trim(role)) in ('class_teacher', 'subject_teacher') then 'teacher'
  else lower(trim(role))
end
where role is not null;

alter table public.user_profiles
  drop constraint if exists user_profiles_role_check;

alter table public.user_profiles
  add constraint user_profiles_role_check
  check (role in ('founder', 'admin', 'teacher', 'student')) not valid;

do $$
begin
  if not exists (
    select 1
    from public.user_profiles
    where email is not null
    group by lower(email)
    having count(*) > 1
  ) then
    create unique index if not exists ux_user_profiles_email_ci
      on public.user_profiles (lower(email))
      where email is not null;
  end if;

  if not exists (
    select 1
    from public.user_profiles
    where user_id is not null
    group by user_id
    having count(*) > 1
  ) then
    create unique index if not exists ux_user_profiles_user_id
      on public.user_profiles (user_id)
      where user_id is not null;
  end if;
end $$;
