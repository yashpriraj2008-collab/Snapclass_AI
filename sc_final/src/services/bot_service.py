from __future__ import annotations

from typing import Any, Dict, List


_PAGE_TITLES = {
    "landing": "Home",
    "home": "Home",
    "about": "About",
    "features": "Features",
    "pricing": "Pricing",
    "contact": "Contact",
    "student_auth": "Student Login",
    "teacher_auth": "Teacher Login",
    "institute_login": "Institute Admin Login",
    "founder_auth": "Founder Login",
    "founder_dashboard": "Founder Dashboard",
    "founder_institutes": "Founder - Institutes",
    "founder_generate_code": "Founder - Generate Code",
    "founder_all_codes": "Founder - All Codes",
    "founder_allcodes": "Founder - All Codes",
    "founder_codes": "Founder - Codes",
    "founder_plans": "Founder - Plans",
    "founder_reports": "Founder - Reports",
    "founder_settings": "Founder - Settings",
    "admin_dashboard": "Admin Dashboard",
    "admin_classes": "Admin - Classes",
    "admin_subjects": "Admin - Subjects",
    "admin_teachers": "Admin - Teachers",
    "admin_students": "Admin - Students",
    "teacher_dashboard": "Teacher Dashboard",
    "teacher_attendance": "Teacher - Attendance",
    "teacher_manual_attendance": "Teacher - Attendance",
    "teacher_reports": "Teacher - Reports",
    "student_dashboard": "Student Dashboard",
    "student_subjects": "Student - My Subjects",
    "student_history": "Student - Attendance History",
    "student_reports": "Student - Reports",
    "student_faceid": "Student - FaceID",
}

_ROLE_ALIASES = {
    "institute_admin": "admin",
    "institute": "admin",
    "school_admin": "admin",
    "hq": "founder",
    "snapclass_hq": "founder",
    "": "public",
}

_ROLE_INTROS = {
    "founder": "You are using the founder tools for HQ operations.",
    "admin": "You are using the institute admin tools for setup and management.",
    "teacher": "You are using the teacher tools for classes, attendance, and reports.",
    "student": "You are using the student tools for subjects, attendance, reports, and FaceID.",
    "public": "You are on a public page before login.",
    "unknown": "I could not detect your role.",
}

QUESTIONS_BY_ROLE = {
    "public": [
        "What can I do in this app?",
        "How does the full app flow work?",
        "How do I enter Student Portal?",
        "How do I enter Teacher Portal?",
        "How do I enter Admin Portal?",
    ],
    "student": [
        "Why student_id missing?",
        "How do I join a subject?",
        "Why My Subjects is empty?",
        "Why Attendance History is blank?",
        "Why reports blank?",
        "How do I use FaceID?",
    ],
    "teacher": [
        "Why assigned class not showing?",
        "How do I mark attendance?",
        "Why attendance not saving?",
        "How do I generate subject join code?",
        "Which table should I check?",
    ],
    "admin": [
        "How do I create class?",
        "How do I add teacher?",
        "How do I add student?",
        "How do I assign teacher?",
        "Why teacher cannot see class?",
    ],
    "founder": [
        "How do I create institute?",
        "How do I generate access code?",
        "Why institute code is not generated?",
        "Which table stores institute data?",
    ],
}

