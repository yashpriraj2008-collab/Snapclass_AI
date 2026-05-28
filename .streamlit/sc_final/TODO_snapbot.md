# SnapBot Fix — TODO

## 1) Remove legacy/broken SnapBot usage
- [ ] Remove any calls/imports of `render_snapbot` / legacy HTML SnapBot from all screens.
- [ ] Keep SnapBot code only in `src/components/snapbot.py`.
- [ ] Stop using `update_snapbot_context` anywhere except app routing / global call (if needed).


## 2) Replace `src/components/snapbot.py` fully
- [ ] Overwrite `src/components/snapbot.py` with the provided fixed code.
- [ ] Ensure it defines only `update_snapbot_context` and `render_snapbot_floating` (and helpers), and builds the full HTML into a single `snapbot_html` variable.
- [ ] Normalize `snapbot_html` using the required `"\n".join(line.strip() ...)` line.
- [ ] Render only via `st.markdown(snapbot_html, unsafe_allow_html=True)`.

## 3) Ensure only one global SnapBot call
- [ ] Update `app.py` to import `render_snapbot_floating` and call it exactly once at the very bottom after routing.
- [ ] Ensure no sidebar/pricing-specific additional SnapBot calls exist.

## 4) Verify HTML is not shown
- [ ] Re-run Streamlit.
- [ ] Hard refresh.
- [ ] Confirm only the 🤖 icon appears; no raw `<div class="snapbot-body">` text.

