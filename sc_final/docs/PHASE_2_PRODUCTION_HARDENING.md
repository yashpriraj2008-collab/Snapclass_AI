# Phase 2 Production Hardening — SnapClass AI

## What this phase changes
This phase hardens the working Phase 1 demo for production beta by improving:
- Database identity consistency (auth.users ↔ public.user_profiles/teachers/students)
- Constraints and indexes for stability and performance
- Supabase RLS policies with least-privilege access
- Removal of demo-style permissive policies
- Repo cleanliness (no UI redesign; SQL only in dedicated files)

## What not to change
Do **not** change any UI/theme/assets or add new features.
This phase must NOT introduce:
- Live Razorpay
- Resend production email
- WhatsApp automation
- Parent portal
- Advanced AI features
- New landing page redesign
- Mobile app
- Any payment webhooks/signature validation changes

Also do not touch unrelated code paths.

## Run order (staging first)
> Run on staging first. Do not apply these SQL files directly to main.

1. `database/production_preflight.sql`
   - SELECT-only checks.
   - Fix any issues it reports before continuing.

2. `database/remove_demo_policies.sql`
   - Removes ONLY demo/phase1 permissive policies.
   - Does not remove production policies unless explicitly matching demo naming patterns.

3. `database/production_constraints_indexes.sql`
   - Adds safe unique constraints/indexes and attendance lookup indexes.
   - Uses column-existence guards where needed.

4. `database/production_rls_policies.sql`
   - Enables RLS and applies minimum least-privilege policies.
   - Avoids recursive policies and avoids user_profiles lookups from user_profiles policies.

## Rollback plan
If staging breaks after applying Phase 2 RLS:
1. Immediately revert RLS by re-enabling demo policies you removed (or disable RLS on affected tables temporarily for diagnosis).
2. Drop only the Phase 2 policies created by `production_rls_policies.sql` (policy names are prefixed in this file).
3. Re-run `production_preflight.sql`.

Rollback steps must be done on staging first; only then replicate on main.