QUESTIONS_BY_PAGE = {
    "landing": QUESTIONS_BY_ROLE["public"],
    "student_auth": ["How do I enter Student Portal?", "Why student_id missing?"],
    "teacher_auth": ["How do I enter Teacher Portal?", "Why assigned class not showing?"],
    "institute_login": ["How do I enter Admin Portal?", "How do I create class?"],
    "founder_auth": ["How do I create institute?", "How do I generate access code?"],
    "student_dashboard": ["Why student_id missing?", "How do I join a subject?", "Why reports blank?"],
    "student_subjects": ["How do I join a subject?", "Why My Subjects is empty?", "Why student_id missing?"],
    "student_history": ["Why Attendance History is blank?", "Why reports blank?", "Is my data saved in Supabase?"],
    "student_reports": ["Why reports blank?", "Why Attendance History is blank?", "Is my data saved in Supabase?"],
    "student_faceid": ["How do I use FaceID?", "Why FaceID not saving?", "Why student_id missing?"],
    "teacher_dashboard": ["Why assigned class not showing?", "How do I mark attendance?", "Which table should I check?"],
    "teacher_attendance": ["Why attendance not saving?", "How do I mark attendance?", "How do I generate subject join code?"],
    "teacher_reports": ["Why reports blank?", "Which table should I check?", "Is my data saved in Supabase?"],
    "admin_dashboard": ["How do I create class?", "How do I add teacher?", "How do I add student?"],
    "admin_classes": ["How do I create class?", "How do I assign teacher?", "Why teacher cannot see class?"],
    "admin_teachers": ["How do I add teacher?", "How do I assign teacher?", "Why teacher cannot see class?"],
    "admin_students": ["How do I add student?", "Why student_id missing?", "How do I assign teacher?"],
    "founder_dashboard": ["How do I create institute?", "How do I generate access code?", "Which table stores institute data?"],
    "founder_institutes": ["How do I create institute?", "How do I generate access code?", "Why institute code is not generated?"],
    "founder_all_codes": ["Which table stores institute data?", "Why institute code is not generated?", "Is my data saved in Supabase?"],
    "founder_allcodes": ["Which table stores institute data?", "Why institute code is not generated?", "Is my data saved in Supabase?"],
    "founder_codes": ["Which table stores institute data?", "Why institute code is not generated?", "Is my data saved in Supabase?"],
}


def _normalize(text: Any) -> str:
    return str(text or "").strip().lower().replace("-", "_").replace(" ", "_")


def _contains(normalized_text: str, phrase: str) -> bool:
    return _normalize(phrase) in normalized_text


def normalize_role(role: Any) -> str:
    role_key = _normalize(role) or "public"
    return _ROLE_ALIASES.get(role_key, role_key)


def _page_title(current_page: str) -> str:
    page_key = _normalize(current_page)
    return _PAGE_TITLES.get(page_key, page_key.replace("_", " ").title() if page_key else "Unknown Page")


def _clean_list(values: List[str]) -> List[str]:
    return [value for value in values if value]


def get_suggested_questions(current_role: str = "public", current_page: str = "landing") -> List[str]:
    role_key = normalize_role(current_role)
    page_key = _normalize(current_page)
    questions = [
        "What page am I on?",
        *QUESTIONS_BY_PAGE.get(page_key, []),
        *QUESTIONS_BY_ROLE.get(role_key, QUESTIONS_BY_ROLE["public"]),
    ]

    seen = set()
    output: List[str] = []
    for question in questions:
        key = _normalize(question)
        if key and key not in seen:
            seen.add(key)
            output.append(question)

    return output[:7]


def _problem_response(
    title: str,
    answer: str,
    checks: List[str],
    tables: List[str],
    next_action: str,
) -> Dict[str, Any]:
    return {
        "title": title,
        "answer": answer,
        "checks": _clean_list(checks),
        "tables": _clean_list(tables),
        "next_action": next_action,
    }


def _page_context_answer(current_page: str, current_role: str, context: Dict[str, Any] | None) -> Dict[str, Any]:
    role_key = normalize_role(current_role)
    role_label = _ROLE_INTROS.get(role_key, _ROLE_INTROS["unknown"])
    page_label = _page_title(current_page)
    extra = []
    if context:
        if context.get("user_name"):
            extra.append(f"User: {context.get('user_name')}")
        if context.get("last_error"):
            extra.append(f"Last error: {context.get('last_error')}")

    answer = f"{role_label} Current page: {page_label}."
    if extra:
        answer += " " + " ".join(extra)

    return _problem_response(
        title="Current Page",
        answer=answer,
        checks=[
            "Confirm the sidebar or page heading matches this page name.",
            "If it is wrong, check the page key stored in Streamlit session state.",
        ],
        tables=[],
        next_action="Use one of the page-specific questions below for the next step.",
    )


