# RLS Test Checklist — Phase 2 (Staging)

After applying Phase 2 changes on staging, test:

- [ ] App starts
- [ ] Supabase connected
- [ ] Teacher login works
- [ ] Teacher dashboard opens
- [ ] My Classes shows 12-A Physics
- [ ] Share Subject shows join code
- [ ] Manual Attendance shows Demo Student
- [ ] Attendance save works
- [ ] attendance_sessions row created
- [ ] attendance_records row created
- [ ] Student login works
- [ ] My Subjects shows Physics
- [ ] Attendance History shows saved attendance
- [ ] Reports show saved attendance
- [ ] No RLS recursion error
- [ ] No blank page
- [ ] No raw HTML visible

If any test fails, stop and rollback RLS changes on staging before applying to main.

