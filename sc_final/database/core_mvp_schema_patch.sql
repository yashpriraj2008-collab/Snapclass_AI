-- SnapClass AI Core MVP Schema Patch
-- Run this in Supabase SQL Editor AFTER your existing schema.sql.
-- Safe patch: does not drop existing data.

-- Optional but recommended for UUID generation in Supabase/Postgres.
create extension if not exists pgcrypto;

-- -------------------------------------------------------------------
-- 1) Teachers
-- -------------------------------------------------------------------
create table if not exists public.teachers (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid references public.institutes(id) on delete set null,
  user_id uuid,
  email text,
  name text,
  subject text,
  phone text,
  invite_code text,
  invite_status text default 'invited',
  status text default 'invited',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.teachers add column if not exists institute_id uuid references public.institutes(id) on delete set null;
alter table public.teachers add column if not exists user_id uuid;
alter table public.teachers add column if not exists email text;
alter table public.teachers add column if not exists name text;
alter table public.teachers add column if not exists subject text;
alter table public.teachers add column if not exists phone text;
alter table public.teachers add column if not exists invite_code text;
alter table public.teachers add column if not exists invite_status text default 'invited';
alter table public.teachers add column if not exists status text default 'invited';
alter table public.teachers add column if not exists updated_at timestamptz default now();

-- -------------------------------------------------------------------
-- 2) Classes
-- -------------------------------------------------------------------
create table if not exists public.classes (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid references public.institutes(id) on delete set null,
  teacher_id uuid references public.teachers(id) on delete set null,
  class_name text,
  name text,
  section text,
  academic_year text,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.classes add column if not exists institute_id uuid references public.institutes(id) on delete set null;
alter table public.classes add column if not exists teacher_id uuid references public.teachers(id) on delete set null;
alter table public.classes add column if not exists class_name text;
alter table public.classes add column if not exists name text;
alter table public.classes add column if not exists section text;
alter table public.classes add column if not exists academic_year text;
alter table public.classes add column if not exists status text default 'active';
alter table public.classes add column if not exists updated_at timestamptz default now();

-- -------------------------------------------------------------------
-- 3) Students
-- -------------------------------------------------------------------
create table if not exists public.students (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid references public.institutes(id) on delete set null,
  class_id uuid references public.classes(id) on delete set null,
  email text,
  name text,
  roll_no text,
  student_code text,
  invite_status text default 'invited',
  section text,
  admission_no text,
  status text default 'invited',
  phone text,
  parent_name text,
  parent_phone text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.students add column if not exists institute_id uuid references public.institutes(id) on delete set null;
alter table public.students add column if not exists class_id uuid references public.classes(id) on delete set null;
alter table public.students add column if not exists email text;
alter table public.students add column if not exists name text;
alter table public.students add column if not exists roll_no text;
alter table public.students add column if not exists student_code text;
alter table public.students add column if not exists invite_status text default 'invited';
alter table public.students add column if not exists section text;
alter table public.students add column if not exists admission_no text;
alter table public.students add column if not exists status text default 'invited';
alter table public.students add column if not exists phone text;
alter table public.students add column if not exists parent_name text;
alter table public.students add column if not exists parent_phone text;
alter table public.students add column if not exists updated_at timestamptz default now();

-- -------------------------------------------------------------------
-- 4) Subjects
-- -------------------------------------------------------------------
create table if not exists public.subjects (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid references public.institutes(id) on delete set null,
  class_id uuid references public.classes(id) on delete set null,
  teacher_id uuid references public.teachers(id) on delete set null,
  name text,
  subject_name text,
  code text,
  subject_code text,
  section text,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.subjects add column if not exists institute_id uuid references public.institutes(id) on delete set null;
alter table public.subjects add column if not exists class_id uuid references public.classes(id) on delete set null;
alter table public.subjects add column if not exists teacher_id uuid references public.teachers(id) on delete set null;
alter table public.subjects add column if not exists name text;
alter table public.subjects add column if not exists subject_name text;
alter table public.subjects add column if not exists code text;
alter table public.subjects add column if not exists subject_code text;
alter table public.subjects add column if not exists section text;
alter table public.subjects add column if not exists status text default 'active';
alter table public.subjects add column if not exists updated_at timestamptz default now();

-- -------------------------------------------------------------------
-- 5) Teacher assignments
-- -------------------------------------------------------------------
create table if not exists public.teacher_assignments (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid references public.institutes(id) on delete set null,
  teacher_id uuid not null references public.teachers(id) on delete cascade,
  class_id uuid not null references public.classes(id) on delete cascade,
  subject_id uuid references public.subjects(id) on delete cascade,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(teacher_id, class_id, subject_id)
);

