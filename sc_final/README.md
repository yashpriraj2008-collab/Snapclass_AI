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

## Production Status

This repo is not production-ready until:

- live Teacher -> Attendance -> Student Reports works,
- production RLS is applied and tested,
- demo allow-all policies are removed,
- secrets are rotated and protected,
- face embeddings are protected,
- app is deployed to a public URL and smoke-tested,
- payments are verified end-to-end or disabled.
