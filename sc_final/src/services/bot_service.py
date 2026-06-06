from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List


_ROLE_ALIASES = {
    "institute_admin": "admin",
    "institute": "admin",
    "school_admin": "admin",
    "hq": "founder",
    "snapclass_hq": "founder",
    "": "public",
}

_PAGE_TITLES = {
    "student_dashboard": "Student Dashboard",
    "student_subjects": "Student My Subjects",
    "student_history": "Attendance History",
    "student_reports": "Student Reports",
    "student_faceid": "Student FaceID",
    "teacher_dashboard": "Teacher Dashboard",
    "teacher_attendance": "Manual Attendance",
    "teacher_manual_attendance": "Manual Attendance",
    "teacher_reports": "Teacher Reports",
    "teacher_classes": "Teacher My Classes",
    "admin_dashboard": "Admin Dashboard",
    "admin_students": "Admin Students",
    "admin_teachers": "Admin Teachers",
    "admin_classes": "Classes and Subjects",
    "admin_subjects": "Classes and Subjects",
    "founder_dashboard": "Founder Dashboard",
    "founder_institutes": "Founder Institutes",
    "founder_codes": "Founder Codes",
    "founder_all_codes": "Founder Codes",
    "founder_allcodes": "Founder Codes",
    "founder_plans": "Founder Plans",
    "landing": "Home",
    "home": "Home",
    "pricing": "Pricing",
    "contact": "Contact",
}

GLOBAL_QUESTIONS = [
    "What can I do in this app?",
    "How does SnapClass work?",
    "Is my data saved?",
    "Why is my data not showing?",
    "How do I logout?",
    "Who should I contact for help?",
    "How do I fix wrong class or subject?",
]

QUESTIONS_BY_PAGE = {
    "student_dashboard": [
        "What can I do here?",
        "Why is my attendance 0%?",
        "How do I join a subject?",
        "Why are reports blank?",
        "Where is my attendance history?",
    ],
    "student_subjects": [
        "How do I join a subject?",
        "Where do I get join code?",
        "Why is my subject not showing?",
        "Can I join multiple subjects?",
    ],
    "student_history": [
        "Why is history blank?",
        "When will attendance appear?",
        "Where can I see present or absent records?",
        "Can I download my attendance?",
    ],
    "student_reports": [
        "Why is report blank?",
        "How is attendance percentage calculated?",
        "Can I download my report?",
        "Why is my percentage low?",
    ],
    "student_faceid": [
        "How does FaceID work?",
        "How do I enroll FaceID?",
        "Why is FaceID not working?",
        "Is manual attendance still available?",
    ],
    "teacher_dashboard": [
        "What should I do first?",
        "Why are my classes not showing?",
        "Why are students not showing?",
        "How do I mark attendance?",
    ],
    "teacher_classes": [
        "Why is student count 0?",
        "How do I share subject code?",
        "How do students join my subject?",
        "How do I take attendance?",
    ],
    "teacher_attendance": [
        "Why are students not showing?",
        "How do I save attendance?",
        "Can I mark all present?",
        "Can I edit attendance later?",
    ],
    "teacher_manual_attendance": [
        "Why are students not showing?",
        "How do I save attendance?",
        "Can I mark all present?",
        "Can I edit attendance later?",
    ],
    "teacher_reports": [
        "Why is report blank?",
        "Where are attendance records?",
        "How do I export attendance?",
        "Why is class filter empty?",
    ],
    "admin_dashboard": [
        "What should I set up first?",
        "Why is teacher assigned pending?",
        "Why are students not visible?",
        "How do I complete setup?",
    ],
    "admin_students": [
        "Where is student code?",
        "How do students register?",
        "Why is student not visible?",
        "How do I fix wrong class?",
    ],
    "admin_teachers": [
        "Where is teacher invite code?",
        "How does teacher create account?",
        "Why is teacher not assigned?",
        "How do I assign teacher?",
    ],
    "admin_classes": [
        "How do I create class?",
        "How do I add subject?",
        "Why is subject not showing?",
    ],
    "admin_subjects": [
        "How do I create class?",
        "How do I add subject?",
        "Why is subject not showing?",
    ],
    "founder_dashboard": [
        "How do I create institute?",
        "How do access codes work?",
        "How do plans work?",
        "Why is institute missing admin?",
    ],
}

