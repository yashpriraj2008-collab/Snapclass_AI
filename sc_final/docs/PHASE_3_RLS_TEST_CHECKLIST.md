# Phase 3 RLS Test Checklist

## Setup
- [ ] Phase 3 SQL tested on staging first
- [ ] Demo/open policies removed
- [ ] No policy uses using(true) for production tables
- [ ] No infinite recursion errors
- [ ] App uses anon key, not service role key

## Teacher Test
- [ ] Teacher can login
- [ ] Teacher can read own profile
- [ ] Teacher can read own teacher row
- [ ] Teacher can see assigned class
- [ ] Teacher can see assigned subject
- [ ] Teacher can see students in assigned class
- [ ] Teacher can create attendance session
- [ ] Teacher can create attendance records
- [ ] Teacher cannot see another teacher’s class
- [ ] Teacher cannot see another institute data

## Student Test
- [ ] Student can login
- [ ] Student can read own profile
- [ ] Student can read own student row
- [ ] Student can see own enrolled subjects
- [ ] Student can see own attendance history
- [ ] Student cannot see another student’s records

## Admin Test
- [ ] Admin can login
- [ ] Admin can see own institute
- [ ] Admin can manage own teachers
- [ ] Admin can manage own students
- [ ] Admin cannot see other institute data

## Founder Test
- [ ] Founder can login
- [ ] Founder can see all institutes
- [ ] Founder can manage all platform data

## Final
- [ ] Manual attendance still works
- [ ] Student reports still work
- [ ] Share subject still works
- [ ] No raw database error visible to normal users

## Exact order to run Phase 3
Do this on staging:

1. Backup database
2. Run phase3_preflight.sql
3. Fix schema/data problems
4. Run phase3_indexes.sql
5. Run phase3_private_rls_helpers.sql
6. Run phase3_production_rls.sql
7. Run phase3_remove_demo_policies.sql
8. Restart app
9. Test teacher flow
10. Test student flow
11. Test admin/founder flow
12. Try forbidden access tests

If anything breaks:

- Do not keep changing random code.
- Open Developer Error.
- Find table/policy causing block.
- Fix that exact policy.
- Retest same step.

Forbidden access tests

Create or use 2 teachers and 2 students.

Teacher A → Class 12-A → Physics
Teacher B → Class 11-A → Chemistry
Student A → Class 12-A
Student B → Class 11-A

Tests:

- Teacher A should not see Teacher B’s class
- Teacher A should not see Student B
- Student A should not see Student B attendance
- Admin Institute A should not see Institute B

If any of these fail, RLS is not secure.

Common Phase 3 errors and fixes

Error 1: infinite recursion

Cause:
policy on user_profiles queries user_profiles

Fix:
Use auth.uid() directly
or use private.security_definer helper

Error 2: data disappears after RLS

Cause:
Policy too strict
wrong ID used
teacher_id is auth.users.id instead of teachers.id

Fix:
Check session_state teacher_id
Check teacher_assignments.teacher_id = teachers.id

Error 3: teacher can login but cannot see subjects

Cause:
subjects policy blocks teacher
teacher_assignments missing or wrong teacher_id

Fix:
select *
from public.teacher_assignments
where teacher_id = '<public.teachers.id>';

Error 4: student history blank

Cause:
attendance_records policy blocks student
student_id mismatch

Fix:
select id, user_id, email
from public.students
where email = 'student.demo@test.com';

Then confirm:
select *
from public.attendance_records
where student_id = '<students.id>';

