# Phase 7 FaceID QA Checklist

## Setup
- [ ] App starts without error
- [ ] Manual attendance still works
- [ ] FaceID page opens
- [ ] Missing DeepFace does not crash app

## Consent
- [ ] Consent checkbox appears
- [ ] Enrollment blocked without consent
- [ ] Consent timestamp saved
- [ ] Delete FaceID option available

## Enrollment
- [ ] Student login works
- [ ] student_id resolves
- [ ] Camera capture works
- [ ] Upload image works
- [ ] Face embedding generated
- [ ] face_embeddings row saved
- [ ] Enrollment status shown

## FaceID Attendance
- [ ] Subject dropdown works
- [ ] Camera/upload option works
- [ ] Face match works
- [ ] Attendance session created
- [ ] Attendance record created
- [ ] mode = faceid
- [ ] verification_method = faceid
- [ ] Student history shows attendance

## Failure Cases
- [ ] No face detected shows clean message
- [ ] Multiple faces shows clean message
- [ ] Unknown face does not mark attendance
- [ ] Missing enrollment asks user to enroll first
- [ ] Face engine missing does not crash app

## Beta / Privacy checks
- [ ] Face raw embeddings are never shown in normal UI
- [ ] Face data is withdrawable/deletable from enrollment screen
- [ ] RLS prevents unauthorized access to face_embeddings

