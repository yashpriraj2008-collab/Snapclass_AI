import streamlit as st

RESPONSES = {
    "faceid":       "🪪 FaceID Attendance: Go to Student Portal → FaceID Attendance. The camera activates and marks your attendance automatically using face recognition.",
    "attendance":   "📋 Your attendance is visible on the Student Dashboard. Below 75% triggers a low-attendance warning. Check each subject under 'My Subjects'.",
    "manual":       "✏️ Manual Attendance (Teacher): Go to Teacher Portal → Manual Attendance. Select class, subject, date, then mark each student Present/Absent.",
    "ai":           "🤖 AI Attendance (Teacher): Go to Teacher Portal → AI Attendance. Upload a class photo, click 'Run AI Analysis', review detected students, and confirm.",
    "admin":        "🏫 Admin Portal: Login with the admin password. You can manage schools, teachers, students, subjects, and view analytics.",
    "login":        "🔑 Login: Use the portal cards on the landing page. Demo: student@snapclass.ai / student123 or teacher@snapclass.ai / teacher123.",
    "report":       "📄 Reports: Available in Teacher and Admin portals under the Analytics and Reports sections.",
    "low":          "⚠️ Low Attendance: Below 75% is flagged as low. You'll see a warning card on your dashboard and under My Subjects.",
    "navigate":     "🧭 Navigation: Use the left sidebar to navigate between pages. Click any menu item to switch sections.",
    "subject":      "📚 Subjects: All your enrolled subjects with attendance stats are visible under Student Portal → My Subjects.",
    "logout":       "🚪 Logout: Click the Logout button at the bottom of the left sidebar.",
}


def _get_response(query: str) -> str:
    q = query.lower()
    for key, response in RESPONSES.items():
        if key in q:
            return response
    if any(w in q for w in ["hello", "hi", "hey"]):
        return "👋 Hi! I'm SnapBot. Ask me about attendance, FaceID, login, AI attendance, or navigation!"
    if any(w in q for w in ["help", "what", "how"]):
        return "💡 I can help with: attendance, faceid, manual attendance, AI attendance, admin portal, login, reports, low attendance, navigation, subjects, logout."
    return "🤔 I'm not sure about that. Try asking: 'how does FaceID work', 'what is low attendance', 'how to mark manual attendance', or 'how to use admin portal'."


def floating_chatbot() -> None:
    """
    Render the chatbot using the floating CSS classes defined in:
      - snapclass/static/chatbot.css

    Previously this widget was rendered inside `st.sidebar`, which meant the floating
    CSS had no effect and the UI looked broken. Now it's rendered in the main page
    using fixed-position containers.
    """
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = True
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [("bot", "👋 Hi! I'm SnapBot. How can I help you today?")]

    # Fixed-position window wrapper
    st.markdown(
        """
        <div class="sc-chat-window" aria-label="SnapBot chat window">
          <div class="sc-chat-header">
            <span>💬 SnapBot</span>
            <span style="font-size:.85rem;opacity:.9;">Online</span>
          </div>
          <div class="sc-chat-body">
        """,
        unsafe_allow_html=True,
    )

    # Messages
    for role, msg in st.session_state.chat_history[-12:]:
        cls = "sc-chat-msg sc-chat-bot" if role == "bot" else "sc-chat-msg sc-chat-user"
        # Use a fixed color to avoid any unexpected Streamlit/CSS overrides.
        # (Also ensures emojis/special characters remain visible.)
        color = "#1F2937" if role == "bot" else "#FFFFFF"
        st.markdown(
            f"<div class='{cls}' style='color:{color};'>{msg}</div>",
            unsafe_allow_html=True,
        )

    # Input area
    st.markdown(
        """
          </div>
          <div class="sc-chat-footer">
        """,
        unsafe_allow_html=True,
    )

    q = st.text_input(
        "Ask SnapBot about attendance…",
        key="chatbot_input",
        label_visibility="collapsed",
        placeholder="e.g. how does FaceID work?",
    )

    if st.button("Send", key="chatbot_send", use_container_width=False):
        if q.strip():
            st.session_state.chat_history.append(("user", q))
            answer = _get_response(q)
            st.session_state.chat_history.append(("bot", answer))
            st.rerun()

    st.markdown(
        """
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