def _supabase_answer(current_page: str, current_role: str) -> Dict[str, Any]:
    page_key = _normalize(current_page)
    role_key = normalize_role(current_role)

    if page_key.startswith("student"):
        tables = ["students", "subject_enrollments", "attendance_records", "attendance_sessions"]
        next_action = "Check the student row first, then verify enrollment or attendance rows."
    elif page_key.startswith("teacher"):
        tables = ["teachers", "teacher_assignments", "attendance_sessions", "attendance_records"]
        next_action = "Check teacher identity, assignment rows, then attendance session and record rows."
    elif page_key.startswith("admin") or role_key == "admin":
        tables = ["classes", "subjects", "teachers", "students", "teacher_assignments"]
        next_action = "Check the setup table for the item you just created or linked."
    elif page_key.startswith("founder") or role_key == "founder":
        tables = ["institutes", "access_codes", "school_codes"]
        next_action = "Check the institute row first, then the code table used by this app."
    else:
        tables = ["institutes", "classes", "subjects", "teachers", "students", "attendance_records"]
        next_action = "Open the workflow-specific table and confirm the latest row exists."

    return _problem_response(
        title="Supabase Data Check",
        answer="Most pages save to Supabase only after a form is submitted successfully. Check the relevant table for a new row with the correct IDs.",
        checks=[
            "Confirm the form showed a success message.",
            "Open the table listed below in Supabase.",
            "Check that required IDs and foreign keys are present.",
        ],
        tables=tables,
        next_action=next_action,
    )


