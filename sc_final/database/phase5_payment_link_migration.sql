-- Payment Link MVP migration
-- Adds columns needed for Payment Link-based checkout flow.

-- payment_orders extensions
alter table public.payment_orders
  add column if not exists amount_paise integer,
  add column if not exists currency text default 'INR',
  add column if not exists plan_name text,
  add column if not exists razorpay_payment_link_id text,
  add column if not exists razorpay_payment_link_url text,
  add column if not exists razorpay_order_id text,
  add column if not exists razorpay_payment_id text,
  add column if not exists razorpay_signature text,
  add column if not exists status text default 'pending',
  add column if not exists updated_at timestamptz default now();

-- subscriptions extensions
alter table public.subscriptions
  add column if not exists payment_status text default 'pending',
  add column if not exists plan_name text,
  add column if not exists current_period_start timestamptz,
  add column if not exists current_period_end timestamptz,
  add column if not exists updated_at timestamptz default now();

