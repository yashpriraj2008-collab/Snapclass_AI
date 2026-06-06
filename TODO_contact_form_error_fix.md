# TODO: SnapClass AI contact form RLS fix

## Planned changes
- Update UI: remove/ensure “Developer Debug” is never shown to normal users.
- Fix contact form error handling: always show the friendly message to real users.
- Verify payload fields mapping to `public.contact_messages` columns.
- Fix Supabase schema/migration for `public.contact_messages`:
  - create table if not exists
  - enable RLS
  - allow anon + authenticated INSERT only
  - allow authenticated SELECT only
  - do not disable RLS

## Steps
1. Confirm current contact page UI and payload mapping.
2. Confirm current contact_service insert + error handling.
3. Implement UI hiding: remove Developer Debug expander entirely (or ensure only dev + never for normal).
4. Implement schema migration SQL file with safe RLS policies.
5. (Optional) Add/adjust payload mapping in contact_service to match schema columns.
6. Run minimal checks / dry-run migration (if applicable).

