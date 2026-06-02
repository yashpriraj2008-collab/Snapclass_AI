-- Contact / Support / Demo Request leads table for SnapClass AI.
-- Run this in Supabase SQL Editor.

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

create index if not exists idx_contact_messages_status
  on public.contact_messages(status);

create index if not exists idx_contact_messages_created_at
  on public.contact_messages(created_at desc);

alter table public.contact_messages enable row level security;

-- Public website visitors can create leads.
drop policy if exists contact_messages_insert_anon on public.contact_messages;
create policy contact_messages_insert_anon
on public.contact_messages
for insert
to anon, authenticated
with check (true);

drop policy if exists contact_messages_founder_read_update on public.contact_messages;
create policy contact_messages_founder_read_update
on public.contact_messages
for all
to authenticated
using (private.is_founder())
with check (private.is_founder());
