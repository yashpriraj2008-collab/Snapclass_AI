-- Add missing user_profiles table (for Supabase Auth app-specific profile)

create table if not exists user_profiles (
  id uuid primary key,
  user_id uuid nullable unique,
  email text unique not null,
  full_name text,
  role text not null,
  status text default 'active',
  subject text nullable,
  roll_no text nullable,
  class_name text nullable,
  institute_id uuid,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Helpful indexes
create index if not exists user_profiles_user_id_idx on user_profiles(user_id);
create index if not exists user_profiles_role_idx on user_profiles(role);
create index if not exists user_profiles_email_idx on user_profiles(email);

alter table user_profiles add column if not exists status text default 'active';


-- Row Level Security
alter table user_profiles enable row level security;

-- NOTE: For this refactor we keep policies permissive for dev unless your project already has policies.
-- Replace policies with least-privilege rules for production.

do $$
declare p text;
begin
  -- Drop existing dev policies if any
  foreach p in array array['allow_all']
  loop
    execute format('drop policy if exists %I on user_profiles', p);
  end loop;

  execute 'create policy allow_all on user_profiles for all using (true) with check (true)';
end$$;