QUESTIONS_BY_ROLE = {
    "public": ["What can I do in this app?", "How does SnapClass work?", "Who can use this app?"],
    "student": QUESTIONS_BY_PAGE["student_dashboard"],
    "teacher": QUESTIONS_BY_PAGE["teacher_dashboard"],
    "admin": QUESTIONS_BY_PAGE["admin_dashboard"],
    "founder": QUESTIONS_BY_PAGE["founder_dashboard"],
}


def _normalize(text: Any) -> str:
    return str(text or "").strip().lower().replace("-", "_").replace(" ", "_")


def _contains(text: str, phrase: str) -> bool:
    return _normalize(phrase) in text


def normalize_role(role: Any) -> str:
    return _ROLE_ALIASES.get(_normalize(role), _normalize(role) or "public")


def _page_title(page: str) -> str:
    key = _normalize(page)
    return _PAGE_TITLES.get(key, key.replace("_", " ").title() if key else "Current Page")


def _answer(
    title: str,
    guide: str,
    can_do: List[str],
    missing: str,
    next_action: str,
    developer: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "title": title,
        "guide": guide,
        "can_do": can_do,
        "missing": missing,
        "next_action": next_action,
        "developer": developer or [],
    }


@lru_cache(maxsize=128)
def get_suggested_questions(current_role: str = "public", current_page: str = "landing") -> List[str]:
    role_key = normalize_role(current_role)
    page_key = _normalize(current_page)
    questions = [
        *QUESTIONS_BY_PAGE.get(page_key, []),
        *QUESTIONS_BY_ROLE.get(role_key, QUESTIONS_BY_ROLE["public"]),
        *GLOBAL_QUESTIONS,
    ]
    seen: set[str] = set()
    output: List[str] = []
    for question in questions:
        key = _normalize(question)
        if key and key not in seen:
            seen.add(key)
            output.append(question)
    return output[:8]


def _page_context_answer(current_page: str, current_role: str) -> Dict[str, Any]:
    role = normalize_role(current_role).title()
    page = _page_title(current_page)
    return _answer(
        "What This Page Does",
        f"You are on {page}. This page gives {role.lower()} users the tools they need for this part of SnapClass.",
        [
            "Use the visible buttons, filters, and forms on this page.",
            "Check the page heading to confirm where you are.",
            "Pick one of the quick questions for more specific help.",
        ],
        "If the page looks empty, the previous setup step may not be complete yet.",
        "Next step: choose the question that matches what you are trying to do.",
    )


