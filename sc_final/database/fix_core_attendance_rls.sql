-- Allow the MVP attendance flow to read/write core attendance tables.
-- Run this in Supabase SQL Editor for demo environments.

alter table public.attendance_sessions enable row level security;
alter table public.attendance_records enable row level security;

drop policy if exists "attendance_sessions_select_all" on public.attendance_sessions;
drop policy if exists "attendance_sessions_insert_all" on public.attendance_sessions;
drop policy if exists "attendance_sessions_update_all" on public.attendance_sessions;
drop policy if exists "attendance_sessions_delete_all" on public.attendance_sessions;

create policy "attendance_sessions_select_all"
on public.attendance_sessions
for select
to anon, authenticated
using (true);

create policy "attendance_sessions_insert_all"
on public.attendance_sessions
for insert
to anon, authenticated
with check (true);

create policy "attendance_sessions_update_all"
on public.attendance_sessions
for update
to anon, authenticated
using (true)
with check (true);

create policy "attendance_sessions_delete_all"
on public.attendance_sessions
for delete
to anon, authenticated
using (true);

drop policy if exists "attendance_records_select_all" on public.attendance_records;
drop policy if exists "attendance_records_insert_all" on public.attendance_records;
drop policy if exists "attendance_records_update_all" on public.attendance_records;
drop policy if exists "attendance_records_delete_all" on public.attendance_records;

create policy "attendance_records_select_all"
on public.attendance_records
for select
to anon, authenticated
using (true);

create policy "attendance_records_insert_all"
on public.attendance_records
for insert
to anon, authenticated
with check (true);

create policy "attendance_records_update_all"
on public.attendance_records
for update
to anon, authenticated
using (true)
with check (true);

create policy "attendance_records_delete_all"
on public.attendance_records
for delete
to anon, authenticated
using (true);
