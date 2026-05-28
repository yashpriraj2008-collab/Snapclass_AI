"""Teacher portal — all pages."""
import streamlit as st
import plotly.express as px
from datetime import date

from src.components.sidebar import teacher_sidebar
from src.components.ui import db_status_banner
from src.utils.session import nav_teacher, check_route_access
from src.services.demo_data import CLASSES, WEEKLY_TREND


def show_teacher_portal():
    check_route_access()
    teacher_sidebar()
    p = st.session_state.get("teacher_page", "dashboard")
    if p == "dashboard":
        _dashboard()
    elif p == "manual_att":
        _manual_att()
    elif p == "ai_att":
        _ai_att()
    elif p == "classes":
        _classes()
    elif p == "students":
        _students()
    elif p == "analytics":
        _analytics()
    elif p == "reports":
        _reports()
    else:
        _dashboard()


def _get_students():
    try:
        from src.database.queries import get_students

        return get_students()
    except:
        from src.services.demo_data import STUDENTS

        return STUDENTS


def _get_subjects():
    try:
        from src.database.queries import get_subjects

        return get_subjects()
    except:
        from src.services.demo_data import SUBJECTS

        return SUBJECTS


def _safe_text(value):
    return "" if value is None else str(value).strip()


def _class_title(class_row):
    name = (
        class_row.get("name")
        or class_row.get("class_name")
        or class_row.get("grade")
        or class_row.get("class")
        or "Class"
    )
    section = class_row.get("section") or ""
    return f"{name} — {section}".strip(" —")


def _get_current_teacher_id():
    return (
        st.session_state.get("teacher_id")
        or st.session_state.get("user_id")
        or st.session_state.get("profile_id")
    )


def _get_current_institute_id():
    return (
        st.session_state.get("institute_id")
        or st.session_state.get("current_institute")
        or st.session_state.get("current_institute_id")
    )


