-- Fix/extend schema for teacher-subject join codes.
-- Safe to run multiple times.

begin;

-- Ensure table exists (if not, app-level inserts will fail).
create table if not exists public.subject_join_codes (
  id uuid primary key default gen_random_uuid(),
  subject_id uuid not null,
  teacher_id uuid not null,
  join_code text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- If updated_at exists but no trigger, keep it simple with a lightweight trigger.
-- (DEMO ONLY: these are demo policies, not production hardening.)
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_subject_join_codes_updated_at on public.subject_join_codes;
create trigger trg_subject_join_codes_updated_at
before update on public.subject_join_codes
for each row execute function public.set_updated_at();

-- Indexes
create index if not exists idx_subject_join_codes_subject_id
  on public.subject_join_codes (subject_id);

create index if not exists idx_subject_join_codes_teacher_id
  on public.subject_join_codes (teacher_id);

-- Unique code constraint/index
create unique index if not exists ux_subject_join_codes_join_code
  on public.subject_join_codes (join_code);

-- RLS (DEMO ONLY policy examples)
alter table public.subject_join_codes enable row level security;

-- DEMO ONLY
-- Allow teachers to manage only their own join codes.
-- (In production, tighten based on institute/institute_id relationships.)
create policy "demo_teachers_manage_their_join_codes"
on public.subject_join_codes
for all
using (true)
with check (true);

-- Notify PostgREST cache to reload schema
notify pgrst, 'reload schema';

commit;