def _problem_map() -> Dict[str, Dict[str, Any]]:
    return {
        "student_id missing": _problem_response(
            title="Student ID Missing",
            answer="The login email must match students.email, and the student resolver must save st.session_state['student_id'].",
            checks=[
                "Confirm the logged-in email exactly matches students.email.",
                "Check that the student row exists in Supabase.",
                "Reload the student page after login so identity can resolve.",
            ],
            tables=["students"],
            next_action="Fix the students.email match, then log in again as the student.",
        ),
        "join a subject": _problem_response(
            title="Join Subject",
            answer="A student joins a subject by entering an active subject join code created by the teacher.",
            checks=[
                "Check subject_join_codes for the code.",
                "Confirm the code is active.",
                "Check subject_enrollments after submitting the code.",
            ],
            tables=["subject_join_codes", "subject_enrollments", "students"],
            next_action="Enter the active join code on My Subjects and refresh the page.",
        ),
        "my subjects is empty": _problem_response(
            title="My Subjects Empty",
            answer="The student is not enrolled yet, or subject_enrollments is missing student_id and subject_id.",
            checks=[
                "Confirm student_id is resolved.",
                "Confirm subject_join_codes has the join code.",
                "Confirm subject_enrollments has student_id and subject_id.",
            ],
            tables=["subject_join_codes", "subject_enrollments", "students"],
            next_action="Use a valid teacher-generated join code to enroll the student.",
        ),
        "attendance history is blank": _problem_response(
            title="Attendance History Blank",
            answer="Attendance history is blank until a teacher marks attendance and attendance_records contains rows for this student_id.",
            checks=[
                "Confirm the teacher saved attendance successfully.",
                "Check attendance_records for the student_id.",
                "Check attendance_sessions for the matching class, subject, and date.",
            ],
            tables=["attendance_records", "attendance_sessions", "students"],
            next_action="Mark one attendance record, then reload Attendance History.",
        ),
        "reports blank": _problem_response(
            title="Reports Blank",
            answer="Reports need live attendance data. If no attendance_records exist for the student_id, show an empty message instead of fake metrics.",
            checks=[
                "Confirm attendance_records has rows for the current student_id.",
                "Confirm attendance_sessions exists for those records.",
                "Confirm report filters use the resolved student_id.",
            ],
            tables=["attendance_records", "attendance_sessions", "students"],
            next_action="Mark attendance once, then open Reports again.",
        ),
        "faceid": _problem_response(
            title="FaceID Help",
            answer="FaceID needs a resolved student_id and working DeepFace/TensorFlow dependencies before it can save embeddings.",
            checks=[
                "Confirm student_id is resolved.",
                "Confirm DeepFace, TensorFlow, tf-keras, and OpenCV are installed.",
                "Check face_embeddings after a successful enrollment.",
            ],
            tables=["face_embeddings", "students"],
            next_action="Resolve student identity first, then enroll FaceID.",
        ),
        "assigned class not showing": _problem_response(
            title="Assigned Class Not Showing",
            answer="The teacher email must match teachers.email, and teacher_assignments must link teacher_id, class_id, and subject_id with active status.",
            checks=[
                "Check teacher.demo@test.com or the login email in teachers.email.",
                "Check teacher_assignments has teacher_id, class_id, subject_id.",
                "Confirm teacher_assignments.status is active.",
            ],
            tables=["teachers", "teacher_assignments", "classes", "subjects"],
            next_action="Ask admin to assign the teacher to the class and subject, then reload Teacher Dashboard.",
        ),
        "teacher cannot see class": _problem_response(
            title="Teacher Cannot See Class",
            answer="The admin setup is incomplete when the teacher row is not linked to class and subject in teacher_assignments.",
            checks=[
                "Confirm the teacher exists in teachers.",
                "Confirm the class and subject exist.",
                "Confirm teacher_assignments links all three IDs and status is active.",
            ],
            tables=["teachers", "teacher_assignments", "classes", "subjects"],
            next_action="Create or fix the teacher assignment row.",
        ),
        "mark attendance": _problem_response(
            title="Mark Attendance",
            answer="Teacher attendance should create or reuse one attendance_session, then save one attendance_record per student.",
            checks=[
                "Select an assigned class and subject.",
                "Set each student status to present, absent, or late.",
                "Submit and check for a success message.",
            ],
            tables=["attendance_sessions", "attendance_records", "students"],
            next_action="Save one small manual attendance session first.",
        ),
        "attendance not saving": _problem_response(
            title="Attendance Not Saving",
            answer="Attendance must save into attendance_sessions and attendance_records. Status values must be present, absent, or late.",
            checks=[
                "Check whether attendance_sessions insert succeeded.",
                "Check whether attendance_records insert or update succeeded.",
                "Read the error message from the attendance service or Supabase RLS policy.",
            ],
            tables=["attendance_sessions", "attendance_records"],
            next_action="Fix the first backend or RLS error shown, then retry attendance save.",
        ),
        "generate subject join code": _problem_response(
            title="Generate Subject Join Code",
            answer="A teacher can generate a subject join code only for an assigned subject.",
            checks=[
                "Confirm teacher_id resolves to teachers.id.",
                "Confirm teacher_assignments links this teacher to the subject.",
                "Check subject_join_codes after generation.",
            ],
            tables=["teachers", "teacher_assignments", "subject_join_codes", "subjects"],
            next_action="Generate the code from the assigned subject card and copy it to the student.",
        ),
        "create class": _problem_response(
            title="Create Class",
            answer="Institute admin creates classes before subjects, students, and teacher assignments can be linked correctly.",
            checks=[
                "Enter class name and section.",
                "Check classes table after save.",
                "Use the created class_id when assigning subjects and teachers.",
            ],
            tables=["classes"],
            next_action="Create the class, then create the subject for that class.",
        ),
        "add teacher": _problem_response(
            title="Add Teacher",
            answer="Admin must add the teacher using the same email the teacher will use to log in.",
            checks=[
                "Confirm teachers.email matches login email.",
                "Confirm status is active.",
                "Assign the teacher after adding the row.",
            ],
            tables=["teachers", "teacher_assignments"],
            next_action="Add the teacher, then assign them to class and subject.",
        ),
        "add student": _problem_response(
            title="Add Student",
            answer="Admin must add the student using the same email the student will use to log in.",
            checks=[
                "Confirm students.email matches login email.",
                "Confirm roll_no, class_name, and section are present.",
                "Reload student login after creating the row.",
            ],
            tables=["students"],
            next_action="Add the student, then log in with that exact email.",
        ),
        "assign teacher": _problem_response(
            title="Assign Teacher",
            answer="Teacher visibility depends on teacher_assignments linking teacher_id, class_id, and subject_id.",
            checks=[
                "Confirm teachers.id is used, not auth user id.",
                "Confirm class_id and subject_id are valid.",
                "Confirm assignment_type and active status are set.",
            ],
            tables=["teacher_assignments", "teachers", "classes", "subjects"],
            next_action="Create the assignment row, then reload Teacher Dashboard.",
        ),
        "create institute": _problem_response(
            title="Create Institute",
            answer="Founder must create the institute before generating an access code or onboarding an admin.",
            checks=[
                "Submit the institute form.",
                "Check institutes table for the new row.",
                "Use the institute_id when generating codes.",
            ],
            tables=["institutes"],
            next_action="Create the institute first, then generate its access code.",
        ),
        "generate access code": _problem_response(
            title="Generate Access Code",
            answer="Access code generation needs an existing institute row and a writable code table.",
            checks=[
                "Confirm the institute exists.",
                "Check whether the app uses access_codes or school_codes.",
                "Confirm the generated code row contains institute_id.",
            ],
            tables=["institutes", "access_codes", "school_codes"],
            next_action="Select the institute and generate a new code.",
        ),
        "institute code is not generated": _problem_response(
            title="Institute Code Not Generated",
            answer="The institute must exist first, and the access or school code table must accept the generated code row.",
            checks=[
                "Confirm the institute row exists.",
                "Check access_codes or school_codes for the new row.",
                "Check Supabase errors or RLS policy if the insert fails.",
            ],
            tables=["institutes", "access_codes", "school_codes"],
            next_action="Create the institute, then retry code generation.",
        ),
        "table stores institute data": _problem_response(
            title="Institute Data Table",
            answer="Institute profile data should live in institutes. Generated onboarding codes may live in access_codes or school_codes depending on the current screen.",
            checks=[
                "Check institutes for institute profile rows.",
                "Check access_codes or school_codes for onboarding codes.",
                "Confirm each code row links back to institute_id.",
            ],
            tables=["institutes", "access_codes", "school_codes"],
            next_action="Open institutes first, then check the code table used by the founder page.",
        ),
    }


