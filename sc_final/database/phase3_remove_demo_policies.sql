-- Phase 3 remove demo/open policies
-- Drop only demo/open policies with obvious naming.
-- IMPORTANT: Review pg_policies first.

begin;

-- Examples patterns provided in task.
-- This script drops only policies whose name matches these patterns.

DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT schemaname, tablename, policyname
    FROM pg_policies
    WHERE policyname ILIKE 'phase1_%'
       OR policyname ILIKE '%demo%'
       OR policyname ILIKE '%open%'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I', r.policyname, r.schemaname, r.tablename);
  END LOOP;
END $$;

commit;

