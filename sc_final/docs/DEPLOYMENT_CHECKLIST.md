# Deployment Checklist

Status: deployment is not production-ready until live Supabase Auth, RLS, and the attendance/report flow pass.

## Required Secrets

Configure these in Streamlit Cloud or the deployment platform:

- `APP_ENV=production`
- `DEMO_AUTH_ENABLED=false`
- `APP_PUBLIC_URL`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` or `SUPABASE_KEY` containing an anon key
- `RESEND_API_KEY` if email is enabled
- `SENDER_EMAIL` if email is enabled
- `RAZORPAY_KEY_ID` if payments are enabled
- `RAZORPAY_KEY_SECRET` if payments are enabled
- `RAZORPAY_WEBHOOK_SECRET` before live Razorpay webhooks

Do not use a Supabase service-role key in the Streamlit app.

## Secret Safety

- `.streamlit/secrets.toml` must remain ignored by Git.
- `.env` and `.env.*` must remain ignored by Git.
- Do not print secrets in UI, logs, README, or debug files.
- Rotate exposed or previously shared keys before production.

## Pre-Deployment Checks

1. `python -m compileall app.py src`
2. `python -m pip check`
3. `streamlit run app.py`
4. Confirm no local-only URLs remain in generated join links.
5. Confirm `APP_PUBLIC_URL` is configured.
6. Confirm demo auth is disabled in production.

## Database Checks

1. Back up Supabase.
2. Run `database/production_schema_preflight.sql`.
3. Run `database/production_constraints_indexes.sql`.
4. Create real Supabase Auth users.
5. Fix `public.user_profiles` mappings.
6. Verify teacher assignments and subject enrollments.
7. Verify attendance session/record writes.
8. Remove demo policies.
9. Apply production RLS.
10. Re-test all roles.

## Post-Deployment Smoke Test

1. App opens on public URL.
2. Supabase connection succeeds.
3. Founder login works.
4. Admin login works.
5. Teacher login works.
6. Student login works.
7. Teacher saves attendance.
8. Student history and reports update.
9. SnapBot opens and closes.
10. Payments are disabled or test-mode only.

## Key Rotation

Rotate before production:

- Supabase anon key if it was exposed.
- Resend API key if it was exposed.
- Razorpay keys if they were exposed.

Deploy with new keys, smoke test, then revoke old keys.