alter table public.teacher_assignments add column if not exists institute_id uuid references public.institutes(id) on delete set null;
alter table public.teacher_assignments add column if not exists teacher_id uuid references public.teachers(id) on delete cascade;
alter table public.teacher_assignments add column if not exists class_id uuid references public.classes(id) on delete cascade;
alter table public.teacher_assignments add column if not exists subject_id uuid references public.subjects(id) on delete cascade;
alter table public.teacher_assignments add column if not exists status text default 'active';
alter table public.teacher_assignments add column if not exists updated_at timestamptz default now();

-- -------------------------------------------------------------------
-- 6) Subject join codes
-- -------------------------------------------------------------------
create table if not exists public.subject_join_codes (
  id uuid primary key default gen_random_uuid(),
  subject_id uuid not null references public.subjects(id) on delete cascade,
  teacher_id uuid references public.teachers(id) on delete set null,
  join_code text unique not null,
  join_url text,
  is_active boolean default true,
  expires_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.subject_join_codes add column if not exists teacher_id uuid references public.teachers(id) on delete set null;
alter table public.subject_join_codes add column if not exists join_url text;
alter table public.subject_join_codes add column if not exists is_active boolean default true;
alter table public.subject_join_codes add column if not exists expires_at timestamptz;
alter table public.subject_join_codes add column if not exists updated_at timestamptz default now();

-- -------------------------------------------------------------------
-- 7) Subject enrollments
-- -------------------------------------------------------------------
create table if not exists public.subject_enrollments (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  subject_id uuid not null references public.subjects(id) on delete cascade,
  join_code text,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(student_id, subject_id)
);

alter table public.subject_enrollments add column if not exists join_code text;
alter table public.subject_enrollments add column if not exists status text default 'active';
alter table public.subject_enrollments add column if not exists updated_at timestamptz default now();

-- -------------------------------------------------------------------
-- 8) Attendance sessions
-- -------------------------------------------------------------------
create table if not exists public.attendance_sessions (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid references public.institutes(id) on delete set null,
  teacher_id uuid references public.teachers(id) on delete set null,
  class_id uuid references public.classes(id) on delete set null,
  subject_id uuid references public.subjects(id) on delete set null,
  attendance_date date not null,
  mode text default 'manual',
  status text default 'completed',
  created_by uuid,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(class_id, subject_id, attendance_date, mode)
);

alter table public.attendance_sessions add column if not exists institute_id uuid references public.institutes(id) on delete set null;
alter table public.attendance_sessions add column if not exists teacher_id uuid references public.teachers(id) on delete set null;
alter table public.attendance_sessions add column if not exists class_id uuid references public.classes(id) on delete set null;
alter table public.attendance_sessions add column if not exists subject_id uuid references public.subjects(id) on delete set null;
alter table public.attendance_sessions add column if not exists attendance_date date;
alter table public.attendance_sessions add column if not exists mode text default 'manual';
alter table public.attendance_sessions add column if not exists status text default 'completed';
alter table public.attendance_sessions add column if not exists created_by uuid;
alter table public.attendance_sessions add column if not exists updated_at timestamptz default now();

