# Phase 5 — Razorpay Test Payments & Subscription Enforcement (Part A)

## Goal
Implement a **Streamlit-only** Phase 5 flow for Razorpay **test mode**:
1. Pricing page buttons
2. Create Razorpay test order
3. Open Razorpay checkout
4. Verify payment signature
5. Save payment + activate subscription (only after verification)
6. Enforce plan limits in key app flows

## Non-goals (for Part A)
- Razorpay webhooks backend (Part B is planned, not required for demo reliability)
- Live Razorpay payments

## Plans
Default plans (inserted by `database/phase5_payment_schema.sql`):
- **demo** (free, forever)
- **starter** ₹499/month → 49900 paise
- **pro** ₹999/month → 99900 paise
- **enterprise** ₹2499/month → 249900 paise

## Required Streamlit Safety Rules
- Never enable live Razorpay.
- Do not use Supabase service-role key in Streamlit.
- Do not activate subscription from button click.
- Activation must happen only after signature verification.
- Payment failures/cancellations must not activate subscription.

## Streamlit Pages
- `src/screens/pricing.py` — plan selection UI + checkout launch (Demo free, Starter/Pro test order)
- `src/screens/payment_success.py` — verify signature → save payment → activate subscription
- `src/screens/payment_failed.py` — mark order failed
- `src/screens/admin_billing.py` — admin view of active plan + usage + upgrade actions

## Services
- `src/services/payment_service.py`
  - `get_plan(plan_code)`
  - `create_razorpay_order(plan_code, institute_id, user_id)`
  - `verify_payment_signature(order_id, payment_id, signature)`
  - `save_payment(...)`, `mark_order_paid(...)`, `mark_order_failed(...)`

- `src/services/subscription_service.py`
  - `activate_subscription(...)`
  - `get_active_subscription(institute_id)`
  - `check_plan_limit(...)`
  - `can_add_student(...)`, `can_add_teacher(...)`
  - `is_feature_enabled(...)`

## Phase B (planned)
A FastAPI webhook service that:
- reads raw request body
- verifies `X-Razorpay-Signature`
- de-duplicates using `x-razorpay-event-id`
- persists event to `payment_events`
- updates subscription/payment state

## Pass Conditions (Phase 5 Part A)
- Pricing buttons route correctly
- Razorpay test order is created for Starter/Pro
- `payment_orders` row is created with Razorpay order id + receipt
- After success: signature verified → `payments` row created → `subscriptions` row active
- Failed/cancelled does not activate subscriptions
- Admin dashboard/admin billing shows active plan
- Plan limits block extra students/teachers and feature access

