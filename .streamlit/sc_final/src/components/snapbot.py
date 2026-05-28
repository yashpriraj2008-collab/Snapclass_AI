import html
import streamlit as st


def update_snapbot_context(**kwargs):
    if "snapbot_context" not in st.session_state:
        st.session_state.snapbot_context = {}

    for key, value in kwargs.items():
        if value is not None:
            st.session_state.snapbot_context[key] = value


def _safe(value, default="Not available"):
    return default if value is None or value == "" else str(value)


def _screen_key():
    context = st.session_state.get("snapbot_context", {})
    screen = str(context.get("screen", "home")).lower().strip()
    return screen.replace(" ", "_").replace("-", "_")


def _build_qas():
    context = st.session_state.get("snapbot_context", {})
    screen = _screen_key()

    role = _safe(context.get("role"), "user")
    class_name = _safe(context.get("class_name"))
    subject_name = _safe(context.get("subject_name"))
    total_students = context.get("total_students")
    present_count = context.get("present_count")
    absent_count = context.get("absent_count")
    attendance_percentage = context.get("attendance_percentage")
    supabase_status = _safe(context.get("supabase_status"), "Not checked")

    if screen in ["home", "pricing", "features", "about", "contact"]:
        return [
            (
                "Which portal should I use?",
                "Use Student Portal if you are a student, Teacher Portal if you mark attendance, Institute Admin if you manage an institute, and SnapClass HQ if you manage access codes and plans.",
            ),
            (
                "What is Student Portal?",
                "Student Portal helps students view attendance, subjects, attendance history, reports, and FaceID attendance.",
            ),
            (
                "What is Teacher Portal?",
                "Teacher Portal helps teachers manage classes, students, manual attendance, AI attendance, analytics, and reports.",
            ),
            (
                "What is Institute Admin?",
                "Institute Admin is for managing institute profile, teachers, students, classes, subjects, attendance threshold, and settings.",
            ),
        ]

    if screen == "manual_attendance":
        percent_answer = "Attendance percentage is not available yet."
        if attendance_percentage is not None:
            percent_answer = f"Attendance percentage is {attendance_percentage}%."
        elif present_count is not None and total_students:
            percent_answer = f"Attendance percentage is {round((present_count / total_students) * 100, 2)}%."

        return [
            ("Show absent students", f"Absent students: {absent_count}." if absent_count is not None else "Absent count is not available yet."),
            ("What's the attendance percentage?", percent_answer),
            ("How many total students?", f"Total students: {total_students}." if total_students is not None else "Total student count is not available yet."),
            ("Which class and subject are selected?", f"Selected class: {class_name}. Selected subject: {subject_name}."),
        ]

    if screen == "ai_attendance":
        return [
            ("How does AI attendance work?", "AI Attendance compares uploaded/live photos with enrolled student face data, then marks matched students present."),
            ("Why is FaceID not working?", "FaceID needs DeepFace, TensorFlow, tf-keras, and OpenCV installed in the same Python 3.11 virtual environment."),
            ("Which class and subject are selected?", f"Selected class: {class_name}. Selected subject: {subject_name}."),
            ("Is AI attendance saved?", f"Supabase status: {supabase_status}."),
        ]

    if screen == "teacher_students":
        return [
            ("Why are students not showing?", "Check Supabase SELECT policy, table columns, institute_id filter, class_name filter, and whether your app is reading the correct students table."),
            ("How do I add a student?", "Open Students page, expand Add Student, enter name, roll number, class, section, and save."),
            ("How do I search student?", "Use the search box with student name or roll number."),
            ("Is student data saved?", f"Supabase status: {supabase_status}."),
        ]

    return [
        ("What can I do in this app?", "SnapClass AI helps students track attendance, teachers mark attendance, admins manage institutes, and HQ manage access codes."),
        ("Is my data saved in Supabase?", f"Supabase status: {supabase_status}."),
        ("What page am I on?", f"You are on {screen}. Role: {role}."),
        ("How do I fix app errors?", "Check terminal error, Supabase table columns, RLS policies, active Python venv, and whether the selected page passes correct context."),
    ]


