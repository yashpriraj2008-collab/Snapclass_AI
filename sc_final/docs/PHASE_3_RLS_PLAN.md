# Phase 3 RLS Plan (Secure Supabase RLS)

## Objective
Implement Phase 3: Secure Supabase RLS.

- Do **not** redesign UI.
- Edit only **data access**.
- Assume all production RLS must be tested on **staging** first.

## Hard rules (Streamlit / Supabase)
- Never use a **service role key** in Streamlit frontend.
- App must use Streamlit anon + authenticated user session.
- Teacher pages must use:
  - `auth_user_id = st.session_state["auth_user_id"]`
  - `teacher_id = st.session_state["teacher_id"]`
  - `institute_id = st.session_state["institute_id"]`
- Student pages must use:
  - `auth_user_id = st.session_state["auth_user_id"]`
  - `student_id = st.session_state["student_id"]`
  - `institute_id = st.session_state["institute_id"]`
- Teacher queries must filter:
  - `.eq("teacher_id", teacher_id)`
  - `.eq("institute_id", institute_id)`
- Student queries must filter:
  - `.eq("student_id", student_id)`
  - `.eq("user_id", auth_user_id)`

Rationale: Supabase recommends adding explicit filters because policies can act like implicit WHERE clauses; explicit filters improve performance.

## SQL files to create
- `database/phase3_preflight.sql`
- `database/phase3_indexes.sql`
- `database/phase3_private_rls_helpers.sql`
- `database/phase3_remove_demo_policies.sql`
- `database/phase3_production_rls.sql`

## App code to update (data access only)
- Ensure all teacher/student queries (where implemented in Streamlit screens/services) include the explicit filters above.
- Add collapsed Developer Debug outputs only where needed:
  - teacher_id
  - student_id
  - institute_id
  - role
  - current page
  - last Supabase error

## Testing checklist
- Create `docs/PHASE_3_RLS_TEST_CHECKLIST.md` and follow it.

## Staging execution order (must follow)
1. Backup database
2. Run `phase3_preflight.sql`
3. Fix schema/data problems
4. Run `phase3_indexes.sql`
5. Run `phase3_private_rls_helpers.sql`
6. Run `phase3_production_rls.sql`
7. Run `phase3_remove_demo_policies.sql`
8. Restart app
9. Test teacher flow
10. Test student flow
11. Test admin/founder flow
12. Try forbidden access tests

## Common Phase 3 failures
- **Infinite recursion**: policies on `user_profiles` querying `user_profiles`.
  - Fix: use `auth.uid()` directly or use a private security-definer helper.
- **Data disappears after RLS**: policy too strict or wrong IDs used.
  - Fix: verify session_state IDs and mappings to table FK columns.
- **Teacher cannot see subjects**: missing/incorrect `teacher_assignments.teacher_id`.
- **Student history blank**: `attendance_records` policy mismatch or student_id mismatch.

