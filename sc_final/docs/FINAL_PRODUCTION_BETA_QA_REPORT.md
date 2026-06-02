# SnapClass AI Final Production-Beta QA Report

Date: 2026-06-01

## Verification Summary

| Area | Status | Notes |
| --- | --- | --- |
| FaceID enrollment | FAIL / blocked | Code now resolves student by `auth_user_id` first, then email, and writes required metadata when Phase 7 schema is present. Live enrollment was not completed because no logged-in student/photo flow was available in this CLI pass. |
| FaceID attendance save | FAIL / blocked | Code now creates `attendance_sessions` and `attendance_records` without using student auth id as `teacher_id`. Live save still requires a logged-in enrolled student and working FaceID engine/photo. |
| Manual attendance | FAIL / blocked | Service path compiles and renders. Live teacher save was not completed because the current smoke route has no logged-in teacher session; direct route shows a clean missing-teacher message. |
| Student history/reports | PASS with empty-state | History, analytics, and reports render without exceptions and use `attendance_records`; empty states are shown when no resolved student/records exist. |
| Razorpay order/payment/subscription | FAIL / blocked | Razorpay keys are configured, but `starter` plan lookup is blocked/not visible through the current Supabase client/RLS path, so order creation cannot be verified. Direct `payment_success` without params shows a clean info message. |
| Resend email/logs | PASS / config-ready | `RESEND_API_KEY` is configured locally and ignored by git. Test-email UI and `email_logs` persistence path are implemented. Production still needs `SENDER_EMAIL` set to a verified Resend sender/domain before real sends. |
| GitHub safety | PASS | `.streamlit/secrets.toml` and `.env` are ignored. Hardcoded-key scan found no committed keys; only service-role detection code/comments were matched. |

## Commands Run

- `python -m compileall app.py src` - PASS
- `pip check` - PASS
- Streamlit route smoke test - PASS for no exceptions
- Required table visibility check - Supabase reachable; required tables respond
- Hardcoded key scan - PASS, no committed secrets found

## Files Modified In This QA Pass

- `src/services/student_identity.py`
- `src/services/face_ai_service.py`
- `src/screens/student_faceid.py`
- `src/services/payment_service.py`
- `src/screens/pricing.py`
- `src/screens/payment_success.py`
- `src/services/email_service.py`
- `src/screens/founder_settings.py`
- `src/screens/student_dashboard.py`
- `docs/FINAL_PRODUCTION_BETA_QA_REPORT.md`

Note: the worktree already contained many unrelated pending changes before this QA pass; those were not reverted.

## SQL Changes Required

Run/confirm these in Supabase before final live beta sign-off:

1. `database/phase7_faceid_schema.sql`
   - Required for `face_embeddings.institute_id`, `consent_given`, `consent_at`, `status`, and FaceID metadata.

2. `database/phase5_payment_schema.sql`
   - Required for `plans`, `payment_orders`, `payments`, and `subscriptions`.
   - Confirm `starter` plan exists with `amount_paise = 49900`.

3. `database/phase6_email_schema.sql`
   - Required for `email_logs`.

4. RLS/policy follow-up
   - `plans` must be readable by the app client for pricing/order creation.
   - `payment_orders` must allow the logged-in institute admin flow to insert order rows.
   - `payments` and `subscriptions` must allow the verified payment success path.
   - `face_embeddings` must allow the logged-in student to insert/update their own row.
   - `attendance_sessions` and `attendance_records` must allow teacher manual saves and student FaceID saves according to the beta policy.

## Remaining Blockers

- `SENDER_EMAIL` is not configured in local secrets. Add a verified Resend sender/domain before production email.
- `starter` plan is not visible through the current app client/RLS path, blocking Razorpay order verification.
- Full live FaceID enrollment/attendance requires a logged-in student, clear face image/camera, Phase 7 schema, and working DeepFace runtime.
- Full manual attendance requires a real logged-in teacher with active `teacher_assignments`, class, subject, and students.
- Payment success/subscription activation requires a real Razorpay checkout callback with `razorpay_order_id`, `razorpay_payment_id`, and `razorpay_signature`.
