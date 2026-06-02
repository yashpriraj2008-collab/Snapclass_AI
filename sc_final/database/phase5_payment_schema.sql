-- Phase 5 Payment Schema (Razorpay Test Flow)
-- Creates:
--   - plans
--   - payment_orders
--   - payments
--   - subscriptions
--   - payment_events

-- NOTE:
--   - Amounts are stored in paise.
--   - Streamlit verifies Razorpay signatures before activating subscriptions.
--   - Webhooks (Part B) can later write/update the same tables.

-- Plans table
create table if not exists public.plans (
  id uuid primary key default gen_random_uuid(),
  plan_code text unique not null,
  display_name text not null,
  billing_cycle text not null check (billing_cycle in ('monthly','yearly','forever')),
  amount_paise integer not null default 0,
  currency text not null default 'INR',
  is_active boolean not null default true,
  limits jsonb not null default '{}'::jsonb,
  feature_flags jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- Payment orders created from Streamlit checkout
create table if not exists public.payment_orders (
  id uuid primary key default gen_random_uuid(),
  order_id text unique not null, -- Razorpay order id
  institute_id uuid not null,
  user_id uuid not null,
  plan_id uuid not null references public.plans(id),
  billing_cycle text not null,
  amount_paise integer not null,
  currency text not null default 'INR',
  receipt text not null unique,
  status text not null default 'created' check (status in ('created','paid','failed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists payment_orders_institute_id_idx on public.payment_orders(institute_id);
create index if not exists payment_orders_plan_id_idx on public.payment_orders(plan_id);

-- Payments rows (after signature verification)
create table if not exists public.payments (
  id uuid primary key default gen_random_uuid(),
  payment_id text unique not null, -- Razorpay payment id
  order_id text not null references public.payment_orders(order_id),
  institute_id uuid not null,
  user_id uuid not null,
  plan_id uuid not null references public.plans(id),
  billing_cycle text not null,
  amount_paise integer not null,
  currency text not null default 'INR',
  status text not null default 'success' check (status in ('success','failed')),
  signature text not null,
  created_at timestamptz not null default now()
);

create index if not exists payments_institute_id_idx on public.payments(institute_id);
create index if not exists payments_plan_id_idx on public.payments(plan_id);

-- Subscriptions activated only after signature verification
create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid not null unique,
  plan_id uuid not null references public.plans(id),
  billing_cycle text not null,
  status text not null check (status in ('active','expired','cancelled')) default 'active',
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  razorpay_order_id text,
  razorpay_payment_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Webhook/event de-duplication table (Part B)
create table if not exists public.payment_events (
  id uuid primary key default gen_random_uuid(),
  razorpay_event_id text unique not null,
  event_type text,
  institute_id uuid,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists payment_events_event_type_idx on public.payment_events(event_type);

-- Insert/Upsert default plans
-- Demo: max 30 students, limited features
-- Starter: max 200 students
-- Pro: max 1000 students
-- Enterprise: unlimited/custom (handled via flags)

insert into public.plans (
  plan_code,
  display_name,
  billing_cycle,
  amount_paise,
  currency,
  is_active,
  limits,
  feature_flags
)
values
  (
    'demo',
    'Demo',
    'forever',
    0,
    'INR',
    true,
    '{"max_students":30,"max_teachers":30}'::jsonb,
    '{"ai_attendance":false,"reports_export":true,"email_alerts":false}'::jsonb
  ),
  (
    'starter',
    'Starter',
    'monthly',
    49900,
    'INR',
    true,
    '{"max_students":200,"max_teachers":50}'::jsonb,
    '{"ai_attendance":true,"reports_export":true,"email_alerts":true}'::jsonb
  ),
  (
    'pro',
    'Pro',
    'monthly',
    99900,
    'INR',
    true,
    '{"max_students":1000,"max_teachers":200}'::jsonb,
    '{"ai_attendance":true,"reports_export":true,"email_alerts":true}'::jsonb
  ),
  (
    'enterprise',
    'Enterprise',
    'monthly',
    249900,
    'INR',
    true,
    '{"max_students":null,"max_teachers":null}'::jsonb,
    '{"ai_attendance":true,"reports_export":true,"email_alerts":true}'::jsonb
  )
on conflict (plan_code) do update set
  display_name = excluded.display_name,
  billing_cycle = excluded.billing_cycle,
  amount_paise = excluded.amount_paise,
  currency = excluded.currency,
  is_active = excluded.is_active,
  limits = excluded.limits,
  feature_flags = excluded.feature_flags;

