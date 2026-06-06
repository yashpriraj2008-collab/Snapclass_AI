-- Profile photos and institute logos.
-- Run in the Supabase SQL Editor before enabling uploads in the app.

alter table public.user_profiles
add column if not exists profile_photo_url text;

alter table public.students
add column if not exists profile_photo_url text;

alter table public.teachers
add column if not exists profile_photo_url text;

alter table public.institutes
add column if not exists logo_url text;

insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'profile-photos',
  'profile-photos',
  true,
  2097152,
  array['image/jpeg', 'image/png']
)
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "profile_photos_public_read" on storage.objects;
create policy "profile_photos_public_read"
on storage.objects for select
using (bucket_id = 'profile-photos');

drop policy if exists "profile_photos_authenticated_insert" on storage.objects;
create policy "profile_photos_authenticated_insert"
on storage.objects for insert
to authenticated
with check (bucket_id = 'profile-photos');

drop policy if exists "profile_photos_authenticated_update" on storage.objects;
create policy "profile_photos_authenticated_update"
on storage.objects for update
to authenticated
using (bucket_id = 'profile-photos')
with check (bucket_id = 'profile-photos');