def _response_for_problem(question_text: str) -> Dict[str, Any] | None:
    problem_map = _problem_map()
    aliases = {
        "how do i join a subject": "join a subject",
        "why my subjects is empty": "my subjects is empty",
        "why attendance history is blank": "attendance history is blank",
        "why assigned class not showing": "assigned class not showing",
        "why faceid not saving": "faceid",
        "how do i use faceid": "faceid",
        "why teacher cannot see class": "teacher cannot see class",
        "how do i mark attendance": "mark attendance",
        "why attendance not saving": "attendance not saving",
        "how do i generate subject join code": "generate subject join code",
        "how do i generate join code": "generate subject join code",
        "how do i create class": "create class",
        "how do i add teacher": "add teacher",
        "how do i add student": "add student",
        "how do i assign teacher": "assign teacher",
        "how do i create institute": "create institute",
        "how do i generate access code": "generate access code",
        "why code not generated": "institute code is not generated",
        "why institute code is not generated": "institute code is not generated",
        "which table stores institute data": "table stores institute data",
    }

    for alias, key in aliases.items():
        if _contains(question_text, alias):
            return problem_map[key]
    for key, response in problem_map.items():
        if _contains(question_text, key):
            return response
    return None


def _portal_answer(portal: str) -> Dict[str, Any]:
    portal_label = portal.title()
    next_page = {
        "student": "Click Enter Student Portal, then log in with the same email stored in students.email.",
        "teacher": "Click Enter Teacher Portal, then log in with the same email stored in teachers.email.",
        "admin": "Click Enter Institute Admin, then use the institute access code to register or log in.",
    }.get(portal, "Choose the matching portal button on the landing page.")
    tables = {
        "student": ["students"],
        "teacher": ["teachers", "teacher_assignments"],
        "admin": ["institutes", "classes", "subjects", "teachers", "students"],
    }.get(portal, [])
    return _problem_response(
        title=f"Enter {portal_label} Portal",
        answer=f"Use the {portal_label} portal only for that role. The login email must match the role table in Supabase.",
        checks=[
            "Click the correct portal button on the landing page.",
            "Use the exact email that exists in Supabase.",
            "If login works but data is missing, check the role-specific table.",
        ],
        tables=tables,
        next_action=next_page,
    )


