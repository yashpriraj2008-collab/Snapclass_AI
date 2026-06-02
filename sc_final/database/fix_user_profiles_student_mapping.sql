-- Fix user_profiles support for Admin -> Students login mapping.
-- Safe schema patch. Does not delete data.
--
-- DEMO ONLY RLS POLICY INCLUDED BELOW:
-- The demo policy allows all user_profiles reads/writes for testing.
-- Replace it before production with role/institute-scoped policies.

create extension if not exists pgcrypto;

create table if not exists public.user_profiles (
  id uuid primary key default gen_random_uuid()
);

alter table public.user_profiles alter column id set default gen_random_uuid();
alter table public.user_profiles add column if not exists user_id uuid;
alter table public.user_profiles add column if not exists email text;
alter table public.user_profiles add column if not exists role text;
alter table public.user_profiles add column if not exists institute_id uuid;
alter table public.user_profiles add column if not exists status text default 'active';
alter table public.user_profiles add column if not exists created_at timestamptz default now();
alter table public.user_profiles add column if not exists updated_at timestamptz default now();

alter table public.user_profiles alter column status set default 'active';
alter table public.user_profiles alter column created_at set default now();
alter table public.user_profiles alter column updated_at set default now();

update public.user_profiles
set status = 'active'
where status is null or status = '';

create index if not exists idx_user_profiles_email_lower
  on public.user_profiles(lower(email));

create index if not exists idx_user_profiles_role
  on public.user_profiles(role);

create index if not exists idx_user_profiles_institute_id
  on public.user_profiles(institute_id);

alter table public.user_profiles enable row level security;

drop policy if exists demo_allow_all_user_profiles on public.user_profiles;

-- DEMO ONLY, replace before production.
create policy demo_allow_all_user_profiles
  on public.user_profiles
  for all
  using (true)
  with check (true);

notify pgrst, 'reload schema';
