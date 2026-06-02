-- SnapClass AI — Cleanup duplicate + unused institutes (SAFE)
--
-- PURPOSE
-- 1) Preview duplicate institutes by normalized name.
-- 2) Preview unused institutes.
-- 3) Delete only institutes that have zero linked data across:
--      classes, teachers, students, subjects, school_codes, subscriptions
--    and only if deleting is safe with duplicate-groups.
--
-- RULES (as requested)
-- A) Delete duplicate institutes only if duplicate has zero linked data.
-- B) Keep institute with most linked data.
-- C) Never delete an institute with students/teachers/classes/subjects/subscriptions.
-- D) Use RETURNING to show deleted rows.
--
-- NOTES
-- - Do not delete blindly: run previews first.
-- - This SQL assumes tables/columns exist:
--     institutes(id,name,...,status,plan,...)
--     teachers(institute_id)
--     students(institute_id)
--     subjects(teacher_id,class_name) or (institute_id?)
--     school_codes(institute_id)
--     subscriptions(institute_id)
--     classes(institute_id)  (may be via teacher_assignments/classes in your schema)
-- - If your schema uses different FKs, adjust the join paths.
--
-- ---------------------------------------------------------------------------------
-- 0) Helper: normalized name (lower(trim(name)))
-- ---------------------------------------------------------------------------------
create or replace temp view normalized_institutes as
select
  i.*,
  lower(trim(coalesce(i.name, ''))) as name_norm
from public.institutes i;

-- ---------------------------------------------------------------------------------
-- A) Preview duplicates by normalized name
-- ---------------------------------------------------------------------------------
-- Duplicate defined as: same lower(trim(name)) appearing 2+ times.
-- Also compute linked-data “score” per institute.

with
inst_base as (
  select * from normalized_institutes
),
classes_count as (
  -- If classes table exists with institute_id, count directly.
  -- Otherwise fall back to 0 (you may edit this section after inspecting schema).
  select
    c.institute_id as institute_id,
    count(*)::int as cnt
  from public.classes c
  group by c.institute_id
),
teachers_count as (
  select t.institute_id as institute_id, count(*)::int as cnt
  from public.teachers t
  group by t.institute_id
),
students_count as (
  select s.institute_id as institute_id, count(*)::int as cnt
  from public.students s
  group by s.institute_id
),
subjects_count as (
  -- Subjects are not directly linked to institutes in the current v2 schema.
  -- In that schema, subjects.teacher_id -> teachers.id -> teachers.institute_id.
  select
    t.institute_id as institute_id,
    count(*)::int as cnt
  from public.subjects sub
  join public.teachers t on t.id = sub.teacher_id
  group by t.institute_id
),
school_codes_count as (
  select sc.institute_id as institute_id, count(*)::int as cnt
  from public.school_codes sc
  group by sc.institute_id
),
subscriptions_count as (
  select s.institute_id as institute_id, count(*)::int as cnt
  from public.subscriptions s
  group by s.institute_id
),
linked as (
  select
    i.id as institute_id,
    coalesce(c.cnt,0) as classes_cnt,
    coalesce(t.cnt,0) as teachers_cnt,
    coalesce(s.cnt,0) as students_cnt,
    coalesce(sub.cnt,0) as subjects_cnt,
    coalesce(sc.cnt,0) as school_codes_cnt,
    coalesce(sb.cnt,0) as subscriptions_cnt
  from inst_base i
  left join classes_count c on c.institute_id = i.id
  left join teachers_count t on t.institute_id = i.id
  left join students_count s on s.institute_id = i.id
  left join subjects_count sub on sub.institute_id = i.id
  left join school_codes_count sc on sc.institute_id = i.id
  left join subscriptions_count sb on sb.institute_id = i.id
),
score as (
  select
    i.id,
    i.name,
    i.city,
    i.state,
    i.status,
    i.plan,
    i.name_norm,
    (classes_cnt + teachers_cnt + students_cnt + subjects_cnt + school_codes_cnt + subscriptions_cnt) as linked_score,
    classes_cnt, teachers_cnt, students_cnt, subjects_cnt, school_codes_cnt, subscriptions_cnt
  from inst_base i
  join linked l on l.institute_id = i.id
)
select
  name_norm,
  count(*) as institutes_in_group,
  jsonb_agg(
    jsonb_build_object(
      'id', id,
      'name', name,
      'city', city,
      'state', state,
      'linked_score', linked_score,
      'classes_cnt', classes_cnt,
      'teachers_cnt', teachers_cnt,
      'students_cnt', students_cnt,
      'subjects_cnt', subjects_cnt,
      'school_codes_cnt', school_codes_cnt,
      'subscriptions_cnt', subscriptions_cnt,
      'status', status,
      'plan', plan
    ) order by linked_score desc, id
  ) as institutes
from score
where name_norm <> ''
group by name_norm
having count(*) > 1
order by institutes_in_group desc, name_norm;

-- ---------------------------------------------------------------------------------
-- B) Preview unused institutes (zero linked data)
-- ---------------------------------------------------------------------------------
-- “Unused” = zero across the specified linked tables.
-- We also compute per-institute linked data counts to confirm safety.

