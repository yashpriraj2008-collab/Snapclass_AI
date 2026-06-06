-- SnapClass AI payment-pending subscription patch.
-- Run this in Supabase SQL Editor before testing paid plan checkout.

alter table public.institutes
add column if not exists subscription_status text default 'pending_payment';

alter table public.institutes
add column if not exists plan text default 'Demo';

alter table public.subscriptions
add column if not exists status text default 'pending_payment';

alter table public.subscriptions
add column if not exists payment_status text default 'unpaid';

alter table public.subscriptions
add column if not exists plan_name text;

alter table public.subscriptions
add column if not exists billing_cycle text default 'monthly';

alter table public.subscriptions
add column if not exists start_date date;

alter table public.subscriptions
add column if not exists end_date date;

alter table public.payment_orders
add column if not exists institute_id uuid;

alter table public.payment_orders
add column if not exists plan_name text;

alter table public.payment_orders
add column if not exists amount_paise integer;

alter table public.payment_orders
add column if not exists currency text default 'INR';

alter table public.payment_orders
add column if not exists status text default 'created';

alter table public.payment_orders
add column if not exists razorpay_order_id text;

alter table public.payment_orders
add column if not exists razorpay_payment_id text;

alter table public.payment_orders
add column if not exists created_at timestamp with time zone default now();

alter table public.payment_orders
add column if not exists paid_at timestamp with time zone;