def get_bot_response(
    question: str,
    current_page: str = "unknown",
    current_role: str = "unknown",
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    question_text = _normalize(question)
    page_key = _normalize(current_page)
    role_key = normalize_role(current_role)
    context = context or {}

    if _contains(question_text, "what page am i on") or _contains(question_text, "current page"):
        return _page_context_answer(current_page, role_key, context)

    if (
        _contains(question_text, "is my data saved in supabase")
        or _contains(question_text, "saved in supabase")
        or _contains(question_text, "which table should i check")
    ):
        return _supabase_answer(current_page, role_key)

    if _contains(question_text, "enter student portal"):
        return _portal_answer("student")
    if _contains(question_text, "enter teacher portal"):
        return _portal_answer("teacher")
    if _contains(question_text, "enter admin portal"):
        return _portal_answer("admin")

    if _contains(question_text, "full app flow"):
        return _problem_response(
            title="Full App Flow",
            answer="Founder creates the institute and access code. Admin creates classes, subjects, teachers, students, and assignments. Teacher marks attendance. Student joins subjects and views history, reports, and FaceID.",
            checks=[
                "Founder setup must happen first.",
                "Admin setup must link teacher, class, subject, and student data.",
                "Teacher attendance must save before student reports show data.",
            ],
            tables=["institutes", "access_codes", "classes", "subjects", "teachers", "students", "teacher_assignments", "attendance_sessions", "attendance_records"],
            next_action="Start with the role that matches your current demo step.",
        )

    if not question_text or _contains(question_text, "what can i do in this app") or question_text == "help":
        return _problem_response(
            title="What Can I Do?",
            answer="SnapClass AI helps institutes set up classes and users, teachers mark attendance, students view attendance, and founder/HQ manage institutes and codes.",
            checks=[
                "Use Student Portal for attendance history and reports.",
                "Use Teacher Portal for assigned classes and attendance.",
                "Use Institute Admin for setup.",
                "Use SnapClass HQ for institutes and access codes.",
            ],
            tables=[],
            next_action="Choose the portal that matches your role.",
        )

    problem_response = _response_for_problem(question_text)
    if problem_response:
        return problem_response

    if page_key.startswith("student") or role_key == "student":
        return _problem_response(
            title="Student Help",
            answer="Student pages depend on a resolved student_id, subject enrollment, and attendance records saved by a teacher.",
            checks=["Check students.email.", "Check subject_enrollments.", "Check attendance_records for this student_id."],
            tables=["students", "subject_enrollments", "attendance_records"],
            next_action="Start by confirming student_id is resolved.",
        )

    if page_key.startswith("teacher") or role_key == "teacher":
        return _problem_response(
            title="Teacher Help",
            answer="Teacher pages depend on teachers.email resolving to teachers.id and teacher_assignments linking the teacher to a class and subject.",
            checks=["Check teachers.email.", "Check teacher_assignments.", "Check attendance_sessions and attendance_records after save."],
            tables=["teachers", "teacher_assignments", "attendance_sessions", "attendance_records"],
            next_action="Confirm the teacher assignment first.",
        )

    if page_key.startswith("admin") or role_key == "admin":
        return _problem_response(
            title="Admin Help",
            answer="Admin setup should be completed in this order: class, subject, teacher, student, then teacher assignment.",
            checks=["Check classes.", "Check subjects.", "Check teachers and students.", "Check teacher_assignments."],
            tables=["classes", "subjects", "teachers", "students", "teacher_assignments"],
            next_action="Complete the missing setup step and refresh the related page.",
        )

    if page_key.startswith("founder") or role_key == "founder":
        return _problem_response(
            title="Founder Help",
            answer="Founder tools manage institutes, access codes, plans, reports, and settings.",
            checks=["Check institutes.", "Check access_codes or school_codes.", "Confirm the code links to institute_id."],
            tables=["institutes", "access_codes", "school_codes"],
            next_action="Create the institute before generating an access code.",
        )

    return _problem_response(
        title="General App Help",
        answer="SnapClass Bot can explain the current page, guide your next step, and show which Supabase table to check.",
        checks=["Ask what page you are on.", "Ask about the full app flow.", "Ask about a specific student, teacher, admin, or founder problem."],
        tables=[],
        next_action=_page_title(current_page) if context else "Choose a page-aware question.",
    )
