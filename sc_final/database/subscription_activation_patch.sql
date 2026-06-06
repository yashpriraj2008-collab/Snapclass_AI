-- SnapClass paid-subscription activation fields and status constraints.
-- Safe to run repeatedly in the Supabase SQL editor.

alter table public.institutes
  add column if not exists plan text,
  add column if not exists subscription_status text default 'pending_payment';

alter table public.subscriptions
  add column if not exists plan_name text,
  add column if not exists payment_status text default 'unpaid',
  add column if not exists current_period_start timestamptz,
  add column if not exists current_period_end timestamptz,
  add column if not exists updated_at timestamptz default now();

alter table public.subscriptions
  drop constraint if exists subscriptions_status_check;

alter table public.subscriptions
  add constraint subscriptions_status_check
  check (status in ('pending', 'pending_payment', 'active', 'expired', 'cancelled'));

alter table public.payment_orders
  add column if not exists razorpay_order_id text,
  add column if not exists razorpay_payment_id text,
  add column if not exists razorpay_payment_link_id text,
  add column if not exists paid_at timestamptz,
  add column if not exists updated_at timestamptz default now();

alter table public.payment_orders
  drop constraint if exists payment_orders_status_check;

alter table public.payment_orders
  add constraint payment_orders_status_check
  check (status in ('created', 'pending', 'paid', 'failed'));

create index if not exists payment_orders_institute_created_idx
  on public.payment_orders (institute_id, created_at desc);
