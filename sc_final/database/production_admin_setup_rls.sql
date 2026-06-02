-- Production Admin Setup RLS
-- Prepared only. Do not apply automatically.
--
-- Goal:
-- - founder/super_admin can manage setup data across institutes
-- - admin/institute_admin can manage only rows for their own institute
-- - teacher/student cannot manage admin setup tables

begin;

create schema if not exists private;

create or replace function private.current_user_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(
    (select up.role from public.user_profiles up where up.user_id = auth.uid() limit 1),
    (select up.role from public.user_profiles up where up.id = auth.uid() limit 1),
    'student'
  )
$$;

create or replace function private.current_institute_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(
    (select up.institute_id from public.user_profiles up where up.user_id = auth.uid() limit 1),
    (select up.institute_id from public.user_profiles up where up.id = auth.uid() limit 1)
  )
$$;

create or replace function private.is_founder()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select private.current_user_role() in ('founder', 'super_admin', 'hq')
$$;

create or replace function private.is_institute_admin(target_institute uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select private.current_user_role() in ('admin', 'institute_admin')
     and private.current_institute_id() = target_institute
$$;

create or replace function private.current_teacher_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select t.id
  from public.teachers t
  where t.user_id = auth.uid()
  limit 1
$$;

create or replace function private.current_student_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select s.id
  from public.students s
  where s.user_id = auth.uid()
  limit 1
$$;

do $$
declare
  tbl text;
begin
  foreach tbl in array array[
    'classes',
    'subjects',
    'students',
    'teachers',
    'teacher_assignments',
    'user_profiles'
  ]
  loop
    if to_regclass('public.' || tbl) is not null then
      execute format('alter table public.%I enable row level security', tbl);
    end if;
  end loop;
end $$;

-- classes: admin setup table scoped by classes.institute_id
do $$
begin
  if to_regclass('public.classes') is not null then
    drop policy if exists prod_admin_setup_classes_select on public.classes;
    create policy prod_admin_setup_classes_select
      on public.classes for select
      using (
        private.is_founder()
        or private.is_institute_admin(institute_id)
        or exists (
          select 1 from public.teacher_assignments ta
          where ta.class_id = classes.id and ta.teacher_id = private.current_teacher_id()
        )
        or exists (
          select 1 from public.students s
          where s.class_id = classes.id and s.id = private.current_student_id()
        )
      );

    drop policy if exists prod_admin_setup_classes_insert on public.classes;
    create policy prod_admin_setup_classes_insert
      on public.classes for insert
      with check (private.is_founder() or private.is_institute_admin(institute_id));

    drop policy if exists prod_admin_setup_classes_update on public.classes;
    create policy prod_admin_setup_classes_update
      on public.classes for update
      using (private.is_founder() or private.is_institute_admin(institute_id))
      with check (private.is_founder() or private.is_institute_admin(institute_id));

    drop policy if exists prod_admin_setup_classes_delete on public.classes;
    create policy prod_admin_setup_classes_delete
      on public.classes for delete
      using (private.is_founder() or private.is_institute_admin(institute_id));
  end if;
end $$;

-- subjects: admin setup table scoped by subjects.institute_id
do $$
begin
  if to_regclass('public.subjects') is not null then
    drop policy if exists prod_admin_setup_subjects_select on public.subjects;
    create policy prod_admin_setup_subjects_select
      on public.subjects for select
      using (
        private.is_founder()
        or private.is_institute_admin(institute_id)
        or exists (
          select 1 from public.teacher_assignments ta
          where ta.subject_id = subjects.id and ta.teacher_id = private.current_teacher_id()
        )
        or exists (
          select 1 from public.subject_enrollments se
          where se.subject_id = subjects.id and se.student_id = private.current_student_id()
        )
      );

    drop policy if exists prod_admin_setup_subjects_insert on public.subjects;
    create policy prod_admin_setup_subjects_insert
      on public.subjects for insert
      with check (private.is_founder() or private.is_institute_admin(institute_id));

    drop policy if exists prod_admin_setup_subjects_update on public.subjects;
    create policy prod_admin_setup_subjects_update
      on public.subjects for update
      using (private.is_founder() or private.is_institute_admin(institute_id))
      with check (private.is_founder() or private.is_institute_admin(institute_id));

    drop policy if exists prod_admin_setup_subjects_delete on public.subjects;
    create policy prod_admin_setup_subjects_delete
      on public.subjects for delete
      using (private.is_founder() or private.is_institute_admin(institute_id));
  end if;
end $$;

-- students: admin manages institute rows; student can read own row
do $$
begin
  if to_regclass('public.students') is not null then
    drop policy if exists prod_admin_setup_students_select on public.students;
    create policy prod_admin_setup_students_select
      on public.students for select
      using (
        private.is_founder()
        or private.is_institute_admin(institute_id)
        or user_id = auth.uid()
        or id = private.current_student_id()
      );

    drop policy if exists prod_admin_setup_students_insert on public.students;
    create policy prod_admin_setup_students_insert
      on public.students for insert
      with check (private.is_founder() or private.is_institute_admin(institute_id));

    drop policy if exists prod_admin_setup_students_update on public.students;
    create policy prod_admin_setup_students_update
      on public.students for update
      using (private.is_founder() or private.is_institute_admin(institute_id))
      with check (private.is_founder() or private.is_institute_admin(institute_id));

    drop policy if exists prod_admin_setup_students_delete on public.students;
    create policy prod_admin_setup_students_delete
      on public.students for delete
      using (private.is_founder() or private.is_institute_admin(institute_id));
  end if;
end $$;

-- teachers: admin manages institute rows; teacher can read own row
do $$
begin
  if to_regclass('public.teachers') is not null then
    drop policy if exists prod_admin_setup_teachers_select on public.teachers;
    create policy prod_admin_setup_teachers_select
      on public.teachers for select
      using (
        private.is_founder()
        or private.is_institute_admin(institute_id)
        or user_id = auth.uid()
        or id = private.current_teacher_id()
      );

    drop policy if exists prod_admin_setup_teachers_insert on public.teachers;
    create policy prod_admin_setup_teachers_insert
      on public.teachers for insert
      with check (private.is_founder() or private.is_institute_admin(institute_id));

    drop policy if exists prod_admin_setup_teachers_update on public.teachers;
    create policy prod_admin_setup_teachers_update
      on public.teachers for update
      using (private.is_founder() or private.is_institute_admin(institute_id))
      with check (private.is_founder() or private.is_institute_admin(institute_id));

    drop policy if exists prod_admin_setup_teachers_delete on public.teachers;
    create policy prod_admin_setup_teachers_delete
      on public.teachers for delete
      using (private.is_founder() or private.is_institute_admin(institute_id));
  end if;
end $$;

-- teacher_assignments: admin manages institute assignment rows; teacher can read own assignments
do $$
begin
  if to_regclass('public.teacher_assignments') is not null then
    drop policy if exists prod_admin_setup_teacher_assignments_select on public.teacher_assignments;
    create policy prod_admin_setup_teacher_assignments_select
      on public.teacher_assignments for select
      using (
        private.is_founder()
        or private.is_institute_admin(institute_id)
        or teacher_id = private.current_teacher_id()
      );

    drop policy if exists prod_admin_setup_teacher_assignments_insert on public.teacher_assignments;
    create policy prod_admin_setup_teacher_assignments_insert
      on public.teacher_assignments for insert
      with check (private.is_founder() or private.is_institute_admin(institute_id));

    drop policy if exists prod_admin_setup_teacher_assignments_update on public.teacher_assignments;
    create policy prod_admin_setup_teacher_assignments_update
      on public.teacher_assignments for update
      using (private.is_founder() or private.is_institute_admin(institute_id))
      with check (private.is_founder() or private.is_institute_admin(institute_id));

    drop policy if exists prod_admin_setup_teacher_assignments_delete on public.teacher_assignments;
    create policy prod_admin_setup_teacher_assignments_delete
      on public.teacher_assignments for delete
      using (private.is_founder() or private.is_institute_admin(institute_id));
  end if;
end $$;

-- user_profiles: admins can manage profiles for their institute; users can read/update own profile
do $$
begin
  if to_regclass('public.user_profiles') is not null then
    drop policy if exists prod_admin_setup_user_profiles_select on public.user_profiles;
    create policy prod_admin_setup_user_profiles_select
      on public.user_profiles for select
      using (
        private.is_founder()
        or private.is_institute_admin(institute_id)
        or user_id = auth.uid()
        or id = auth.uid()
      );

    drop policy if exists prod_admin_setup_user_profiles_insert on public.user_profiles;
    create policy prod_admin_setup_user_profiles_insert
      on public.user_profiles for insert
      with check (
        private.is_founder()
        or private.is_institute_admin(institute_id)
        or user_id = auth.uid()
        or id = auth.uid()
      );

    drop policy if exists prod_admin_setup_user_profiles_update on public.user_profiles;
    create policy prod_admin_setup_user_profiles_update
      on public.user_profiles for update
      using (
        private.is_founder()
        or private.is_institute_admin(institute_id)
        or user_id = auth.uid()
        or id = auth.uid()
      )
      with check (
        private.is_founder()
        or private.is_institute_admin(institute_id)
        or user_id = auth.uid()
        or id = auth.uid()
      );

    drop policy if exists prod_admin_setup_user_profiles_delete on public.user_profiles;
    create policy prod_admin_setup_user_profiles_delete
      on public.user_profiles for delete
      using (private.is_founder() or private.is_institute_admin(institute_id));
  end if;
end $$;

commit;
