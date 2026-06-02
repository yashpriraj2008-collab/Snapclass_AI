# TODO — plan-specific signup flow (Surgical mode)

- [x] Update `pricing.py` to always set `st.session_state["selected_plan_code"]` and `st.session_state["selected_plan_name"]` when a plan CTA is clicked.
- [x] Ensure Enterprise routes to Contact Sales without opening signup; do not set signup page.
- [x] Update `demo_signup.py` to render title/subtitle/button based on `selected_plan_code`.
- [x] Ensure submit button label matches plan requirements (Demo/Starter/Pro).
- [ ] After signup, set session_state fields:
  - [ ] `logged_in=True`
  - [ ] `portal="admin"`
  - [ ] `role="admin"`
  - [x] `selected_plan_code`
  - [x] `subscription_status`
  - [ ] institute/user identifiers (already mostly present)
- [ ] Redirect to Admin Dashboard after signup (via existing router conventions).

- [ ] Run: `python -m compileall app.py src` and `pip check`.
- [ ] Manual test matrix:
  - [ ] Pricing → Demo → Demo signup → demo subscription
  - [ ] Pricing → Starter → Starter Trial signup → starter subscription
  - [ ] Pricing → Pro → Pro Trial signup → pro subscription
  - [ ] Enterprise → Contact Sales (no signup form)

