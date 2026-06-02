# Deployment Checklist (Secrets & Configuration Hardening)

This checklist covers how to keep secrets out of git, how to configure Streamlit/Render safely, how to use `st.secrets`, and how to rotate keys.

> Target: PHASE 3 — Secrets and configuration hardening

---

## 1) Ensure secrets are not committed

### Repository / local dev
- **Never commit** these files:
  - `.streamlit/secrets.toml`
  - any `.env` / `.env.*` files
- This repo already ignores secrets by default via `sc_final/.gitignore`:
  - `.streamlit/secrets.toml`
  - `.env`, `.env.*`
  - `**/.streamlit/secrets.toml`

### Validate “ignored” behavior
- Confirm you do **not** see `SUPABASE_...`, `RAZORPAY_...`, `RESEND_...` keys in:
  - `README.md`
  - any `*.py` source
  - any tracked config files

---

## 2) Streamlit secret management (`st.secrets`)

### What to add
Add secrets in Streamlit Cloud (or locally via `secrets.toml`) under **Advanced Settings → Secrets**.

The code reads Supabase and Razorpay credentials from `st.secrets` keys:
- `SUPABASE_URL`
- `SUPABASE_KEY` *(or optionally `SUPABASE_ANON_KEY`)*
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

> Note: `src/database/client.py` reads `SUPABASE_KEY` first, then falls back to `SUPABASE_ANON_KEY`.

### Example `secrets.toml` (local)
Create `sc_final/.streamlit/secrets.toml` (do **not** commit it):

```toml
# Supabase
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_SERVICE_ROLE_OR_ANON_KEY"

# Razorpay
RAZORPAY_KEY_ID = "rzp_test_XXXX"
RAZORPAY_KEY_SECRET = "YOUR_RAZORPAY_SECRET"

# (If/when email provider is used)
# RESEND_API_KEY = "..."
```

### How to use `st.secrets` in code
- Access values safely:
  - `st.secrets.get("SUPABASE_URL")`
  - `st.secrets.get("RAZORPAY_KEY_SECRET")`
- Avoid printing secrets. Use presence checks and user-friendly error messages.

---

## 3) Render deployment secrets (environment variables)

When deploying on Render, store the same values as **environment variables**.

### Required environment variables
Set these environment variables on the Render service:
- `SUPABASE_URL`
- `SUPABASE_KEY` *(or `SUPABASE_ANON_KEY` if you use anon keys)*
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

### Important note about `st.secrets`
This app primarily uses Streamlit’s `st.secrets`.
- On Streamlit Cloud: secrets map naturally to `st.secrets`.
- On Render: you must ensure the runtime exposes secrets in a way Streamlit can read them.

Common approaches:
1. **Mount a `secrets.toml`** into the Streamlit app container.
2. Use a build/runtime step to generate `.streamlit/secrets.toml` from Render env vars.

If your Render configuration already mounts `sc_final/.streamlit/secrets.toml`, then no extra work is needed.

---

## 4) Key rotation (Supabase / Resend / Razorpay)

### Supabase rotation
1. Create new key in Supabase Dashboard (Keys section):
   - keep the old key active while you deploy
2. Update secrets:
   - `SUPABASE_KEY` (or `SUPABASE_ANON_KEY`)
3. Deploy/restart the app.
4. Verify:
   - login/auth works
   - database reads/writes work
5. Revoke the old key after a successful verification window.

### Resend rotation (if used)
1. Create a new Resend API key.
2. Update `RESEND_API_KEY` in secrets/env.
3. Redeploy.
4. Verify email sending.
5. Revoke the old key.

> This repo currently references an email service module; ensure the exact env var names match what that module expects before rotating.

### Razorpay rotation
1. Create new Razorpay test/live keys (depending on environment).
2. Update:
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
3. Redeploy/restart.
4. Verify payments end-to-end.
5. Revoke the old key.

> For safety, do not enable production/live Razorpay flow until payment verification + webhook handling are implemented (see Phase 6 docs).

---

## 5) Verification smoke tests (no secret leakage)

After setting secrets, run these checks:

### Local / staging
- Confirm Supabase client can be created (no traceback shown to end users).
- Confirm “connected” user flows:
  - login
  - load a dashboard page that reads from Supabase

### Production
- Confirm:
  - no “No secrets found” banner shown (if secrets are required)
  - no secret values appear in UI logs
  - any connection errors are user-friendly

---

## 6) Required environment variable reference (summary)

**Supabase**
- `SUPABASE_URL`
- `SUPABASE_KEY` *(preferred by this code)* **or** `SUPABASE_ANON_KEY`

**Razorpay**
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

**Resend (optional / if enabled by your email flow)**
- `RESEND_API_KEY`

