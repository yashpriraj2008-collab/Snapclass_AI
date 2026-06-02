# Founder HQ Flow

SnapClass HQ is the platform-level control center. Founder users manage institutes, plans, access codes, reports, and data quality. Founders do not take daily attendance and do not normally add day-to-day students.

## Product Flow

1. Founder logs in.
2. Founder opens SnapClass HQ Dashboard.
3. Founder adds an institute or generates an access code.
4. Founder shares the code with the school or coaching admin.
5. School admin joins the institute with the code.
6. Admin creates classes and subjects.
7. Admin adds teachers and students.
8. Teacher marks attendance.
9. Student views attendance and reports.

## Founder Login

Founder login opens the SnapClass HQ area. After login, the dashboard shows institute counts, code counts, health metrics, revenue metrics, recent institutes, and data quality warnings.

## Add Institute

Use `Add Institute` from the dashboard or sidebar.

Expected fields:

- Institute Name
- City
- State
- Admin Name
- Admin Email
- Plan
- Attendance settings

After submit, the app creates or reuses the institute and can generate an access code.

## Generate Code

Use `Generate Access Code` from the dashboard or Institutes page.

Expected result:

- Access code
- Institute
- Admin email
- Expiry
- Copy action

The access code is shared with the institute admin.

## Join Institute Flow

The school admin uses the institute access code from the Join Institute page. The app validates the code, links the admin to the institute, and opens the admin portal.

## Manage Institutes

Founder Dashboard and Institutes page support:

- View details
- Edit institute
- Suspend institute
- Reactivate institute
- Delete Test Institute by soft status update
- Link Admin when a user profile already exists

Production records should not be hard-deleted from the Streamlit app.

## Data Quality Checks

The dashboard warns about:

- Institutes without linked admin profiles
- Possible duplicate institute rows
- Expired access codes
- Profiles without institute
- App users without matching profiles where detectable from public app tables

Because Streamlit uses the public Supabase anon client, the app does not inspect `auth.users` directly or use a service-role key.

## SQL Checks

Check duplicate institutes:

```sql
select
  lower(trim(name)) as institute_name,
  city,
  state,
  count(*) as duplicate_count
from public.institutes
group by lower(trim(name)), city, state
having count(*) > 1
order by duplicate_count desc;
```

Check institutes without admin:

```sql
select
  i.id,
  i.name,
  i.city,
  i.state,
  i.status
from public.institutes i
left join public.user_profiles up
  on up.institute_id = i.id
  and up.role in ('admin', 'institute_admin')
where up.id is null
order by i.created_at desc;
```

Check admin profiles:

```sql
select
  email,
  name,
  role,
  institute_id,
  status
from public.user_profiles
where role in ('admin', 'institute_admin')
order by created_at desc;
```