def _global_answer(question_text: str) -> Dict[str, Any] | None:
    if _contains(question_text, "how does snapclass work"):
        return _answer(
            "How SnapClass Works",
            "SnapClass connects admin, teachers, and students in one attendance workflow.",
            [
                "Admin creates classes, subjects, teachers, and students.",
                "Teacher marks attendance.",
                "Student views subjects, attendance history, and reports.",
            ],
            "If data is missing, one earlier setup step may still be incomplete.",
            "Next step: open the portal for your role and continue from the first setup or attendance page.",
        )
    if _contains(question_text, "what can i do in this app") or question_text == "help":
        return _answer(
            "What You Can Do",
            "SnapClass helps institutes manage classes and attendance from setup to student reports.",
            [
                "Students can join subjects and view attendance.",
                "Teachers can manage assigned classes and mark attendance.",
                "Admins can create classes, subjects, teachers, and students.",
                "Founders can manage institutes, codes, and plans.",
            ],
            "If your page is empty, finish setup for your role first.",
            "Next step: choose your portal and open the page you want help with.",
        )
    if _contains(question_text, "is my data saved"):
        return _answer(
            "Saved Data",
            "Your data is saved after the app shows a successful save or update message.",
            [
                "Attendance appears after the teacher saves it.",
                "Subjects appear after joining with a valid code or class assignment.",
                "Reports appear after attendance exists.",
            ],
            "If you do not see new data, refresh the page and confirm the save message appeared.",
            "Next step: return to the page where the action was saved and refresh once.",
        )
    if _contains(question_text, "data not showing"):
        return _answer(
            "Missing Data",
            "Data usually appears after the previous role completes their step.",
            [
                "Students need a student record and subject/class link.",
                "Teachers need assigned classes and subjects.",
                "Admins need to complete setup in order.",
            ],
            "If the setup is complete and data is still missing, contact your institute admin.",
            "Next step: check the page that owns the missing setup step.",
        )
    if _contains(question_text, "logout"):
        return _answer(
            "Logout",
            "Use the Logout button in the sidebar to leave your current portal.",
            ["Open the sidebar.", "Scroll to the bottom if needed.", "Click Logout."],
            "If the sidebar is hidden on mobile, use the menu button first.",
            "Next step: click Logout in the sidebar.",
        )
    if _contains(question_text, "contact") or _contains(question_text, "help"):
        return _answer(
            "Who To Contact",
            "For account, class, subject, or attendance issues, contact your institute admin first.",
            [
                "Students should contact their teacher or admin.",
                "Teachers should contact their institute admin.",
                "Admins should contact SnapClass support for institute-level issues.",
            ],
            "Share the page name and what you expected to see.",
            "Next step: contact the person who manages your role setup.",
        )
    if _contains(question_text, "wrong class") or _contains(question_text, "wrong subject"):
        return _answer(
            "Wrong Class Or Subject",
            "Wrong class or subject data needs to be corrected by the admin who manages setup.",
            [
                "Students should ask admin to check their class and section.",
                "Teachers should ask admin to check assigned class and subject.",
                "Admins should update the class/subject mapping.",
            ],
            "Do not create duplicate records if one mapping is simply wrong.",
            "Next step: ask admin to verify the class and subject assignment.",
        )
    return None


def _student_answer(question_text: str, page: str) -> Dict[str, Any]:
    if _contains(question_text, "attendance 0"):
        return _answer(
            "Why Attendance Is 0%",
            "Your attendance is 0% because no attendance records are available yet.",
            [
                "Your teacher may not have marked attendance yet.",
                "You may not have joined the subject.",
                "Your student account may not be linked to the correct class.",
            ],
            "Your data appears after your teacher marks attendance or after you join a subject using a join code.",
            "Next step: open My Subjects and check whether your subject is joined.",
        )
    if _contains(question_text, "join") or _contains(question_text, "join code"):
        return _answer(
            "Join A Subject",
            "To join a subject, enter the subject join code shared by your teacher.",
            [
                "Open My Subjects.",
                "Enter the code, for example SC-XAJIOY.",
                "After joining, the subject appears in your subject list.",
            ],
            "If the code does not work, ask your teacher for the latest active code.",
            "Next step: go to My Subjects and enter the code shared by your teacher.",
        )
    if _contains(question_text, "history") or _contains(question_text, "attendance appear"):
        return _answer(
            "Attendance History",
            "Attendance History shows records only after your teacher saves attendance.",
            [
                "See present, absent, or late records.",
                "Check the date, class, subject, and marked-by details.",
                "Use Reports when you need a downloadable summary.",
            ],
            "If this page is blank, attendance may not be marked yet or your subject/class link may be missing.",
            "Next step: check My Subjects first, then ask your teacher to mark attendance.",
        )
    if _contains(question_text, "report") or _contains(question_text, "percentage") or _contains(question_text, "download"):
        return _answer(
            "Student Reports",
            "Your report is generated from live attendance records.",
            [
                "Overall percentage is Present classes divided by Total marked classes.",
                "Download your report when records exist.",
                "Use the report to understand low attendance.",
            ],
            "If reports are blank, attendance has not been marked yet.",
            "Next step: wait for attendance to be marked, then open Reports again.",
        )
    if _contains(question_text, "faceid") or _contains(question_text, "manual attendance"):
        return _answer(
            "FaceID Attendance",
            "FaceID attendance works only after your face is enrolled.",
            [
                "Open FaceID Attendance.",
                "Enroll your face.",
                "Use FaceID only after setup is complete.",
                "Manual attendance can still work even if FaceID is not set up.",
            ],
            "If FaceID is unavailable, your teacher can still mark attendance manually.",
            "Next step: open FaceID Attendance and check your enrollment status.",
        )
    return _answer(
        "Student Dashboard",
        "This page shows your attendance summary, subjects, and recent attendance updates.",
        [
            "Check your overall attendance.",
            "See subjects linked to your account.",
            "Open Attendance History.",
            "View reports when attendance is marked.",
        ],
        "Your data appears after your teacher marks attendance or after you join a subject using a join code.",
        "Next step: open My Subjects and check whether your subject is joined.",
    )


