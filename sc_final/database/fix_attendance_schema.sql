create table if not exists public.attendance (
    id uuid primary key default gen_random_uuid(),
    student_id uuid references public.students(id) on delete cascade,
    class_id uuid references public.classes(id) on delete cascade,
    subject_id uuid references public.subjects(id) on delete cascade,
    attendance_date date not null,
    status text not null default 'present',
    marked_by uuid references auth.users(id),
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create unique index if not exists attendance_unique_student_session
on public.attendance(student_id, class_id, subject_id, attendance_date);

alter table public.attendance enable row level security;

drop policy if exists "attendance_select_all" on public.attendance;
drop policy if exists "attendance_insert_all" on public.attendance;
drop policy if exists "attendance_update_all" on public.attendance;
drop policy if exists "attendance_delete_all" on public.attendance;

create policy "attendance_select_all"
on public.attendance
for select
to anon, authenticated
using (true);

create policy "attendance_insert_all"
on public.attendance
for insert
to anon, authenticated
with check (true);

create policy "attendance_update_all"
on public.attendance
for update
to anon, authenticated
using (true)
with check (true);

create policy "attendance_delete_all"
on public.attendance
for delete
to anon, authenticated
using (true);

