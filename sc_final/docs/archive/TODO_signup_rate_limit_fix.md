# TODO - Fix plan signup rate-limit & account reuse (Surgical Mode)

## Information gathered
- `sc_final/src/screens/demo_signup.py` currently calls `create_demo_admin_account()` which internally calls Supabase `sign_up` (and may retry sign-up indirectly / double calls).
- There is existing safe signup logic in `sc_final/src/services/user_onboarding_service.py` but the screen uses the older implementation in this file.

## Plan
1. Implement required function `create_or_continue_admin_onboarding(email, password, institute_name, admin_name, city, state, phone, selected_plan_code)` in `user_onboarding_service.py`.
2. Update `create_demo_admin_account()` to reuse the new function or stop re-calling `sign_up` (only sign up after sign-in fails).
3. Update `sc_final/src/screens/demo_signup.py`:
   - Add `st.session_state['signup_in_progress']` guard.
   - Use `st.form` submit handler to prevent double-click.
   - Call only `create_or_continue_admin_onboarding(...)`.
   - Handle messages exactly as required (already exists, rate limited).
4. Ensure onboarding idempotency:
   - Reuse institute by existing profile/institute admin email.
   - Update `user_profiles` if exists.
   - Reuse subscription if it exists for institute.
5. Run `python -m compileall app.py src` and `pip check`.

## Followup steps
- Manual test checklist from the task.

