-- SnapClass AI — Full Schema v2
-- Run this entire file in your Supabase SQL Editor (one click)

-- ── Institutes ──────────────────────────────────────────────
create table if not exists institutes (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  city        text,
  state       text,
  address     text,
  institute_type text default 'School',
  admin_name  text,
  admin_email text,
  admin_phone text,
  plan        text default 'Demo',
  status      text default 'active',
  attendance_threshold integer default 75,
  academic_year text,
  onboarding_completed boolean default false,
  created_at  timestamptz default now()
);

-- Access codes for onboarding
create table if not exists school_codes (
  id           uuid primary key default gen_random_uuid(),
  code         text unique not null,
  institute_id uuid references institutes(id) on delete cascade,
  admin_email  text,
  status       text default 'unused',
  used_at      timestamptz,
  used_by      text,
  updated_at   timestamptz default now(),
  created_at   timestamptz default now(),
  expires_at   timestamptz
);


-- ── Teachers ─────────────────────────────────────────────────
create table if not exists teachers (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  email        text unique,
  phone        text,
  subject      text,
  class_name   text,
  institute_id uuid references institutes(id) on delete set null,
  created_at   timestamptz default now()
);

-- ── Teacher Assignments (Phase 1) ─────────────────────────────
-- Controls teacher permissions per institute.
-- class_teacher: teacher gets a single class (class_id)
-- subject_teacher: teacher gets a single subject (subject_id)
create table if not exists teacher_assignments (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid references institutes(id) on delete cascade,
  teacher_id uuid references teachers(id) on delete cascade,
  assignment_type text check (assignment_type in ('class_teacher','subject_teacher')) not null,
  class_name text,
  subject_id uuid references subjects(id) on delete cascade,
  class_id uuid references classes(id) on delete cascade,
  created_at timestamptz default now()
);


-- ── Students ─────────────────────────────────────────────────
create table if not exists students (
  id           uuid primary key default gen_random_uuid(),
  roll_no      text,
  name         text not null,
  email        text unique,
  class_name   text,
  institute_id uuid references institutes(id) on delete set null,
  created_at   timestamptz default now()
);

-- ── Subjects ─────────────────────────────────────────────────
create table if not exists subjects (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  teacher_id  uuid references teachers(id) on delete set null,
  class_name  text,
  created_at  timestamptz default now()
);

-- ── Attendance ───────────────────────────────────────────────
create table if not exists attendance (
  id               uuid primary key default gen_random_uuid(),
  student_id       uuid references students(id) on delete cascade,
  subject_id       uuid references subjects(id) on delete cascade,
  attendance_date  date not null,
  status           text check (status in ('present','absent')) not null,
  marked_by        text default 'teacher',
  created_at       timestamptz default now(),
  unique (student_id, subject_id, attendance_date)
);

-- ── Notifications ────────────────────────────────────────────
create table if not exists notifications (
  id          uuid primary key default gen_random_uuid(),
  student_id  uuid references students(id) on delete cascade,
  message     text not null,
  type        text default 'info',
  is_read     boolean default false,
  created_at  timestamptz default now()
);

-- ── Enable Row Level Security (RLS) ──────────────────────────
alter table institutes    enable row level security;
alter table school_codes enable row level security;
alter table teachers      enable row level security;
alter table students      enable row level security;
alter table subjects      enable row level security;
alter table attendance    enable row level security;
alter table notifications enable row level security;


-- Allow anon key full access (demo/dev mode — tighten per-role in production)
do $$
declare tbl text;
begin
  foreach tbl in array array['institutes','school_codes','teachers','students','subjects','attendance','notifications']

  loop
    execute format('drop policy if exists allow_all on %I', tbl);
    execute format('create policy allow_all on %I for all using (true) with check (true)', tbl);
  end loop;
end$$;

-- ── Seed Demo Data (only if tables are empty) ─────────────────

insert into institutes (name, city)
select name, city from (values
  ('Sunrise Academy', 'Mumbai'),
  ('Bright Coaching',  'Delhi'),
  ('Future Institute', 'Pune')
) as t(name, city)
where not exists (select 1 from institutes limit 1);

insert into teachers (name, email, subject, class_name)
select name, email, subject, class_name from (values
  ('Dr. Sharma',  'sharma@snapclass.ai',  'Mathematics', '12-A'),
  ('Prof. Gupta', 'gupta@snapclass.ai',   'Physics',     '12-A'),
  ('Dr. Patel',   'patel@snapclass.ai',   'Chemistry',   '12-B'),
  ('Ms. Rao',     'rao@snapclass.ai',     'English',     '11-A')
) as t(name, email, subject, class_name)
where not exists (select 1 from teachers limit 1);

insert into students (roll_no, name, email, class_name)
select roll_no, name, email, class_name from (values
  ('SC001', 'Yashraj Mehta', 'yashraj@demo.com', '12-A'),
  ('SC002', 'Aarav Singh',   'aarav@demo.com',   '12-A'),
  ('SC003', 'Meera Patel',   'meera@demo.com',   '12-A'),
  ('SC004', 'Kabir Khan',    'kabir@demo.com',   '12-A'),
  ('SC005', 'Riya Sharma',   'riya@demo.com',    '12-B'),
  ('SC006', 'Dev Joshi',     'dev@demo.com',     '12-B'),
  ('SC007', 'Ananya Rao',    'ananya@demo.com',  '11-A'),
  ('SC008', 'Rohan Verma',   'rohan@demo.com',   '11-A')
) as t(roll_no, name, email, class_name)
where not exists (select 1 from students limit 1);

insert into subjects (name, class_name)
select name, class_name from (values
  ('Mathematics', '12-A'),
  ('Physics',     '12-A'),
  ('Chemistry',   '12-B'),
  ('English',     '11-A'),
  ('Biology',     '12-A'),
  ('Computer Sc', '12-A')
) as t(name, class_name)
where not exists (select 1 from subjects limit 1);

-- ── Face Embeddings (Phase 3) ─────────────────────────────────
create table if not exists face_embeddings (
  id         uuid primary key default gen_random_uuid(),
  roll_no    text unique not null,
  name       text,
  embedding  text not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
alter table face_embeddings enable row level security;
drop policy if exists allow_all on face_embeddings;
create policy allow_all on face_embeddings for all using (true) with check (true);
