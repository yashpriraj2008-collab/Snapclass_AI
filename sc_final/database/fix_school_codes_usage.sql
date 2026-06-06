-- SnapClass AI: access-code usage lifecycle columns.
-- Run once in Supabase SQL Editor.

alter table public.school_codes
add column if not exists status text default 'unused';

alter table public.school_codes
add column if not exists used_at timestamptz;

alter table public.school_codes
add column if not exists used_by text;

alter table public.school_codes
add column if not exists institute_id uuid;

alter table public.school_codes
add column if not exists updated_at timestamptz default now();

create index if not exists idx_school_codes_code_upper
on public.school_codes (upper(code));

create index if not exists idx_school_codes_status
on public.school_codes (status);

-- Backfill old invite codes that were used before the lifecycle columns existed
-- or before the app reliably marked the row after onboarding.
update public.school_codes sc
set
  status = 'used',
  used_by = coalesce(sc.used_by, up.email, sc.admin_email),
  used_at = coalesce(sc.used_at, up.created_at, now()),
  updated_at = now()
from public.user_profiles up
where sc.institute_id = up.institute_id
  and lower(coalesce(up.role, '')) in ('admin', 'institute_admin')
  and (
    sc.admin_email is null
    or sc.admin_email = ''
    or lower(sc.admin_email) = lower(up.email)
  )
  and lower(coalesce(sc.status, 'unused')) = 'unused';
