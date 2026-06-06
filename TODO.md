# TODO

- [x] Implement founder access production-ready (Supabase Auth only, fetch user_profiles role, remove unsafe dev bypass in production, show explicit error when role missing).
- [x] Implement Resend email service interface: `is_email_configured()` and `send_email()` using `requests.post`.
- [x] Update founder settings UI to use `is_email_configured()` and show warning instead of crash; ensure no secrets shown.
- [x] Hide founder settings from normal users: add `require_founder()` guard and remove/keep debug visibility only for founder/super_admin.
- [ ] Update test steps in final response and run basic import sanity checks.


