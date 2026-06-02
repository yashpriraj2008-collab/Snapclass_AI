# TODO - Student code UX + invite/registration flow (Student registration UX + correctness)

## Step 1: Update Student Register UI
- [ ] In `sc_final/src/screens/auth.py` (function `show_student_auth` -> tab `Register`):
  - [ ] Change helper text below “Roll Number or Student Code” exactly as provided.
  - [ ] Add small button/link “I don’t have a code”.
  - [ ] On click, show the required message about contacting teacher/admin.
  - [ ] Ensure helper UI does not change theme/sidebar/unrelated pages.

## Step 2: Fix registration logic/validation
- [ ] In `sc_final/src/screens/auth.py` register handler:
  - [ ] If student_code_or_roll_no empty => show required message prompting teacher/admin.
  - [ ] Update call to onboarding service if needed.

## Step 3: Update onboarding service to follow required verification rules
- [ ] In `sc_final/src/services/user_onboarding_service.py` (`register_student_with_code`):
  - [ ] Enforce that student must match existing public.students record.
  - [ ] Verify by (email + roll_no) OR (email + student_code) in `public.students`.
  - [ ] Keep existing behavior but adjust error messages to the required set.

## Step 4: Update teacher/admin student creation UI to show generated code + copy buttons
- [ ] In `sc_final/src/screens/institute_students.py` (Add New Student section):
  - [ ] After adding student, ensure code is displayed.
  - [ ] Add “Copy Code” button.
  - [ ] Add “Copy Invite Message” with invite template.

## Step 5: Ensure required empty/error state messages
- [ ] Confirm the UI shows one of:
  - Invalid student code. Please ask your teacher/admin.
  - Student account already exists. Please login.
  - No student record found. Ask your teacher/admin to add you first.

## Step 6: Run checks
- [ ] `python -m compileall app.py src`
- [ ] `pip check`

## Step 7: Manual test checklist
- [ ] Admin/teacher adds student; Student code shown.
- [ ] Student registers with correct code.
- [ ] `students.user_id` filled.
- [ ] `user_profiles` row created with role='student'.
- [ ] Student dashboard opens.