-- -------------------------------------------------------------------
-- 9) Attendance records
-- -------------------------------------------------------------------
create table if not exists public.attendance_records (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.attendance_sessions(id) on delete cascade,
  student_id uuid not null references public.students(id) on delete cascade,
  status text not null check (status in ('present','absent','late')),
  marked_by uuid,
  marked_at timestamptz default now(),
  attendance_date date,
  class_id uuid references public.classes(id) on delete set null,
  subject_id uuid references public.subjects(id) on delete set null,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(session_id, student_id)
);

alter table public.attendance_records add column if not exists session_id uuid references public.attendance_sessions(id) on delete cascade;
alter table public.attendance_records add column if not exists student_id uuid references public.students(id) on delete cascade;
alter table public.attendance_records add column if not exists status text not null default 'present';
alter table public.attendance_records add column if not exists attendance_date date;
alter table public.attendance_records add column if not exists verification_method text default 'manual';
alter table public.attendance_records add column if not exists confidence numeric;
alter table public.attendance_records add column if not exists marked_by uuid;
alter table public.attendance_records add column if not exists marked_at timestamptz default now();
alter table public.attendance_records add column if not exists created_at timestamptz default now();
alter table public.attendance_records add column if not exists updated_at timestamptz default now();

-- -------------------------------------------------------------------
-- 10) Face embeddings
-- -------------------------------------------------------------------
create table if not exists public.face_embeddings (
  id uuid primary key default gen_random_uuid(),
  student_id uuid references public.students(id) on delete cascade,
  user_id uuid,
  user_email text,
  user_name text,
  roll_no text,
  name text,
  embedding text not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(student_id)
);

alter table public.face_embeddings add column if not exists student_id uuid references public.students(id) on delete cascade;
alter table public.face_embeddings add column if not exists user_id uuid;
alter table public.face_embeddings add column if not exists user_email text;
alter table public.face_embeddings add column if not exists user_name text;
alter table public.face_embeddings add column if not exists roll_no text;
alter table public.face_embeddings add column if not exists name text;
alter table public.face_embeddings add column if not exists updated_at timestamptz default now();
alter table public.face_embeddings alter column roll_no drop not null;

-- -------------------------------------------------------------------
-- Useful indexes
-- -------------------------------------------------------------------
create index if not exists idx_teachers_email on public.teachers(email);
create index if not exists idx_teachers_institute_id on public.teachers(institute_id);
create index if not exists idx_teachers_invite_code on public.teachers(invite_code);

create index if not exists idx_classes_institute_id on public.classes(institute_id);
create index if not exists idx_classes_teacher_id on public.classes(teacher_id);

create index if not exists idx_students_email on public.students(email);
create index if not exists idx_students_roll_no on public.students(roll_no);
create index if not exists idx_students_class_id on public.students(class_id);
create index if not exists idx_students_student_code on public.students(student_code);

create index if not exists idx_subjects_class_id on public.subjects(class_id);
create index if not exists idx_subjects_teacher_id on public.subjects(teacher_id);
create index if not exists idx_subjects_institute_id on public.subjects(institute_id);

create index if not exists idx_teacher_assignments_teacher_id on public.teacher_assignments(teacher_id);
create index if not exists idx_teacher_assignments_class_id on public.teacher_assignments(class_id);
create index if not exists idx_teacher_assignments_subject_id on public.teacher_assignments(subject_id);

create index if not exists idx_subject_join_codes_subject_id on public.subject_join_codes(subject_id);
create index if not exists idx_subject_enrollments_student_id on public.subject_enrollments(student_id);
create index if not exists idx_attendance_records_student_id on public.attendance_records(student_id);
create index if not exists idx_attendance_sessions_date on public.attendance_sessions(attendance_date);
create index if not exists idx_face_embeddings_student_id on public.face_embeddings(student_id);
create index if not exists idx_face_embeddings_user_email on public.face_embeddings(user_email);

-- NOTE (MVP constraint): keep this patch limited to CREATE/ALTER ONLY.
-- No RLS policy setup and no destructive migration in this file.
