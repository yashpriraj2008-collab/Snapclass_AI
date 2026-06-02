-- Phase 7 — FaceID / AI Attendance Beta schema (DPDP/privacy aware)
-- Run in Supabase SQL Editor.

create extension if not exists pgcrypto;

-- 1) Face embeddings table
create table if not exists public.face_embeddings (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now()
);

alter table public.face_embeddings
  add column if not exists institute_id uuid;

alter table public.face_embeddings
  add column if not exists student_id uuid;

alter table public.face_embeddings
  add column if not exists user_id uuid;

alter table public.face_embeddings
  add column if not exists embedding jsonb;

alter table public.face_embeddings
  add column if not exists embedding_model text default 'deepface';

alter table public.face_embeddings
  add column if not exists image_quality_score numeric;

alter table public.face_embeddings
  add column if not exists consent_given boolean default false;

alter table public.face_embeddings
  add column if not exists consent_at timestamptz;

alter table public.face_embeddings
  add column if not exists status text default 'active';

alter table public.face_embeddings
  add column if not exists deleted_at timestamptz;

alter table public.face_embeddings
  add column if not exists updated_at timestamptz default now();

-- Backfill defaults where needed (best-effort)
update public.face_embeddings
set updated_at = now()
where updated_at is null;

-- Helpful indexes
create index if not exists idx_face_embeddings_student_id
  on public.face_embeddings(student_id);

create index if not exists idx_face_embeddings_user_id
  on public.face_embeddings(user_id);

create index if not exists idx_face_embeddings_institute_id
  on public.face_embeddings(institute_id);

-- Optional: keep only active rows logically (app filters)
-- (No hard unique constraint added to avoid breaking existing deployments.)

-- 2) Attendance schema tweaks (attendance_date + mode + verification metadata)
alter table public.attendance_sessions
  add column if not exists institute_id uuid,
  add column if not exists class_id uuid,
  add column if not exists subject_id uuid,
  add column if not exists teacher_id uuid,
  add column if not exists attendance_date date,
  add column if not exists mode text default 'manual',
  add column if not exists status text default 'completed',
  add column if not exists created_by uuid,
  add column if not exists created_at timestamptz default now(),
  add column if not exists updated_at timestamptz default now();

alter table public.attendance_records
  add column if not exists session_id uuid,
  add column if not exists student_id uuid,
  add column if not exists status text,
  add column if not exists attendance_date date,
  add column if not exists verification_method text default 'manual',
  add column if not exists confidence numeric,
  add column if not exists marked_at timestamptz default now(),
  add column if not exists created_at timestamptz default now();

-- Ensure RLS policies exist for face_embeddings (Phase 3+ prerequisite)
alter table public.face_embeddings enable row level security;

drop policy if exists "face_embeddings_student_own" on public.face_embeddings;
drop policy if exists "face_embeddings_teacher_read_assigned" on public.face_embeddings;
drop policy if exists "face_embeddings_admin_manage" on public.face_embeddings;

-- Student can manage their own embeddings
create policy "face_embeddings_student_own"
on public.face_embeddings
for all
to authenticated
using (
  user_id = auth.uid()
)
with check (
  user_id = auth.uid()
);

-- Teachers can read embeddings for students they teach (best-effort)
create policy "face_embeddings_teacher_read_assigned"
on public.face_embeddings
for select
to authenticated
using (
  student_id in (
    select st.id
    from public.students st
    where private.teacher_can_access_class(st.class_id)
  )
);

-- Admin/institute_admin manage within their institute
create policy "face_embeddings_admin_manage"
on public.face_embeddings
for all
to authenticated
using (
  institute_id = private.current_institute_id()
  and private.current_user_role() in ('admin', 'institute_admin')
)
with check (
  institute_id = private.current_institute_id()
  and private.current_user_role() in ('admin', 'institute_admin')
);
