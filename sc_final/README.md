# SnapClass AI

AI-powered attendance management SaaS for institutes, teachers, students, admins, and SnapClass HQ.

## Local Development

Run the app from the `sc_final` folder so Streamlit can find `.streamlit/secrets.toml` next to `app.py`:

```bash
cd "C:\Working Project's\snapclass_final yash\sc_final"
.\.venv311\Scripts\Activate.ps1
streamlit run app.py --server.port 8507
```

If you need to create the virtual environment first:

```bash
py -3.11 -m venv .venv311
.\.venv311\Scripts\Activate.ps1
pip install -r requirements.txt
```

Python 3.11 is required for the current FaceID dependency set.

## Demo Credentials

These are for local/demo testing only. Production must use real Supabase Auth users and matching `user_profiles`.

| Portal | Email | Password |
| --- | --- | --- |
| Founder | founder@snapclass.ai | `<local-founder-password>` |
| Teacher | teacher.demo@example.com | `<local-teacher-password>` |
| Student | student.demo@example.com | `<local-student-password>` |

## Required Production Secrets

Configure these in Streamlit secrets or the deployment platform. Do not commit `.streamlit/secrets.toml`.

```toml
APP_ENV = "production"
DEMO_AUTH_ENABLED = "false"
APP_PUBLIC_URL = "https://your-public-app-url"
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"
RESEND_API_KEY = "YOUR_RESEND_API_KEY"
SENDER_EMAIL = "YOUR_VERIFIED_SENDER_EMAIL"
RAZORPAY_KEY_ID = "YOUR_RAZORPAY_KEY_ID"
RAZORPAY_KEY_SECRET = "YOUR_RAZORPAY_KEY_SECRET"
RAZORPAY_WEBHOOK_SECRET = "YOUR_RAZORPAY_WEBHOOK_SECRET"
```

Never use a Supabase service-role key in this Streamlit frontend app.

## Production Database Sequence

Do not run production RLS until the live attendance flow passes and mappings are correct.

1. Back up Supabase.
2. Run `database/production_schema_preflight.sql`.
3. Run `database/production_constraints_indexes.sql`.
4. Create or reset real Supabase Auth users.
5. Insert/fix `public.user_profiles` for founder, admin, teacher, and student.
6. Verify teacher assignments, subject enrollments, and attendance writes.
7. Run `database/remove_demo_policies.sql`.
8. Run `database/production_rls_policies.sql`.
9. Re-test founder, admin, teacher, student, FaceID, and reporting flows.

## Render Deployment (Python 3.11 + Streamlit)

Render uses a build step that can fail/slow down when heavy ML deps (tensorflow/deepface/opencv) are involved.

### Start command (Render)
Set the **Start Command** to exactly:

```bash
cd sc_final && streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

### Python version
Use `runtime.txt` to force Python 3.11.9:
- `sc_final/runtime.txt` must contain: `python-3.11.9`


### Secrets (no hardcoding)
The app reads secrets from:
- `os.getenv(...)` for runtime values like `APP_BASE_URL`, `RESEND_API_KEY` (where applicable)
- `st.secrets` + optional local `.streamlit/secrets.toml` via `src/database/client.py::read_app_secrets()`

On Render, set these as environment variables (keys must match exactly):

```toml
APP_ENV = "production"
DEMO_AUTH_ENABLED = "false"
APP_PUBLIC_URL = "https://your-public-app-url"
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"
RESEND_API_KEY = "YOUR_RESEND_API_KEY"
SENDER_EMAIL = "YOUR_VERIFIED_SENDER_EMAIL"
RAZORPAY_KEY_ID = "YOUR_RAZORPAY_KEY_ID"
RAZORPAY_KEY_SECRET = "YOUR_RAZORPAY_KEY_SECRET"
RAZORPAY_WEBHOOK_SECRET = "YOUR_RAZORPAY_WEBHOOK_SECRET"
```

Never store Supabase **service_role** keys in Render.

### Smoke test after deploy
Once Render shows the app, test the following flows:
- Founder login + dashboard
- Teacher login + Manual Attendance screen
- Teacher login + AI Attendance (must not crash; may be slower cold-start)
- Teacher login + QR joining / subject join code screen
- Student login + Student Subjects
- Student FaceID Attendance: Enroll FaceID + Mark Attendance
- Admin/Institute portal attendance + reports
- Payment: start checkout and verify access activation (or disable payments if you are in schema-testing)

## Production Status

This repo is not production-ready until:

- live Teacher -> Attendance -> Student Reports works,
- production RLS is applied and tested,
- demo allow-all policies are removed,
- secrets are rotated and protected,
- face embeddings are protected,
- app is deployed to a public URL and smoke-tested,
- payments are verified end-to-end or disabled.

## Final Deployment Checklist (Render)

- [ ] `sc_final/runtime.txt` is `python-3.11.9`
- [ ] `sc_final/requirements.txt` works on Python 3.11 (TensorFlow/DeepFace stack preserved)
- [ ] `opencv-python-headless` is installed (not GUI opencv)
- [ ] Render Start Command set to:
  - `cd sc_final && streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- [ ] Render environment variables are set (all required keys)
- [ ] No secrets are committed to git
- [ ] Supabase RLS policies enabled only after FaceID + attendance writes are verified
- [ ] Payments verified end-to-end or disabled until webhook verification is confirmed
- [ ] Cold start tested for AI/FaceID paths (expect a slow first import)

