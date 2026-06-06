-- Fix public contact form inserts without disabling RLS.
-- Run this in Supabase SQL Editor if the Contact page shows:
-- "new row violates row-level security policy for table contact_messages"

create table if not exists public.contact_messages (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  institute_name text,
  email text not null,
  phone text,
  inquiry_type text not null,
  student_count text,
  subject text not null,
  message text not null,
  status text not null default 'new',
  source text not null default 'website',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.contact_messages enable row level security;

grant insert on public.contact_messages to anon, authenticated;
grant select, update on public.contact_messages to authenticated;

drop policy if exists contact_messages_insert_anon on public.contact_messages;
drop policy if exists contact_messages_public_insert on public.contact_messages;
create policy contact_messages_public_insert
on public.contact_messages
for insert
to anon, authenticated
with check (
  coalesce(status, 'new') = 'new'
  and coalesce(source, 'website') in ('website', 'landing_contact_form')
);

drop policy if exists contact_messages_founder_read_update on public.contact_messages;
create policy contact_messages_founder_read_update
on public.contact_messages
for all
to authenticated
using (private.is_founder())
with check (private.is_founder());