def _teacher_answer(question_text: str, page: str) -> Dict[str, Any]:
    if _contains(question_text, "student count") or _contains(question_text, "students not showing"):
        return _answer(
            "Students In Teacher Pages",
            "Students show when admin adds them to the class assigned to you.",
            [
                "Open My Classes to confirm the assigned class.",
                "Check whether student count is greater than zero.",
                "Use Manual Attendance after students appear.",
            ],
            "If student count is 0, admin may need to add students or fix their class mapping.",
            "Next step: ask admin to confirm students are added to your assigned class.",
        )
    if _contains(question_text, "share") or _contains(question_text, "join my subject"):
        return _answer(
            "Share Subject Code",
            "My Classes lets you create a subject join code for students.",
            [
                "Open My Classes.",
                "Click Share Subject.",
                "Copy the join code or link.",
                "Send it to students so they can join.",
            ],
            "If sharing fails, your subject assignment may be missing.",
            "Next step: click Share Subject on the assigned subject card.",
        )
    if _contains(question_text, "mark all") or _contains(question_text, "save attendance") or _contains(question_text, "mark attendance"):
        return _answer(
            "Manual Attendance",
            "Manual Attendance lets you mark students as Present, Absent, or Late.",
            [
                "Select class.",
                "Select subject.",
                "Select date.",
                "Mark students or use Mark all Present.",
                "Save attendance.",
            ],
            "If students are missing, admin should check whether students were added to the selected class.",
            "Next step: select class and subject, then mark students present or absent.",
        )
    if _contains(question_text, "report") or _contains(question_text, "export"):
        return _answer(
            "Teacher Reports",
            "Reports show live attendance records after attendance is saved.",
            [
                "Filter by class or date.",
                "Review present, absent, and late records.",
                "Export CSV when records exist.",
            ],
            "If reports are blank, no attendance has been saved yet or the wrong filter is selected.",
            "Next step: go to Manual Attendance and save one attendance record.",
        )
    return _answer(
        "Teacher Dashboard",
        "Teacher Dashboard shows your assigned classes, subjects, students, and attendance status.",
        [
            "Open My Classes to review assignments.",
            "Use Manual Attendance to mark attendance.",
            "Open Reports after saving attendance.",
        ],
        "If classes are missing, admin has not assigned you to a class and subject yet.",
        "Next step: open My Classes. If no class appears, ask admin to assign you.",
    )


