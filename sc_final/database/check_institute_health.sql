-- SnapClass AI — Institute health report
-- Reports duplicates + missing admin + “health” indicators

-- Admin mapping logic (as requested):
-- user_profiles.role in ('admin','institute_admin')
-- AND user_profiles.institute_id = institutes.id

with
inst as (
  select
    i.*,
    lower(trim(coalesce(i.name,''))) as name_norm
  from public.institutes i
),
admin_profiles as (
  select
    up.institute_id,
    up.id as user_profile_id
  from public.user_profiles up
  where lower(trim(coalesce(up.role,''))) in ('admin','institute_admin')
    and up.institute_id is not null
),
admin_per_institute as (
  select
    institute_id,
    count(*)::int as admin_profiles_cnt
  from admin_profiles
  group by institute_id
),
classes_exist as (
  select c.institute_id, count(*)::int as cnt
  from public.classes c
  group by c.institute_id
),
teachers_exist as (
  select t.institute_id, count(*)::int as cnt
  from public.teachers t
  group by t.institute_id
),
students_exist as (
  select s.institute_id, count(*)::int as cnt
  from public.students s
  group by s.institute_id
),
subjects_exist as (
  -- subjects are linked via teachers in the current schema
  select t.institute_id, count(*)::int as cnt
  from public.subjects sub
  join public.teachers t on t.id = sub.teacher_id
  group by t.institute_id
),
school_codes_exist as (
  select sc.institute_id, count(*)::int as cnt
  from public.school_codes sc
  group by sc.institute_id
),
subscriptions_exist as (
  select s.institute_id, count(*)::int as cnt
  from public.subscriptions s
  group by s.institute_id
),
per_institute as (
  select
    i.id,
    i.status,
    i.plan,
    i.name_norm,
    coalesce(api.admin_profiles_cnt,0) as admin_cnt,
    coalesce(ce.cnt,0) as classes_cnt,
    coalesce(te.cnt,0) as teachers_cnt,
    coalesce(se.cnt,0) as students_cnt,
    coalesce(sube.cnt,0) as subjects_cnt,
    coalesce(sce.cnt,0) as school_codes_cnt,
    coalesce(subsc.cnt,0) as subscriptions_cnt
  from inst i
  left join admin_per_institute api on api.institute_id = i.id
  left join classes_exist ce on ce.institute_id = i.id
  left join teachers_exist te on te.institute_id = i.id
  left join students_exist se on se.institute_id = i.id
  left join subjects_exist sube on sube.institute_id = i.id
  left join school_codes_exist sce on sce.institute_id = i.id
  left join subscriptions_exist subsc on subsc.institute_id = i.id
)
select
  (select count(*)::int from inst) as total_institutes,

  -- “active” definition: status = 'active' OR status is null/empty treated as active.
  (select count(*)::int from per_institute where lower(trim(coalesce(status,''))) in ('','active')) as active_institutes,

  -- Trial institutes: based on plan OR subscription status if you store it.
  -- Current schema may not have subscription_status on institutes; we still follow your app logic safely.
  (select count(*)::int from per_institute
    where lower(trim(coalesce(plan,''))) in ('demo','free demo','trial')
  ) as trial_institutes,

  -- Paid institutes: plan in starter/pro/enterprise and not suspended/disabled/test_deleted.
  (select count(*)::int from per_institute
    where lower(trim(coalesce(plan,''))) in ('starter','pro','enterprise')
      and lower(trim(coalesce(status,''))) not in ('suspended','disabled','test_deleted')
  ) as paid_institutes,

  -- duplicate names (by normalized name, count of institutes in duplicate groups)
  (select coalesce(sum(dup_cnt)::int,0)
   from (
     select name_norm, count(*) as dup_cnt
     from inst
     where name_norm <> ''
     group by name_norm
     having count(*) > 1
   ) d
  ) as duplicate_names_institutes,

  -- Missing admin
  (select count(*)::int from per_institute where admin_cnt = 0) as institutes_missing_admin,

  -- No classes/teachers/students/subscriptions
  (select count(*)::int from per_institute where classes_cnt = 0) as institutes_with_no_classes,
  (select count(*)::int from per_institute where teachers_cnt = 0) as institutes_with_no_teachers,
  (select count(*)::int from per_institute where students_cnt = 0) as institutes_with_no_students,
  (select count(*)::int from per_institute where subscriptions_cnt = 0) as institutes_with_no_subscription
;

