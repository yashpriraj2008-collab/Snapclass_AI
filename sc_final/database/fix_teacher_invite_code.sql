-- Fix teacher invite code support for Teacher Create Account.
-- Safe to run in Supabase SQL Editor. Does not drop data, foreign keys, or policies.

create extension if not exists pgcrypto;

create table if not exists public.teachers (
  id uuid primary key default gen_random_uuid()
);

alter table public.teachers add column if not exists teacher_code text;
alter table public.teachers add column if not exists email text;
alter table public.teachers add column if not exists status text default 'active';
alter table public.teachers add column if not exists invite_code text;
alter table public.teachers add column if not exists invite_status text default 'pending';
alter table public.teachers add column if not exists invite_sent_at timestamptz;
alter table public.teachers add column if not exists user_id uuid;
alter table public.teachers add column if not exists updated_at timestamptz default now();

alter table public.teachers alter column invite_status set default 'pending';
alter table public.teachers alter column updated_at set default now();

update public.teachers
set invite_code = teacher_code
where invite_code is null
  and teacher_code is not null;

update public.teachers
set invite_status = 'pending'
where invite_status is null or invite_status = '';

do $$
begin
  if not exists (
    select 1
    from public.teachers
    where invite_code is not null
    group by invite_code
    having count(*) > 1
  ) then
    create unique index if not exists uq_teachers_invite_code
      on public.teachers(invite_code)
      where invite_code is not null;
  else
    raise notice 'Skipped unique invite_code index because duplicate invite codes exist.';
  end if;
end $$;

create index if not exists idx_teachers_email_lower
  on public.teachers(lower(email));

notify pgrst, 'reload schema';
