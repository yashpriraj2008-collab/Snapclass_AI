# SnapClass AI - Demo Accounts Template

Use this file as a local reference only. Do not store real passwords or live service keys in repository docs.

## Teacher
- **Email:** `teacher.demo@example.com`
- **Password:** `<local-demo-password>`

## Student
- **Email:** `student.demo@example.com`
- **Password:** `<local-demo-password>`

## Notes
- Replace placeholders only in private local notes.
- Supabase-backed identity requires matching rows in:
  - `public.user_profiles` (role must be `teacher` / `student`)
  - `public.teachers` / `public.students`
