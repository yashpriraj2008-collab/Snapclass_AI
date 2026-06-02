# SnapBot Fix — Step Tracker

- [x] Search repo for old SnapBot HTML markers (snapbot-body/footer/answer-box/SnapClass Bot)
- [x] Remove/disable legacy floating chatbot raw HTML/CSS (src/components/floating_chatbot.py)
- [x] Ensure only src/components/snapbot.py contains snapbot-body/footer/answer-box/SnapClass Bot strings
- [x] Remove all screen-level render_snapbot() calls so SnapBot is global-only
- [x] Ensure app.py calls render_snapbot_floating only once at the bottom
- [x] Rewrite src/screens/attendance.py without SnapBot calls
- [x] Rewrite src/screens/settings.py without SnapBot calls
- [x] Rewrite src/screens/my_institute.py without SnapBot calls
- [x] Remove SnapBot import/usage from src/screens/institute_dashboard.py and src/screens/institute_classes.py
- [x] Clean up src/screens/pricing.py (removed broken SnapBot context code)

Next:
- [ ] Replace src/components/snapbot.py with the exact provided implementation that builds snapbot_html as a single variable and normalizes it before st.markdown.
- [ ] Run: streamlit run app.py --server.port 8507 and hard refresh (Ctrl+F5)
- [ ] Verify: only bottom-right 🤖 icon, right-side panel, no raw HTML text.