def _admin_answer(question_text: str, page: str) -> Dict[str, Any]:
    if _contains(question_text, "student"):
        return _answer(
            "Admin Students",
            "Student Code is generated when admin adds a student.",
            [
                "Add student with email, roll number, class, and section.",
                "Share the student code with the student.",
                "Students register using email, code, and password.",
            ],
            "If a student is not visible for a teacher, check that the student is assigned to the correct class and section.",
            "Next step: open Students and verify the student's class mapping.",
        )
    if _contains(question_text, "teacher") or _contains(question_text, "assign"):
        return _answer(
            "Admin Teachers",
            "Teacher Invite Code is used by teachers to create their account.",
            [
                "Add teacher with the login email.",
                "Share the invite code.",
                "Assign teacher to class and subject.",
            ],
            "If teacher is not assigned, they cannot see classes or mark attendance.",
            "Next step: open Teachers and assign class and subject.",
        )
    if _contains(question_text, "class") or _contains(question_text, "subject"):
        return _answer(
            "Classes And Subjects",
            "Classes and subjects are the foundation for teacher assignments and student attendance.",
            [
                "Create class with section.",
                "Add subject for that class.",
                "Assign teacher after both exist.",
            ],
            "If a subject is not showing, confirm it belongs to the selected class.",
            "Next step: create class first, then add subject.",
        )
    return _answer(
        "Admin Setup Flow",
        "Admin setup should be completed from left to right.",
        [
            "Add class.",
            "Add subject.",
            "Add teacher.",
            "Assign teacher to class and subject.",
            "Add students.",
            "Share student invite codes.",
        ],
        "If setup progress is pending, complete the missing step shown on the dashboard.",
        "Next step: complete the setup progress from left to right.",
    )


def _founder_answer(question_text: str, page: str) -> Dict[str, Any]:
    return _answer(
        "Founder Tools",
        "Founder pages manage institutes, access codes, plans, and high-level reporting.",
        [
            "Create institutes.",
            "Generate access codes.",
            "Review plans and institute status.",
            "Check whether an institute has an admin.",
        ],
        "If an institute is missing admin setup, create or share the access code with the admin.",
        "Next step: create the institute, then generate an access code.",
    )


def _public_answer(question_text: str, page: str) -> Dict[str, Any]:
    return _answer(
        "SnapClass Overview",
        "SnapClass helps institutes run attendance from setup to reports.",
        [
            "Students view subjects and attendance.",
            "Teachers mark attendance.",
            "Admins set up classes and users.",
            "Founders manage institutes.",
        ],
        "If you are not logged in, choose the portal that matches your role.",
        "Next step: select Student, Teacher, Admin, or Founder portal.",
    )


@lru_cache(maxsize=512)
def _get_bot_response_cached(question: str, current_page: str, current_role: str) -> tuple[tuple[str, Any], ...]:
    response = _build_bot_response(question, current_page, current_role)
    return tuple(response.items())


def _build_bot_response(
    question: str,
    current_page: str = "unknown",
    current_role: str = "unknown",
) -> Dict[str, Any]:
    question_text = _normalize(question)
    page_key = _normalize(current_page)
    role_key = normalize_role(current_role)

    if _contains(question_text, "what page am i on") or _contains(question_text, "what can i do here"):
        return _page_context_answer(current_page, role_key)

    global_response = _global_answer(question_text)
    if global_response:
        return global_response

    if page_key.startswith("student") or role_key == "student":
        return _student_answer(question_text, page_key)
    if page_key.startswith("teacher") or role_key == "teacher":
        return _teacher_answer(question_text, page_key)
    if page_key.startswith("admin") or role_key == "admin":
        return _admin_answer(question_text, page_key)
    if page_key.startswith("founder") or role_key == "founder":
        return _founder_answer(question_text, page_key)
    return _public_answer(question_text, page_key)


def get_bot_response(
    question: str,
    current_page: str = "unknown",
    current_role: str = "unknown",
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return dict(_get_bot_response_cached(question, current_page, current_role))
