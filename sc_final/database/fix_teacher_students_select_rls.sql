-- Allow authenticated teachers to read students only from their assigned classes.
-- Existing founder, institute-admin, and student self-access policies remain intact.

alter table public.students enable row level security;

drop policy if exists teacher_assigned_students_select on public.students;
create policy teacher_assigned_students_select
  on public.students
  for select
  to authenticated
  using (
    exists (
      select 1
      from public.teacher_assignments ta
      join public.teachers t on t.id = ta.teacher_id
      where ta.teacher_id = private.current_teacher_id()
        and ta.class_id = students.class_id
        and t.institute_id = students.institute_id
        and lower(trim(coalesce(ta.status, 'active'))) = 'active'
    )
  );

create index if not exists idx_teacher_assignments_teacher_class_active
  on public.teacher_assignments (teacher_id, class_id)
  where lower(trim(coalesce(status, 'active'))) = 'active';
