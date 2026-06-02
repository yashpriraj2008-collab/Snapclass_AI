# QA Test Plan

## Founder

- Login with real Supabase Auth founder account.
- View institute list.
- Create institute.
- Generate access code.
- View plans.
- View reports.
- Open settings.
- Confirm founder can see HQ-level data only as intended.

## Admin / Institute Admin

- Login with real Supabase Auth admin account.
- Create class.
- Create subject.
- Add teacher.
- Add student.
- Assign teacher to class/subject.
- View institute reports.
- Confirm admin cannot see another institute.

## Teacher

- Login with real Supabase Auth teacher account.
- Resolve `public.teachers.id` from login email.
- See assigned Class 12-A / Physics.
- Generate subject join code.
- Mark Demo Student present.
- Confirm `attendance_sessions` row exists.
- Confirm `attendance_records` row exists.
- View reports.
- Confirm teacher cannot see unassigned classes/subjects.

## Student

- Login with real Supabase Auth student account.
- Resolve `public.students.id` from login email.
- Join subject with code.
- View Attendance History.
- View Reports percentage.
- Download CSV.
- Open FaceID page.
- Enroll FaceID.
- Confirm student cannot see another student's records.

## Security

- Student can select only own `students` row.
- Student can select only own attendance records.
- Teacher can select only assigned class/subject.
- Teacher cannot read all face embeddings.
- Admin can manage only own institute.
- Founder access matches HQ design.
- Demo allow-all policies are removed.
- Production RLS policies are enabled and tested.

## Payment

- Create order server-side.
- Reject tampered amount.
- Verify checkout signature.
- Verify webhook signature from raw body.
- Handle `payment.captured`.
- Handle `payment.failed`.
- Handle refunds/cancellations if enabled.
- Upgrade subscription only after verified payment/webhook.

## UI

- No raw HTML visible.
- Dropdown selected values are readable.
- Mobile layout is usable.
- SnapBot opens/closes and does not block buttons.
- Empty states are present.
- Fake/demo data is clearly labeled.

