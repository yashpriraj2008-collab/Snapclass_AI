# Payment Production Plan

Status: not production-ready. Keep Razorpay live checkout disabled until this plan is implemented and tested.

## Current State

- `src/services/payment_service.py` can create Razorpay orders.
- Checkout signature and webhook signature helper functions exist.
- The pricing UI does not yet run a verified production checkout flow.
- Subscription upgrades must not be granted from frontend success alone.

## Required Design

1. Server-side order creation
   - Calculate plan amount server-side from a trusted plan table or constant.
   - Ignore any frontend-provided amount.
   - Store `razorpay_order_id`, plan, amount, currency, user/institute id, and status.

2. Checkout verification
   - Require `razorpay_order_id`, `razorpay_payment_id`, and `razorpay_signature`.
   - Verify signature server-side using `RAZORPAY_KEY_SECRET`.
   - Mark payment successful only after verification passes.

3. Webhook verification
   - Verify `X-Razorpay-Signature` using the raw request body.
   - Handle at minimum:
     - `payment.captured`
     - `payment.failed`
     - `order.paid`
     - refund/cancel events if refunds are enabled
   - Store every webhook event with provider event id and processing status.

4. Subscription update
   - Update subscription only after verified checkout or verified webhook.
   - Store plan start/end, status, provider ids, and audit timestamps.
   - Handle failed, cancelled, refunded, and expired states.

5. Plan limits
   - Enforce limits server-side:
     - institutes
     - students
     - teachers
     - AI/FaceID access
     - reports/exports

## Tables Needed

- `plans`
- `subscriptions`
- `payments`
- `payment_events` or `webhook_events`

## Manual Razorpay Dashboard Steps

1. Keep test mode until the verified flow passes.
2. Configure webhook URL only after a backend endpoint can read raw body.
3. Add webhook secret to deployment secrets as `RAZORPAY_WEBHOOK_SECRET`.
4. Rotate test/live keys before production.
5. Verify payment capture, failure, refund, and duplicate webhook handling.

## Release Gate

Payment production-ready: no.

Live payments may be enabled only after:

- server-side amount calculation is enforced,
- checkout signature verification is mandatory,
- webhook raw-body verification is implemented,
- subscription changes are idempotent and verified,
- failure/refund/cancel states are tested.

