-- SnapClass AI - safe schema alignment fixes
--
-- Purpose:
-- - Non-destructive SQL for columns/tables the app expects.
-- - Does not remove data.
-- - Does not apply production RLS.
-- - Does not create Supabase Auth users.
--
-- Run after taking a database backup and before production RLS.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Identity and profiles
-- ---------------------------------------------------------------------------

alter table public.user_profiles
  add column if not exists user_id uuid,
  add column if not exists email text,
  add column if not exists full_name text,
  add column if not exists role text,
  add column if not exists institute_id uuid,
  add column if not exists status text default 'active';

create index if not exists idx_user_profiles_email on public.user_profiles (lower(email));
create index if not exists idx_user_profiles_role on public.user_profiles (role);
create index if not exists idx_user_profiles_institute_id on public.user_profiles (institute_id);

-- ---------------------------------------------------------------------------
-- Core attendance shape used by the Streamlit app
-- ---------------------------------------------------------------------------

alter table public.attendance_sessions
  add column if not exists institute_id uuid,
  add column if not exists teacher_id uuid,
  add column if not exists class_id uuid,
  add column if not exists subject_id uuid,
  add column if not exists attendance_date date,
  add column if not exists mode text default 'manual',
  add column if not exists status text default 'completed',
  add column if not exists created_by uuid,
  add column if not exists updated_at timestamptz default now();

alter table public.attendance_records
  add column if not exists session_id uuid,
  add column if not exists student_id uuid,
  add column if not exists status text,
  add column if not exists attendance_date date,
  add column if not exists verification_method text default 'manual',
  add column if not exists confidence numeric,
  add column if not exists marked_at timestamptz default now(),
  add column if not exists created_at timestamptz default now(),
  add column if not exists updated_at timestamptz default now();

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'attendance_records_session_id_fkey'
      and conrelid = 'public.attendance_records'::regclass
  ) then
    alter table public.attendance_records
      add constraint attendance_records_session_id_fkey
      foreign key (session_id)
      references public.attendance_sessions(id)
      on delete cascade;
  end if;
end $$;

create index if not exists idx_attendance_sessions_scope_date
  on public.attendance_sessions (teacher_id, class_id, subject_id, date);
create index if not exists idx_attendance_records_session_id
  on public.attendance_records (session_id);
create index if not exists idx_attendance_records_student_id
  on public.attendance_records (student_id);

-- ---------------------------------------------------------------------------
-- Subject enrollment and join code alignment
-- ---------------------------------------------------------------------------

alter table public.subject_enrollments
  add column if not exists status text default 'active',
  add column if not exists join_code text;

alter table public.subject_join_codes
  add column if not exists join_code text,
  add column if not exists join_url text,
  add column if not exists is_active boolean default true,
  add column if not exists expires_at timestamptz;

create unique index if not exists ux_subject_join_codes_join_code
  on public.subject_join_codes (join_code)
  where join_code is not null and btrim(join_code) <> '';

create unique index if not exists ux_subject_enrollments_student_subject
  on public.subject_enrollments (student_id, subject_id);

-- ---------------------------------------------------------------------------
-- Payment beta tables. Keep live payments disabled until signatures and
-- webhooks are verified end to end.
-- ---------------------------------------------------------------------------

create table if not exists public.payments (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid,
  plan_id uuid,
  user_email text,
  amount integer,
  plan text,
  payment_id text,
  order_id text,
  status text default 'created',
  created_at timestamptz default now()
);

create table if not exists public.payment_events (
  id uuid primary key default gen_random_uuid(),
  provider text default 'razorpay',
  event_type text,
  event_id text,
  order_id text,
  payment_id text,
  status text,
  payload jsonb,
  created_at timestamptz default now()
);

alter table public.plans
  add column if not exists code text,
  add column if not exists price integer,
  add column if not exists currency text default 'INR',
  add column if not exists status text default 'active';

alter table public.subscriptions
  add column if not exists institute_id uuid,
  add column if not exists plan_id uuid,
  add column if not exists status text default 'inactive',
  add column if not exists current_period_start timestamptz,
  add column if not exists current_period_end timestamptz,
  add column if not exists updated_at timestamptz default now();

alter table public.payment_links
  add column if not exists institute_id uuid,
  add column if not exists plan_id uuid,
  add column if not exists amount integer,
  add column if not exists status text default 'created';

create unique index if not exists ux_payments_payment_id
  on public.payments (payment_id)
  where payment_id is not null and btrim(payment_id) <> '';

create unique index if not exists ux_payment_events_event_id
  on public.payment_events (event_id)
  where event_id is not null and btrim(event_id) <> '';

-- ---------------------------------------------------------------------------
-- Preflight report. These must be fixed before production RLS.
-- ---------------------------------------------------------------------------

select 'missing_founder_profile' as check_name, count(*) as issue_count
from public.user_profiles
where lower(email) = 'founder@snapclass.ai'
  and role = 'founder'
having count(*) = 0
union all
select 'missing_teacher_profile', count(*)
from public.user_profiles
where lower(email) = 'teacher.demo@test.com'
  and role = 'teacher'
  and institute_id is not null
having count(*) = 0
union all
select 'missing_student_profile', count(*)
from public.user_profiles
where lower(email) = 'student.demo@test.com'
  and role = 'student'
  and institute_id is not null
having count(*) = 0
union all
select 'missing_teacher_assignment', count(*)
from public.teacher_assignments ta
join public.teachers t on t.id = ta.teacher_id
where lower(t.email) = 'teacher.demo@test.com'
having count(*) = 0
union all
select 'missing_attendance_session_rows', count(*)
from public.attendance_sessions
having count(*) = 0
union all
select 'missing_attendance_record_rows', count(*)
from public.attendance_records
having count(*) = 0;
