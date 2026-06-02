# Phase 7 — FaceID / AI Attendance Beta (Plan)

## Goals
- Keep Manual Attendance as stable production feature.
- Make FaceID attendance beta/optional.
- Do not crash if DeepFace/engine is missing.
- Add privacy-safe consent + delete/withdraw consent.
- Persist face embeddings with a DPDP-conscious data model.

## Target flow (Phase 7)
Student logs in
→ Student gives consent
→ Student enrolls face
→ Face embedding saves in Supabase
→ Student/teacher opens FaceID Attendance
→ App detects face
→ Matches with enrolled embedding
→ Attendance saves into attendance_sessions + attendance_records
→ Student sees attendance in history/reports

## What to implement
### 1) Consent before face enrollment
UI must include:
- FaceID Attendance is optional
- Face data used only for attendance verification
- User can delete FaceID data anytime
- Manual attendance always available
- Checkbox gating enrollment
- Parent/guardian consent required for students under 18 (when DOB/age is available)

### 2) Fix face enrollment data model
Create/update:
- `public.face_embeddings` with columns: 
  `id, institute_id, student_id, user_id, embedding, embedding_model, image_quality_score, consent_given, consent_at, status, created_at, updated_at, deleted_at`

### 3) Add FaceID service layer
Create/implement `src/services/face_service.py` functions:
- `is_faceid_available()`
- `extract_face_embedding(image)`
- `save_face_embedding(student_id, user_id, institute_id, embedding)`
- `get_student_embedding(student_id)`
- `delete_face_embedding(student_id)`
- `compare_faces(live_embedding, stored_embedding)`
- `mark_face_attendance(student_id, subject_id, class_id, teacher_id)`

### 4) Decide one face engine
Prefer DeepFace.
If DeepFace is missing or broken:
- Show: "FaceID engine is not available on this system. Manual attendance is still available."
- Do not fake success.
- Manual attendance remains available.

### 5) Fix enrollment page
`src/screens/student_faceid.py` updates:
- FaceID beta label
- Consent checkbox
- Camera/upload option
- Face quality check
- Save FaceID button
- Enrollment status
- Delete FaceID data button
- Developer Debug expander with safe information

### 6) Fix FaceID attendance page
Same file updates:
- Subject selector
- Date selector
- Camera/upload option
- Verify & Mark Attendance button
- Clean success/failure messages
- On match:
  - Create/update attendance session with `mode='faceid'`
  - Create attendance record with `verification_method='faceid'` and confidence if available

### 7) Privacy & safety requirements
- Consent checkbox + delete/withdraw consent
- Face data not visible in normal UI
- RLS on `face_embeddings`
- Beta label and manual fallback

## Files created/updated (Phase 7)
Created:
- `sc_final/database/phase7_faceid_schema.sql`
- `sc_final/docs/PHASE_7_FACEID_PLAN.md`
- `sc_final/docs/PHASE_7_FACEID_TEST_CHECKLIST.md`

Updated (expected):
- `sc_final/src/services/face_service.py`
- `sc_final/src/screens/student_faceid.py`
- `sc_final/src/services/attendance_service.py`
- `sc_final/requirements.txt` (only if missing deps)

## Execution order
1. Add SQL schema + RLS for face_embeddings + attendance metadata.
2. Refactor/add face_service layer.
3. Update student_faceid UI: consent gating, delete, debug expander.
4. Update FaceID attendance to save sessions/records with mode/verification metadata.
5. Update attendance_service for `verification_method` + `confidence` fields.
6. Run compile + pip check.
7. Manual regression + Phase 7 QA checklist.