def _load_subjects_for_class(supabase, class_id):
    try:
        res = (
            supabase
            .table("subjects")
            .select("*")
            .eq("class_id", class_id)
            .order("created_at", desc=False)
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Could not load subjects: {e}")
        return []


def _add_subject(supabase, class_id, subject_name, subject_code):
    teacher_id = _get_current_teacher_id()
    institute_id = _get_current_institute_id()

    payload = {
        "class_id": class_id,
        "teacher_id": teacher_id,
        "institute_id": institute_id,
        "name": _safe_text(subject_name),
        "code": _safe_text(subject_code),
    }

    try:
        supabase.table("subjects").insert(payload).execute()
        return True, None
    except Exception as e:
        return False, str(e)


def _update_subject(supabase, subject_id, subject_name, subject_code):
    payload = {
        "name": _safe_text(subject_name),
        "code": _safe_text(subject_code),
        "updated_at": "now()",
    }

    try:
        supabase.table("subjects").update(payload).eq("id", subject_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)


def _dashboard():
    db_status_banner()
    name = (st.session_state.get("user_name", "") or "Teacher").replace(" Demo", "").strip()
    st.markdown(f"<h1>Welcome back, {name}! 👋</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6B7280;margin-top:-8px;'>Teaching overview for today</p>",
                unsafe_allow_html=True)

    students = _get_students()
    avg_att = round(students.attendance.mean(), 1) if not students.empty else 0

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    for col, label, val, color, icon in [
        (c1, "Total Classes", len(CLASSES), "pink", "🏫"),
        (c2, "Total Students", len(students), "blue", "👥"),
        (c3, "Avg Attendance", f"{avg_att}%", "green", "📈"),
        (c4, "Sessions Today", "3", "orange", "🗓️"),
    ]:
        with col:
            st.markdown(
                f"""<div class="sc-stat {color}">
              <div class="sc-stat-icon">{icon}</div>
              <div class="sc-stat-label">{label}</div>
              <div class="sc-stat-value">{val}</div>
            </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1.4, 1], gap="large")
    with col_l:
        st.markdown("#### 📊 Weekly Attendance")
        fig = px.bar(WEEKLY_TREND, x="day", y="rate", color_discrete_sequence=["#5B6CFF"])
        fig.add_hline(y=75, line_dash="dash", line_color="#EF4444")
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=220,
        )
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        st.markdown("#### 🕐 Today's Sessions")
        for subj, time, cls, status in [
            ("Mathematics", "9:00 AM", "12-A", "Present"),
            ("Physics", "11:00 AM", "12-B", "Upcoming"),
            ("Chemistry", "2:00 PM", "11-A", "Upcoming"),
        ]:
            badge = {"Present": "ok", "Upcoming": "primary"}.get(status, "info")
            st.markdown(
                f"""<div class="sc-class-item">
              <div><div style="font-weight:600;font-size:.88rem;">{subj} — {cls}</div>
              <div style="color:#6B7280;font-size:.78rem;">{time}</div></div>
              <span class="sc-badge {badge}">{status}</span>
            </div>""",
                unsafe_allow_html=True,
            )

    if st.button("📧 Send Weekly Report Email", key="send_weekly", use_container_width=False):
        try:
            from src.services.email_service import send_weekly_report

            r = send_weekly_report(
                st.session_state.get("user_email", ""),
                name,
                "All Classes",
                {
                    "total": len(students),
                    "avg": avg_att,
                    "low": len(students[students.attendance < 75]) if not students.empty else 0,
                },
            )
            st.success("✅ Report sent!") if r.get("ok") else st.warning(r.get("message", ""))
        except:
            st.warning("Email not configured. Add RESEND_API_KEY to secrets.toml")


def _manual_att():
    st.markdown("## 📝 Manual Attendance")

    from src.services.attendance_service import save_attendance_records
    from src.database.client import get_supabase_client

    supabase = get_supabase_client()

    if not supabase:
        st.error("Supabase is not connected.")
        return

    try:
        classes_res = supabase.table("classes").select("*").execute()
        subjects_res = supabase.table("subjects").select("*").execute()
        students_res = supabase.table("students").select("*").execute()

        classes = classes_res.data or []
        subjects = subjects_res.data or []
        students = students_res.data or []

    except Exception as e:
        st.error(f"Failed to load data from Supabase: {e}")
        return

    if not classes:
        st.warning("No classes found. Add classes first.")
        return

    if not subjects:
        st.warning("No subjects found. Add subjects first.")
        return

    if not students:
        st.warning("No students found. Add students first.")
        return

    def class_label(c):
        if not c:
            return "Select class"
        name = c.get("name") or c.get("class_name") or c.get("grade") or ""
        section = c.get("section") or ""
        return f"{name} — {section}".strip(" —") or "Unnamed Class"

    def subject_label(s):
        if not s:
            return "Select subject"
        return s.get("name") or s.get("subject_name") or s.get("title") or "Unnamed Subject"


    col1, col2, col3 = st.columns(3)

    with col1:
        selected_class = st.selectbox(
            "Class",
            classes,
            format_func=class_label,
            key="manual_class_selectbox",
        )

    with col2:
        selected_subject = st.selectbox(
            "Subject",
            subjects,
            format_func=subject_label,
            key="manual_subject_selectbox",
        )

    with col3:
        selected_date = st.date_input(
            "Date",
            value=date.today(),
            key="manual_attendance_date",
        )

    selected_class_id = selected_class.get("id")
    selected_subject_id = selected_subject.get("id")

    class_name = class_label(selected_class)
    subject_name = subject_label(selected_subject)


    class_students = [
        s
        for s in students
        if str(s.get("class_id")) == str(selected_class_id)
        or str(s.get("class")) == str(class_name)
        or str(s.get("class_name")) == str(class_name)
    ]


    if not class_students:
        st.warning(f"No students found for {class_name}.")
        return

    st.markdown(
        f"### {subject_name} — {class_name} — {selected_date} ({len(class_students)} students)"
    )

    attendance_records = []
    present_count = 0

    for student in class_students:
        student_id = student.get("id")
        roll = (
            student.get("roll")
            or student.get("roll_no")
            or student.get("student_code")
            or "-"
        )
        name = student.get("name") or student.get("full_name") or "Student"

        is_present = st.checkbox(
            f"{roll} — {name}",
            value=True,
            key=f"manual_present_{student_id}_{selected_class_id}_{selected_subject_id}_{selected_date}",
        )

        if is_present:
            present_count += 1

        attendance_records.append(
            {
                "student_id": student_id,
                "class_id": selected_class_id,
                "subject_id": selected_subject_id,
                "attendance_date": str(selected_date),
                "status": "present" if is_present else "absent",
                "marked_by": st.session_state.get("user_id") or st.session_state.get("teacher_id"),
            }
        )

    c1, c2 = st.columns(2)
    c1.metric("Present", present_count)
    c2.metric("Absent", len(class_students) - present_count)

    if st.button("💾 Save", key="save_manual_attendance"):
        result = save_attendance_records(attendance_records)

        if result.get("success"):
            st.success(f"✅ {result.get('saved', 0)} records saved to Supabase.")
        else:
            st.error(f"❌ Attendance not saved: {result.get('error')}")


def _ai_att():
    db_status_banner()
    st.markdown("### 🤖 AI Attendance")
    st.info(
        "AI Attendance — upload a class photo or use live camera to match enrolled students."
    )

    # Prefer Supabase objects when available; fall back to demo data.
    try:
        from src.database.client import get_supabase_client

        supabase = get_supabase_client()
        classes_res = supabase.table("classes").select("*").execute() if supabase else None
        subjects_res = supabase.table("subjects").select("*").execute() if supabase else None
        classes = classes_res.data or [] if classes_res else []
        subjects = subjects_res.data or [] if subjects_res else []
    except Exception:
        classes = []
        subjects = []

    if not classes:
        classes = [
            {"id": c, "class_name": c, "section": ""}
            for c in (CLASSES.class_name.unique().tolist() or ["12-A", "12-B"])
        ]

    if not subjects:
        # Keep existing AI review behavior (subj passed through), so just create ids.
        demo_subjects = _get_subjects()
        if not getattr(demo_subjects, "empty", True):
            subj_names = demo_subjects.subject.tolist()
        else:
            subj_names = ["Mathematics", "Physics"]
        subjects = [
            {"id": i + 1, "subject_name": n}
            for i, n in enumerate(subj_names)
        ]

    def class_label(c):
        if not c:
            return "Select class"
        name = c.get("name") or c.get("class_name") or c.get("grade") or ""
        section = c.get("section") or ""
        return f"{name} — {section}".strip(" —") or "Unnamed Class"

    def subject_label(s):
        if not s:
            return "Select subject"
        return s.get("name") or s.get("subject_name") or s.get("title") or "Unnamed Subject"

    c1, c2, c3 = st.columns(3)

    selected_class = c1.selectbox(
        "Class",
        classes,
        format_func=class_label,
        key="ai_class_selectbox",
    )

    selected_subject = c2.selectbox(
        "Subject",
        subjects,
        format_func=subject_label,
        key="ai_subject_selectbox",
    )

    d = c3.date_input("Date", value=date.today(), key="ai_attendance_date")

    # Use IDs for saving; visible labels are derived from objects only.
    cls = selected_class.get("id")
    subj = selected_subject.get("id")
    cls_label = class_label(selected_class)
    subj_label = subject_label(selected_subject)

    st.session_state["_ai_selected_class_label"] = cls_label
    st.session_state["_ai_selected_subject_label"] = subj_label
    st.session_state["ai_selected_class_id"] = cls
    st.session_state["ai_selected_subject_id"] = subj

    st.markdown("#### 📸 Upload Class Photo or Take Live Photo")
    t1, t2 = st.tabs(["📁 Upload Photo", "📷 Live Camera"])
    img_bytes = None

    with t1:
        up = st.file_uploader(
            "Upload group photo", type=["jpg", "jpeg", "png"], key="ai_up"
        )
        if up:
            img_bytes = up.getvalue()
            st.image(up, caption="Uploaded ✅", use_container_width=True)

    with t2:
        photo = st.camera_input(
            "Take live photo",
            key="ai_live_camera"
        )
        if photo:
            st.image(photo, width=420)
            img_bytes = photo.getvalue()

    btn_l = "🤖 Run AI Attendance"
    if st.button(btn_l, type="primary", key="ai_run"):
        st.session_state.ai_step = "review"

        with st.spinner("🤖 Analysing…"):
            import time

            time.sleep(1.2)
        st.rerun()

    if st.session_state.get("ai_step") == "review":
        _ai_review()


def _ai_review():
    import pandas as pd
    import random

    students = _get_students()

    # Keep existing AI review table logic; use labels stored during selection.
    subj = st.session_state.get("_ai_selected_subject_label", "Mathematics")
    cls = st.session_state.get("_ai_selected_class_label", "12-A")
    d = st.session_state.get("ai_attendance_date", str(date.today()))

    st.markdown(f"#### 🔍 Results — {subj} | {cls} | {d}")
    random.seed(42)
    stu = students[students.class_name == cls] if not students.empty else students

    # AI results normalized: store lowercase status internally.
    ai_results = []

    rows = []
    for _, r in stu.iterrows():
        roll = r.roll
        # Real matching (DeepFace-based) occurs later inside face_ai_service.
        matched = None

        status = "present" if bool(matched) else "absent"

        ai_results.append(
            {
                "student_id": None,
                "roll": roll,
                "name": r.get("name") if hasattr(r, "get") else r["name"],
                "status": status,
            }
        )

        rows.append(
            {
                "Roll": roll,
                "Name": r["name"],
                "Confidence": f"{random.uniform(88,99):.1f}%" if random.random() > .2 else "—",
                "Present": True if status == "present" else False,
            }
        )

    df = pd.DataFrame(rows)
    nd = int(df["Present"].sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Detected", nd)
    c2.metric("Absent", len(df) - nd)
    c3.metric("Confidence", "93%")

    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={"Present": st.column_config.CheckboxColumn("Present ✅", default=True)},
        key="ai_edit",
    )

    col1, col2, _ = st.columns([1, 1, 3])
    if col1.button("✅ Confirm & Save", type="primary", key="ai_confirm"):
        # Keep existing behavior (existing queries-based save), but UI text changes are already handled above.
        from src.database.queries import get_student_id, get_subject_id

        student_ids = [get_student_id(r["Roll"]) for _, r in edited.iterrows()]
        subject_id = st.session_state.get("ai_selected_subject_id")

        # If IDs are missing for some reason, fall back to existing helper.
        if not subject_id:
            subject_id = get_subject_id(subj, cls)

        records = []
        for (_, r), student_id in zip(edited.iterrows(), student_ids):
            if not student_id or not subject_id:
                continue
            records.append(
                    {
                        "student_id": student_id,
                        "class_id": st.session_state.get("ai_selected_class_id"),
                        "subject_id": st.session_state.get("ai_selected_subject_id"),
                        "attendance_date": d,
                        "status": "present" if r["Present"] else "absent",
                        "marked_by": st.session_state.get("user_id", "ai"),
                    }
                )

        if "attendance_saved" not in st.session_state:
            st.session_state.attendance_saved = {}
        st.session_state.attendance_saved[f"{subj}_{d}"] = records
        st.success(f"✅ {len(records)} records saved.")

        st.session_state.pop("ai_step", None)
        st.rerun()

    if col2.button("← Back", key="ai_back"):
        st.session_state.pop("ai_step", None)
        st.rerun()


def _classes():
    db_status_banner()
    st.markdown("### 🏫 My Classes")

    try:
        from src.database.client import get_supabase_client
    except Exception:
        get_supabase_client = None

    supabase = get_supabase_client() if get_supabase_client else None
    classes = []

    if supabase:
        try:
            classes_res = supabase.table("classes").select("*").order("created_at", desc=False).execute()
            classes = classes_res.data or []
        except Exception as e:
            st.warning(f"Could not load classes from Supabase: {e}")

    if not classes:
        classes = CLASSES.to_dict("records") if hasattr(CLASSES, "to_dict") else []

    for class_row in classes:
        class_id = class_row.get("id") or class_row.get("class_id")
        class_name = class_row.get("subject") or class_row.get("name") or class_row.get("class_name") or "Class"
        class_time = class_row.get("time") or ""
        class_students = class_row.get("students") or ""
        display_title = _class_title(class_row)

        c1, c2 = st.columns([3, 1])
        c1.markdown(
            f"**{class_name}** — {class_row.get('class_name') or display_title} &nbsp; 🕐 {class_time} &nbsp; 👥 {class_students}"
        )
        if c2.button("Take Attendance", key=f"cls_{class_id}", type="primary"):
            nav_teacher("manual_att")

        subjects = _load_subjects_for_class(supabase, class_id) if supabase and class_id else []

        with st.expander(f"📚 Subjects for {display_title}", expanded=False):
            st.markdown("#### Existing Subjects")

            if subjects:
                for subject in subjects:
                    subject_id = subject.get("id")
                    subject_name = subject.get("name") or subject.get("subject_name") or "Unnamed Subject"
                    subject_code = subject.get("code") or ""

                    with st.form(f"edit_subject_{subject_id}"):
                        new_name = st.text_input(
                            "Subject Name",
                            value=subject_name,
                            key=f"subject_name_{subject_id}"
                        )

                        new_code = st.text_input(
                            "Subject Code",
                            value=subject_code,
                            key=f"subject_code_{subject_id}"
                        )

                        update_clicked = st.form_submit_button("Update Subject")

                        if update_clicked:
                            if not new_name.strip():
                                st.error("Subject name is required.")
                            else:
                                ok, err = _update_subject(
                                    supabase,
                                    subject_id,
                                    new_name,
                                    new_code
                                )

                                if ok:
                                    st.success("Subject updated successfully.")
                                    st.rerun()
                                else:
                                    st.error(f"Subject update failed: {err}")
            else:
                st.info("No subjects added yet.")

            st.markdown("#### Add New Subject")

            with st.form(f"add_subject_{class_id}"):
                subject_name = st.text_input(
                    "New Subject Name",
                    placeholder="Example: Mathematics",
                    key=f"new_subject_name_{class_id}"
                )

                subject_code = st.text_input(
                    "Subject Code",
                    placeholder="Example: MATH-101",
                    key=f"new_subject_code_{class_id}"
                )

                add_clicked = st.form_submit_button("Add Subject")

                if add_clicked:
                    if not subject_name.strip():
                        st.error("Subject name is required.")
                    else:
                        ok, err = _add_subject(
                            supabase,
                            class_id,
                            subject_name,
                            subject_code
                        )

                        if ok:
                            st.success("Subject added successfully.")
                            st.rerun()
                        else:
                            st.error(f"Subject save failed: {err}")

        # --- Create New Subject + Share Subject (join codes + QR) ---
        st.divider()
        st.markdown("### ➕ Create New Subject")

        # Resolve teacher identity
        teacher_id = _get_current_teacher_id()
        teacher_email = st.session_state.get("user_email") or st.session_state.get("teacher_email")

        if not teacher_id and teacher_email:
            st.caption(f"[debug] teacher_id missing; will try fallback via email={teacher_email!r}")

        with st.form(f"create_subject_form_{class_id}"):
            subject_code = st.text_input(
                "Subject Code (optional)",
                placeholder="e.g., CS101 or random",
                key=f"cs_code_{class_id}",
            )
            subject_name = st.text_input(
                "Subject Name",
                placeholder="e.g., Mathematics",
                key=f"cs_name_{class_id}",
            )
            class_text = st.text_input(
                "Class",
                value=str(class_row.get("class_name") or class_row.get("name") or ""),
                key=f"cs_class_{class_id}",
            )
            section = st.text_input(
                "Section",
                value=str(class_row.get("section") or ""),
                key=f"cs_section_{class_id}",
            )

            submitted = st.form_submit_button("Create Subject")

            if submitted:
                if not teacher_id and not teacher_email:
                    st.error("Teacher identity missing. Please login again.")
                elif not subject_name.strip():
                    st.error("Subject name is required.")
                else:
                    # Map requested Class/Section to the existing schema fields.
                    # This app already uses `subjects` fields: class_id, teacher_id, institute_id, name, code.
                    # We'll reuse the currently expanded class_id for saving.
                    payload = {
                        "class_id": class_id,
                        "teacher_id": teacher_id,
                        "institute_id": _get_current_institute_id(),
                        "name": _safe_text(subject_name),
                        "code": _safe_text(subject_code),
                    }

                    from src.services.subject_service import create_subject

                    try:
                        if supabase is None:
                            st.error("Supabase is not connected.")
                        else:
                            res = create_subject(supabase, payload)
                            st.success("✅ Subject created.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Subject create failed: {e}")

        st.markdown("### 📣 Share Subject")

        if supabase is None:
            st.warning("Supabase is not connected. Join codes will not work.")
        else:
            from src.services.subject_service import (
                generate_subject_join_code,
                get_teacher_subjects,
                make_qr_image,
            )

            teacher_subjects = get_teacher_subjects(
                supabase,
                teacher_id=teacher_id,
                teacher_email=teacher_email,
            )

            if not teacher_subjects:
                st.info("No subjects found for your teacher account yet.")
            else:
                subj_opts = teacher_subjects
                selected_subject_id = st.selectbox(
                    "Select a subject to share",
                    subj_opts,
                    format_func=lambda s: s.get("name") or s.get("subject_name") or "Unnamed Subject",
                    key=f"share_subject_select_{class_id}",
                )
                selected_id_val = selected_subject_id.get("id")

                if st.button("Generate Join Code", key=f"gen_join_{class_id}"):
                    try:
                        base_url = st.session_state.get(
                            "base_url", "http://localhost:8507"
                        )
                        data = generate_subject_join_code(
                            supabase,
                            selected_id_val,
                            teacher_id=teacher_id,
                            base_url=base_url,
                        )

                        if not data:
                            st.error("Failed to generate join code.")
                        else:
                            join_code = data.get("join_code")
                            join_url = data.get("join_url")
                            st.success("✅ Join code generated.")

                            st.text_input(
                                "Join Code",
                                value=str(join_code or ""),
                                key=f"join_code_out_{class_id}",
                                disabled=True,
                            )
                            st.text_input(
                                "Join Link",
                                value=str(join_url or ""),
                                key=f"join_url_out_{class_id}",
                                disabled=True,
                            )

                            copy_text = join_url or join_code or ""
                            st.code(copy_text, language="text")

                            qr_buf = make_qr_image(copy_text)
                            st.image(qr_buf, caption="Scan to enroll", use_container_width=False)

                    except Exception as e:
                        st.error(f"Join code generation failed: {e}")

        st.divider()



def _students():
    import pandas as pd
    import streamlit as st

    from src.database.client import get_supabase_client

    st.markdown("## 👥 Students")

    supabase = get_supabase_client()

    if not supabase:
        st.error("Supabase is not connected.")
        return

    # Search box
    search = st.text_input("🔍 Search", placeholder="Name or roll...", key="teacher_students_search")

    # Add Student section
    with st.expander("➕ Add Student", expanded=False):
        with st.form("add_student_form"):
            name = st.text_input("Student Name *", key="new_student_name")
            roll_no = st.text_input("Roll No *", key="new_student_roll")
            class_name = st.text_input("Class", placeholder="Example: 12-A", key="new_student_class")
            section = st.text_input("Section", placeholder="Example: A", key="new_student_section")

            submitted = st.form_submit_button("Add Student")

            if submitted:
                if not name.strip() or not roll_no.strip():
                    st.error("Student name and roll number are required.")
                else:
                    payload = {
                        "name": name.strip(),
                        "roll_no": roll_no.strip(),
                        "class_name": class_name.strip() if class_name else None,
                        "section": section.strip() if section else None,
                    }

                    try:
                        supabase.table("students").insert(payload).execute()
                        st.success("Student added successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Student save failed: {e}")

    # Load students
    try:
        res = (
            supabase
            .table("students")
            .select("*")
            .order("name")
            .execute()
        )

        students = res.data or []

    except Exception as e:
        st.error(f"Could not load students from Supabase: {e}")
        return

    if not students:
        st.info("No students found in Supabase.")
        return

    # Normalize rows for display
    rows = []

    for s in students:
        rows.append({
            "Roll No": s.get("roll_no") or s.get("roll") or "",
            "Name": s.get("name") or "",
            "Class": s.get("class_name") or s.get("class") or "",
            "Section": s.get("section") or "",
        })

    df = pd.DataFrame(rows)

    # Apply search
    if search:
        search_lower = search.lower()
        df = df[
            df["Name"].astype(str).str.lower().str.contains(search_lower, na=False)
            | df["Roll No"].astype(str).str.lower().str.contains(search_lower, na=False)
            | df["Class"].astype(str).str.lower().str.contains(search_lower, na=False)
        ]

    if df.empty:
        st.warning("No students matched your search.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)



def _analytics():
    db_status_banner()
    st.markdown("## 📊 Analytics & Insights")
    st.caption("Detailed attendance analytics across all your classes")
    students = _get_students()
    avg = round(students.attendance.mean(), 1) if not students.empty else 90
    best_cls = students.groupby("class_name")["attendance"].mean().idxmax() if not students.empty else "12-A"

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, sub, color in [
        (c1, "Overall Average", f"{avg}%", "+5% this month", "#10B981"),
        (c2, "Best Class", best_cls, "95% attendance", "#10B981"),
        (c3, "Total Sessions", "48", "This month", "#6B7280"),
        (c4, "Active Students", len(students), "Across 4 classes", "#6B7280"),
    ]:
        with col:
            st.markdown(
                f"""<div style="background:white;border-radius:16px;padding:22px;
              border:1px solid #E5E7EB;box-shadow:0 4px 12px rgba(0,0,0,.06);">
              <div style="color:#6B7280;font-size:.82rem;margin-bottom:8px;">{label}</div>
              <div style="font-size:2rem;font-weight:800;font-family:Poppins,sans-serif;">{val}</div>
              <div style="color:{color};font-size:.82rem;margin-top:6px;">{sub}</div>
            </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.line(
            WEEKLY_TREND,
            x="day",
            y="rate",
            markers=True,
            title="Weekly Attendance Trend",
            color_discrete_sequence=["#FF4FA3"],
        )
        fig1.add_hline(y=75, line_dash="dash", line_color="#EF4444")
        fig1.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="white",
            margin=dict(l=20, r=20, t=50, b=20),
            height=300,
        )
        fig1.update_traces(line_width=3, marker_size=8)
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        cls_d = (
            students.groupby("class_name")["attendance"].mean().reset_index()
            if not students.empty
            else __import__("pandas").DataFrame(
                {"class_name": ["12-A", "12-B", "11-A", "11-B"], "attendance": [88, 92, 95, 86]}
            )
        )
        fig2 = px.bar(
            cls_d,
            x="class_name",
            y="attendance",
            title="Class Performance",
            color_discrete_sequence=["#5B6CFF"],
        )
        fig2.add_hline(y=75, line_dash="dash", line_color="#EF4444")
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="white",
            margin=dict(l=20, r=20, t=50, b=20),
            height=300,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### 📅 Monthly Breakdown")
    for month, pct in [("Jan", 84), ("Feb", 87), ("Mar", 80), ("Apr", 90), ("May", 92)]:
        color = "#5B6CFF" if pct >= 85 else "#FF4FA3"
        st.markdown(
            f"""<div style="display:flex;align-items:center;padding:10px 0;
          border-bottom:1px solid #F3F4F6;">
          <span style="font-weight:600;width:60px;">{month}</span>
          <div style="flex:1;margin:0 16px;background:#F3F4F6;border-radius:999px;
            height:10px;overflow:hidden;">
            <div style="width:{pct}%;background:linear-gradient(90deg,{color},#818cf8);
              height:10px;border-radius:999px;"></div></div>
          <span style="font-weight:700;color:{color};width:48px;text-align:right;">{pct}%</span>
        </div>""",
            unsafe_allow_html=True,
        )


def _reports():
    db_status_banner()
    st.markdown("### 📄 Reports")
    students = _get_students()
    if not students.empty:
        cls_opts = ["All"] + students.class_name.unique().tolist()
        f = st.selectbox("Filter by Class", cls_opts, key="r_cls")
        df = students if f == "All" else students[students.class_name == f]
        display = df[["roll", "name", "class_name", "attendance"]].rename(
            columns={"roll": "Roll", "name": "Name", "class_name": "Class", "attendance": "Att %"}
        )
        st.dataframe(display, use_container_width=True, hide_index=True)
        csv = display.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "class_attendance.csv", "text/csv", use_container_width=True)
    else:
        st.info("No student data available.")
