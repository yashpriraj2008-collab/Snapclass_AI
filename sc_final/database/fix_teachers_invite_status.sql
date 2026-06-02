-- Fix teachers invite/account status columns for Admin -> Teachers.
-- Safe to run in Supabase SQL Editor. Does not drop data or policies.

create extension if not exists pgcrypto;

create table if not exists public.teachers (
  id uuid primary key default gen_random_uuid()
);

alter table public.teachers add column if not exists institute_id uuid;
alter table public.teachers add column if not exists user_id uuid;
alter table public.teachers add column if not exists name text;
alter table public.teachers add column if not exists email text;
alter table public.teachers add column if not exists phone text;
alter table public.teachers add column if not exists teacher_code text;
alter table public.teachers add column if not exists invite_code text;
alter table public.teachers add column if not exists invite_status text default 'pending';
alter table public.teachers add column if not exists invite_sent_at timestamptz;
alter table public.teachers add column if not exists status text default 'active';
alter table public.teachers add column if not exists created_at timestamptz default now();
alter table public.teachers add column if not exists updated_at timestamptz default now();

alter table public.teachers alter column invite_status set default 'pending';
alter table public.teachers alter column updated_at set default now();

update public.teachers
set invite_status = 'pending'
where invite_status is null or invite_status = '';

update public.teachers
set teacher_code = coalesce(nullif(teacher_code, ''), nullif(invite_code, ''))
where teacher_code is null or teacher_code = '';

create index if not exists idx_teachers_invite_status
  on public.teachers(invite_status);

create index if not exists idx_teachers_teacher_code
  on public.teachers(teacher_code);

notify pgrst, 'reload schema';
