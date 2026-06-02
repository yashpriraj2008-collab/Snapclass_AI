# Production Deployment Plan

## Runtime

- Python: 3.11
- Command: `streamlit run app.py`
- Install: `pip install -r requirements.txt`

## Deployment Options

1. Streamlit Community Cloud
   - Best for simple demo/beta.
   - Configure secrets in Advanced Settings.

2. Render
   - Better control over environment variables and process settings.
   - Ensure Streamlit can read secrets or generate `.streamlit/secrets.toml` at runtime.

3. Later backend architecture
   - Required for robust Razorpay webhooks because raw webhook body handling is easier in a backend API.
   - Keep service-role operations out of the Streamlit frontend.

## Before Deploying

1. Confirm `.venv311` is ignored and not pushed.
2. Confirm `.streamlit/secrets.toml` is ignored and not pushed.
3. Confirm `.env` files are ignored and not pushed.
4. Run `python -m compileall app.py src`.
5. Run `python -m pip check`.
6. Run `streamlit run app.py`.
7. Verify no debug files are required.
8. Verify `APP_PUBLIC_URL` is set for join links.
9. Verify production RLS has been tested in Supabase.

## Deployment Secrets

Required:

- `APP_ENV`
- `DEMO_AUTH_ENABLED`
- `APP_PUBLIC_URL`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

Optional until enabled:

- `RESEND_API_KEY`
- `SENDER_EMAIL`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`

## Post-Deployment Smoke Test

1. App opens.
2. Supabase connects.
3. Founder login works.
4. Teacher login works.
5. Student login works.
6. Teacher attendance save creates `attendance_sessions`.
7. Teacher attendance save creates `attendance_records`.
8. Student history shows record.
9. Student reports show percentage.
10. SnapBot opens/closes.
11. Payment stays disabled or test-only.

## Release Gate

Do not call the deployment production-ready until the smoke test passes on the public URL with production RLS enabled.

