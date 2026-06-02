# Mobile QA Checklist

Run each viewport against `streamlit run app.py --server.port 8507`.

## Viewports

- [ ] 360 x 800 Android small phone
- [ ] 390 x 844 iPhone
- [ ] 412 x 915 Android large phone
- [ ] 768 x 1024 tablet
- [ ] 1366 x 768 desktop

## Public Pages

- [ ] Landing page has no horizontal scroll.
- [ ] Portal cards stack cleanly on mobile.
- [ ] Public navigation buttons remain tappable.
- [ ] Pricing cards stack one per row on mobile.
- [ ] Pricing text reads `Free forever`, not `Freeforever`.
- [ ] Pricing buttons are full width on mobile.
- [ ] FAQ expanders fit the viewport.

## Auth And Onboarding

- [ ] Founder HQ Login form fits 360 px width.
- [ ] Admin Login form shows email/password without cut-off fields.
- [ ] Start Free Demo form fields stack vertically.
- [ ] Join Institute with Code form fields stack vertically.
- [ ] Password inputs and helper text remain readable.
- [ ] Back buttons and secondary actions are full width on mobile.

## Dashboards

- [ ] Founder dashboard metrics stack vertically on mobile.
- [ ] Admin dashboard metrics stack vertically on mobile.
- [ ] Teacher dashboard metrics stack vertically on mobile.
- [ ] Student dashboard metrics stack vertically on mobile.
- [ ] Charts fit inside the viewport.
- [ ] Sidebar opens without covering content permanently.
- [ ] Page headings wrap without overlapping.

## Attendance And FaceID

- [ ] Manual Attendance form controls stack on mobile.
- [ ] Manual Attendance save button remains visible and full width.
- [ ] AI Attendance upload/camera controls fit the viewport.
- [ ] Student FaceID enrollment layout stacks on mobile.
- [ ] FaceID status cards do not overflow.

## Tables

- [ ] Students table scrolls horizontally instead of breaking layout.
- [ ] Teachers table scrolls horizontally instead of breaking layout.
- [ ] Classes/Subjects tables scroll horizontally instead of breaking layout.
- [ ] Attendance History table scrolls horizontally instead of breaking layout.
- [ ] Reports tables scroll horizontally instead of breaking layout.

## SnapBot

- [ ] Floating SnapBot button does not cover primary form buttons.
- [ ] SnapBot panel fits within phone viewport.
- [ ] SnapBot panel can be closed on mobile.