def render_snapbot_floating(context=None):
    if "snapbot_context" not in st.session_state:
        st.session_state.snapbot_context = {}

    if context:
        update_snapbot_context(**context)

    qas = _build_qas()

    question_html = ""
    answer_css = ""
    answer_html = ""

    for i, (question, answer) in enumerate(qas):
        checked = "checked" if i == 0 else ""
        question_html += (
            f'<input type="radio" name="snapbot-question" id="snapbot-q{i}" class="snapbot-radio" {checked}>'
            f'<label for="snapbot-q{i}" class="snapbot-question">{html.escape(question)}</label>'
        )
        answer_css += f"#snapbot-q{i}:checked ~ .snapbot-answer-box .snapbot-answer-{i}{{display:block;}}"
        answer_html += (
            f'<div class="snapbot-answer snapbot-answer-{i}"><div class="snapbot-bot-line">🤖 {html.escape(answer)}</div></div>'
        )

    snapbot_html = f"""
<style>
.snapbot-toggle{{display:none;}}
.snapbot-float-btn{{position:fixed;right:28px;bottom:28px;width:64px;height:64px;border-radius:999px;background:linear-gradient(135deg,#6366f1,#ec4899);color:white;display:flex;align-items:center;justify-content:center;font-size:30px;cursor:pointer;z-index:999999;box-shadow:0 18px 45px rgba(99,102,241,.35);}}
.snapbot-panel{{position:fixed;right:28px;bottom:108px;width:430px;max-width:calc(100vw - 32px);max-height:calc(100vh - 140px);overflow-y:auto;background:white;border-radius:24px;border:1px solid #e5e7eb;box-shadow:0 24px 70px rgba(15,23,42,.22);z-index:999998;display:none;}}
.snapbot-toggle:checked~.snapbot-panel{{display:block;}}
.snapbot-header{{background:linear-gradient(135deg,#6366f1,#ec4899);padding:22px;color:white;display:flex;align-items:center;gap:14px;}}
.snapbot-avatar{{width:48px;height:48px;border-radius:16px;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:24px;}}
.snapbot-title{{font-size:22px;font-weight:800;color:white;}}
.snapbot-subtitle{{font-size:14px;color:rgba(255,255,255,.9);}}
.snapbot-close{{margin-left:auto;font-size:24px;cursor:pointer;color:white;}}
.snapbot-body{{padding:22px;}}
.snapbot-try{{font-size:17px;font-weight:800;color:#111827;margin-bottom:14px;}}
.snapbot-radio{{display:none;}}
.snapbot-question{{display:block;padding:14px 16px;margin-bottom:10px;border:1px solid #e5e7eb;border-radius:14px;background:white;color:#111827;font-weight:650;cursor:pointer;box-shadow:0 8px 22px rgba(15,23,42,.06);}}
.snapbot-question:hover{{border-color:#6366f1;background:#f8fafc;}}
.snapbot-answer-box{{margin-top:18px;border-top:1px solid #e5e7eb;padding-top:18px;}}
.snapbot-answer{{display:none;}}
.snapbot-bot-line{{background:#f8fafc;color:#111827;padding:14px 16px;border-radius:16px;line-height:1.55;font-weight:500;}}
.snapbot-footer{{padding:0 22px 22px 22px;}}
.snapbot-input-note{{padding:13px 16px;border-radius:14px;border:1px solid #e5e7eb;color:#64748b;background:white;font-weight:500;}}
{answer_css}
@media(max-width:640px){{.snapbot-float-btn{{right:16px;bottom:16px;}}.snapbot-panel{{right:16px;bottom:92px;width:calc(100vw - 32px);max-height:calc(100vh - 120px);}}}}
</style>
<input type="checkbox" id="snapbot-toggle" class="snapbot-toggle">
<label for="snapbot-toggle" class="snapbot-float-btn">🤖</label>
<div class="snapbot-panel">
<div class="snapbot-header"><div class="snapbot-avatar">🤖</div><div><div class="snapbot-title">SnapClass Bot</div><div class="snapbot-subtitle">Attendance Assistant</div></div><label for="snapbot-toggle" class="snapbot-close">×</label></div>
<div class="snapbot-body"><div class="snapbot-try">Try asking:</div>{question_html}<div class="snapbot-answer-box">{answer_html}</div></div>
<div class="snapbot-footer"><div class="snapbot-input-note">Choose a question above. Full typing AI can be added later.</div></div>
</div>
"""

    snapbot_html = "\n".join(line.strip() for line in snapbot_html.splitlines() if line.strip())
    st.markdown(snapbot_html, unsafe_allow_html=True)

