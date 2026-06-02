# Phase 5 Payment Test Checklist

## Pricing
- [ ] Pricing page loads
- [ ] Demo plan activates without payment
- [ ] Starter button creates Razorpay test order
- [ ] Pro button creates Razorpay test order
- [ ] Enterprise shows contact/sales message

## Orders
- [ ] `payment_orders` row created
- [ ] `razorpay_order_id` saved
- [ ] amount is in paise (₹499=49900, ₹999=99900)
- [ ] receipt is unique
- [ ] status is `created`

## Checkout
- [ ] Razorpay test checkout opens
- [ ] Test payment succeeds
- [ ] Payment signature is verified
- [ ] `payments` row created
- [ ] `subscriptions` row becomes active

## Plan Limits
- [ ] Demo blocks after 30 students
- [ ] Starter blocks after 200 students
- [ ] Pro blocks after 1000 students
- [ ] AI Attendance disabled when plan does not allow it
- [ ] Email alerts disabled when plan does not allow it

## Failure Cases
- [ ] Cancelled payment does not activate subscription
- [ ] Failed payment saved as failed
- [ ] Duplicate payment does not double-activate subscription
- [ ] Missing Razorpay keys shows clear message

## Webhook Later
- [ ] Webhook endpoint planned
- [ ] Raw body signature verification planned
- [ ] `x-razorpay-event-id` duplicate handling planned

## Phase 5 Pass Condition
Phase 5 Part A passes when:
- [ ] Pricing buttons route correctly
- [ ] Razorpay test order is created
- [ ] `payment_orders` row saved
- [ ] Test checkout works
- [ ] Payment signature is verified
- [ ] `payments` row is saved
- [ ] `subscriptions` row becomes active
- [ ] Admin billing shows active plan
- [ ] Plan limits actually block extra usage
- [ ] Failed/cancelled payment does not activate plan

