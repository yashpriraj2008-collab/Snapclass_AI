-- Demo Admin Setup RLS
-- Use only for local/demo testing. This intentionally allows all operations.
-- Do not use this as production RLS.

begin;

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
      execute format('drop policy if exists demo_admin_setup_allow_all on public.%I', tbl);
      execute format(
        'create policy demo_admin_setup_allow_all on public.%I for all using (true) with check (true)',
        tbl
      );
    end if;
  end loop;
end $$;

commit;
