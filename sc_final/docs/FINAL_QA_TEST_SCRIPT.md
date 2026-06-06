# SnapClass AI Final QA Test Script

Use this script against a clean Supabase test project with seeded test users for Founder, Admin, Teacher, and Student. Do not use production data.

## 1. Public Visitor Flow
1. Open the app landing page.
2. Verify Home, Features, Pricing, Contact, Admin Login, Teacher Login, Student Login, and Founder HQ navigation.
3. Click Pricing.
4. Click Get Free Demo or Start Free Trial and confirm Demo Signup opens.
5. Click Join Institute and confirm the access-code form opens.
6. Submit Contact with valid data and verify `contact_messages` receives a row.
7. Remove/disable Resend test key and submit Contact again. Expected: lead saves and app does not crash.

## 2. Founder Login
1. Open Founder HQ login.
2. Login with a founder or super_admin user.
3. Verify non-founder users are rejected with a clean message.
4. Verify wrong password, missing profile, and unconfirmed email show clean errors.

## 3. Founder Generate Code
1. Open Founder Dashboard.
2. Open Institutes and verify institute list, admin status, plan/status, and duplicate warnings if data exists.
3. Open Generate Code.
4. Select an institute, enter admin email, set expiry days, and generate code.
5. Verify code is stored and Copy Code / Copy Invite Message are visible.
6. Open All Codes and verify code, institute, admin email, expiry, and status.

## 4. Admin Join Institute
1. Open Join Institute.
2. Enter a valid founder-generated code.
3. Complete institute/admin setup.
4. Login as admin and confirm Admin Dashboard opens.

## 5. Admin Create Class
1. Open Classes & Subjects.
2. Create class with class name, section, and academic year.
3. Submit twice and verify no duplicate class is created.
4. Verify row has `institute_id`.

## 6. Admin Add Teacher
1. Open Teachers.
2. Add teacher with name, email, and phone if available.
3. Verify teacher row and profile mapping.
4. Verify teacher invite/code text is understandable.

## 7. Admin Add Student
1. Open Students.
2. Add student with name, email, roll number, class, and section.
3. Verify student appears in the list and has class linkage.
4. Verify student code/invite copy is understandable.

## 8. Admin Create Subject
1. Open Classes & Subjects.
2. Add a subject for the created class.
3. Assign teacher to class/subject.
4. Verify subject has `class_id`, `institute_id`, and teacher assignment if selected.

## 9. Teacher Login
1. Login as assigned teacher.
2. Verify Dashboard shows only assigned classes/subjects.
3. Login as a teacher with no assignment. Expected: "No class assigned yet. Contact admin."

## 10. Teacher Manual Attendance
1. Open Manual Attendance.
2. Select assigned class, subject, and date.
3. Verify student list loads.
4. Mark present/absent/late and Save.
5. Re-save same date and verify records update, not duplicate.
6. Verify `attendance_sessions` and `attendance_records`.

## 11. Student Login
1. Login as student.
2. Verify role guard blocks non-students.
3. If no class is linked, expect: "Your class is not assigned yet. Contact admin."
4. Verify Dashboard shows name, class/section, subjects, and attendance summary.

## 12. Student FaceID Enroll
1. Open FaceID Attendance.
2. If dependencies are missing, expect: "FaceID is currently unavailable. Use manual attendance."
3. If available, enroll face.
4. Verify `face_embeddings` row links to `student_id` or `user_id`.

## 13. Student FaceID Mark Attendance
1. Select an enrolled subject.
2. Capture/upload face image.
3. Verify matching succeeds or shows a clean failure.
4. Confirm attendance writes to `attendance_sessions` and `attendance_records`.

## 14. Student Attendance History
1. Open Attendance History.
2. Verify manual and FaceID records appear.
3. Verify empty state is clean when no records exist.

## 15. Reports
1. Open Student Reports.
2. Verify summary and CSV export when records exist.
3. Open Teacher Reports and verify class/date filters and CSV export.
4. Open Admin Reports if implemented; otherwise verify clean "not implemented" state.

## 16. Contact Form
1. Submit valid contact form.
2. Verify Supabase save.
3. Verify missing Resend key shows no crash.

## 17. Razorpay Test Mode
1. Open Pricing.
2. Click paid plan.
3. If keys are missing, expect: "Payment setup is not configured yet."
4. If keys are configured, verify Razorpay test checkout opens.
5. Open payment success without redirect params. Expected: "Missing Razorpay redirect parameters."

## 18. Resend Email Check
1. Verify `RESEND_API_KEY` status in Founder Settings if available.
2. With key missing, expected message: "Email service is not configured yet."
3. With key configured, verify test/contact notification sends and optional `email_logs` row is created if table exists.

## 19. Mobile Check
Test 360x800, 390x844, 412x915, 768x1024, and desktop.
1. Verify sidebar does not cover content.
2. Verify forms are full-width and readable.
3. Verify pricing cards stack.
4. Verify dropdown text is visible.
5. Verify tables scroll horizontally.
6. Verify chatbot bubble does not hide primary buttons.

## Required Commands
```powershell
python -m compileall app.py src
pip check
streamlit run app.py --server.port 8507
```