with
inst_base as (
  select * from normalized_institutes
),
classes_count as (
  select c.institute_id as institute_id, count(*)::int as cnt
  from public.classes c
  group by c.institute_id
),
teachers_count as (
  select t.institute_id as institute_id, count(*)::int as cnt
  from public.teachers t
  group by t.institute_id
),
students_count as (
  select s.institute_id as institute_id, count(*)::int as cnt
  from public.students s
  group by s.institute_id
),
subjects_count as (
  select
    t.institute_id as institute_id,
    count(*)::int as cnt
  from public.subjects sub
  join public.teachers t on t.id = sub.teacher_id
  group by t.institute_id
),
school_codes_count as (
  select sc.institute_id as institute_id, count(*)::int as cnt
  from public.school_codes sc
  group by sc.institute_id
),
subscriptions_count as (
  select s.institute_id as institute_id, count(*)::int as cnt
  from public.subscriptions s
  group by s.institute_id
),
linked as (
  select
    i.id as institute_id,
    coalesce(c.cnt,0) as classes_cnt,
    coalesce(t.cnt,0) as teachers_cnt,
    coalesce(s.cnt,0) as students_cnt,
    coalesce(sub.cnt,0) as subjects_cnt,
    coalesce(sc.cnt,0) as school_codes_cnt,
    coalesce(sb.cnt,0) as subscriptions_cnt
  from inst_base i
  left join classes_count c on c.institute_id = i.id
  left join teachers_count t on t.institute_id = i.id
  left join students_count s on s.institute_id = i.id
  left join subjects_count sub on sub.institute_id = i.id
  left join school_codes_count sc on sc.institute_id = i.id
  left join subscriptions_count sb on sb.institute_id = i.id
)
select
  i.id,
  i.name,
  i.city,
  i.state,
  i.status,
  i.plan,
  i.name_norm,
  l.classes_cnt,
  l.teachers_cnt,
  l.students_cnt,
  l.subjects_cnt,
  l.school_codes_cnt,
  l.subscriptions_cnt
from public.institutes i
join linked l on l.institute_id = i.id
where
  l.classes_cnt = 0
  and l.teachers_cnt = 0
  and l.students_cnt = 0
  and l.subjects_cnt = 0
  and l.school_codes_cnt = 0
  and l.subscriptions_cnt = 0
order by i.name_norm, i.created_at;

-- ---------------------------------------------------------------------------------
-- C/D/E/F) Cleanup (DELETE) with safety checks and RETURNING
-- ---------------------------------------------------------------------------------
-- Strategy:
-- 1) Compute linked counts per institute.
-- 2) Define “deletable” = all counts are zero (specified tables).
-- 3) If institute is in a duplicate-name group, delete only those deletable institutes.
-- 4) Keep institute with most linked data within each duplicate group.
--    (Given our deletable definition, only zero-linked ones are eligible, so the
--     “keep most linked data” constraint is naturally satisfied; but we enforce it.)
--
-- IMPORTANT: This DELETE is written to be idempotent and safe.

with
inst_base as (
  select * from normalized_institutes
),
classes_count as (
  select c.institute_id as institute_id, count(*)::int as cnt
  from public.classes c
  group by c.institute_id
),
teachers_count as (
  select t.institute_id as institute_id, count(*)::int as cnt
  from public.teachers t
  group by t.institute_id
),
students_count as (
  select s.institute_id as institute_id, count(*)::int as cnt
  from public.students s
  group by s.institute_id
),
subjects_count as (
  select
    t.institute_id as institute_id,
    count(*)::int as cnt
  from public.subjects sub
  join public.teachers t on t.id = sub.teacher_id
  group by t.institute_id
),
school_codes_count as (
  select sc.institute_id as institute_id, count(*)::int as cnt
  from public.school_codes sc
  group by sc.institute_id
),
subscriptions_count as (
  select s.institute_id as institute_id, count(*)::int as cnt
  from public.subscriptions s
  group by s.institute_id
),
linked as (
  select
    i.id as institute_id,
    coalesce(c.cnt,0) as classes_cnt,
    coalesce(t.cnt,0) as teachers_cnt,
    coalesce(s.cnt,0) as students_cnt,
    coalesce(sub.cnt,0) as subjects_cnt,
    coalesce(sc.cnt,0) as school_codes_cnt,
    coalesce(sb.cnt,0) as subscriptions_cnt
  from inst_base i
  left join classes_count c on c.institute_id = i.id
  left join teachers_count t on t.institute_id = i.id
  left join students_count s on s.institute_id = i.id
  left join subjects_count sub on sub.institute_id = i.id
  left join school_codes_count sc on sc.institute_id = i.id
  left join subscriptions_count sb on sb.institute_id = i.id
),
scored as (
  select
    i.id,
    i.name_norm,
    (classes_cnt + teachers_cnt + students_cnt + subjects_cnt + school_codes_cnt + subscriptions_cnt) as linked_score,
    classes_cnt, teachers_cnt, students_cnt, subjects_cnt, school_codes_cnt, subscriptions_cnt
  from inst_base i
  join linked l on l.institute_id = i.id
),
groups as (
  select
    name_norm,
    count(*) as group_size,
    max(linked_score) as max_linked_score
  from scored
  where name_norm <> ''
  group by name_norm
),
ranked as (
  select
    s.*,
    g.max_linked_score,
    row_number() over (
      partition by s.name_norm
      order by s.linked_score desc, s.id
    ) as rn_in_group
  from scored s
  join groups g on g.name_norm = s.name_norm
)
-- Only delete if:
-- - All specified linked counts are zero
-- - AND (if in duplicate group) the row is not the “keep” candidate
--   (keep candidate = highest linked_score; in a zero-only group this will pick one;
--    we avoid deleting keep candidate to satisfy E.)
select 1;

-- Uncomment to perform deletion after reviewing previews.
--
-- delete from public.institutes i
-- using ranked r
-- where i.id = r.id
--   and r.linked_score = 0
--   and (
--     -- If not a duplicate-name group, safe.
--     r.name_norm not in (
--       select name_norm from scored group by name_norm having count(*) > 1
--     )
--     -- If duplicate group, do not delete the “keep” one.
--     or r.rn_in_group > 1
--   )
-- returning
--   i.id,
--   i.name,
--   i.city,
--   i.state,
--   i.status,
--   i.plan;

