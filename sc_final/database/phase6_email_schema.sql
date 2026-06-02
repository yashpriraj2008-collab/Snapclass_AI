-- Phase 6 — Email System (Resend + Supabase logs)

-- Extensions (for gen_random_uuid)
-- Assumes pgcrypto is available; if not, enable:
-- create extension if not exists pgcrypto;

create table if not exists public.email_logs (
  id uuid primary key default gen_random_uuid(),
  institute_id uuid,
  sender_user_id uuid,
  recipient_email text not null,
  recipient_type text,
  subject text not null,
  template_key text,
  status text default 'queued',
  resend_email_id text,
  error_message text,
  metadata jsonb,
  sent_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists public.email_templates (
  id uuid primary key default gen_random_uuid(),
  template_key text unique not null,
  name text not null,
  subject text not null,
  body_html text not null,
  status text default 'active',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.notification_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  institute_id uuid,
  email_enabled boolean default true,
  low_attendance_alerts boolean default true,
  weekly_reports boolean default true,
  payment_emails boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

