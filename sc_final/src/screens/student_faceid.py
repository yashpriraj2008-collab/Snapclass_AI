"""Student FaceID attendance â€” enrollment + verification."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any
import ast
import html
import json
import os

try:
    import importlib

    st = importlib.import_module("streamlit")
except Exception:
    # Provide a clear error when streamlit is not available at runtime.
    raise ImportError("streamlit is not installed. Please install it with: pip install streamlit")

from src.database.client import get_supabase_client
from src.services.face_ai_service import (
    check_face_enrolled,
    cosine_similarity,
    deepface_error_message,
    generate_face_embedding,
    is_deepface_available,
    save_face_embedding_to_supabase,
)
from src.services.face_service import check_image_quality
from src.services.subject_service import get_student_enrolled_subjects
from src.utils.session import nav_student
from src.utils.user_guards import show_faceid_unavailable


def _debug_enabled() -> bool:
    try:
        from src.screens.student_dashboard import _debug_enabled as dashboard_debug_enabled

        return dashboard_debug_enabled()
    except Exception:
        try:
            from src.utils.perf import perf_enabled

            return perf_enabled()
        except Exception:
            return bool(st.session_state.get("debug_mode"))


def _show_debug(title: str, message: Any) -> None:
    if not _debug_enabled():
        return
    with st.expander(title, expanded=False):
        st.code(str(message or ""))


def _dev_errors_visible() -> bool:
    return _debug_enabled()


def _show_faceid_dev_error(exc: Exception, payload: dict[str, Any]) -> None:
    if not _dev_errors_visible():
        return
    st.exception(exc)
    with st.expander("Developer Debug", expanded=False):
        st.json(payload)


def _rpc_payload_data(response: Any) -> dict[str, Any]:
    data = getattr(response, "data", response)
    if isinstance(data, list):
        data = data[0] if data else {}
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {"message": data}
    return data if isinstance(data, dict) else {}


def _rpc_exception_payload(exc: Exception) -> dict[str, Any]:
    for candidate in (
        getattr(exc, "args", (None,))[0] if getattr(exc, "args", ()) else None,
        getattr(exc, "message", None),
        str(exc),
    ):
        if isinstance(candidate, dict):
            return candidate
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(candidate)
            except (TypeError, ValueError, SyntaxError):
                continue
            if isinstance(parsed, dict):
                return parsed
    return {}


def _mark_faceid_attendance_with_rpc(
    supabase,
    *,
    student_email: str,
    subject_code: str,
) -> dict[str, Any]:
    try:
        response = supabase.rpc(
            "mark_faceid_attendance_demo",
            {
                "p_student_email": student_email,
                "p_subject_code": subject_code,
            },
        ).execute()
        return _rpc_payload_data(response)
    except Exception as exc:
        payload = _rpc_exception_payload(exc)
        if payload.get("ok") is True:
            return payload
        raise


def validate_student_subject_match(
    supabase,
    student_email: str,
    subject_code: str,
    *,
    selected_subject: dict[str, Any] | None = None,
) -> tuple[bool, Any]:
    result = (
        supabase
        .table("students")
        .select("id, email, class_id")
        .ilike("email", student_email)
        .limit(1)
        .execute()
    )

    students = result.data or []
    if not students:
        return False, "Student profile not found."

    student = students[0]

    subject_result = (
        supabase
        .table("subjects")
        .select("id, subject_code, class_id")
        .ilike("subject_code", subject_code)
        .limit(1)
        .execute()
    )

    subjects = subject_result.data or []
    if not subjects:
        return False, "Subject not found."

    subject = subjects[0]
    selected_subject = selected_subject or {}

    enrollment_rows: list[dict[str, Any]] = []
    try:
        enrollment_rows = (
            supabase
            .table("subject_enrollments")
            .select("*")
            .eq("student_id", student["id"])
            .eq("subject_id", subject["id"])
            .limit(1)
            .execute()
            .data
            or []
        )
    except Exception:
        enrollment_rows = []

    enrollment = enrollment_rows[0] if enrollment_rows else {}
    if enrollment:
        enrollment_class_id = enrollment.get("class_id") or subject.get("class_id")
        if enrollment_class_id and subject.get("class_id") and str(enrollment_class_id) != str(subject.get("class_id")):
            return False, "This subject enrollment is linked to a different class. Ask admin to fix the subject enrollment."
    elif student.get("class_id") and subject.get("class_id") and str(student.get("class_id")) != str(subject.get("class_id")):
        return False, "Your class does not match this subject. Ask admin to fix your class mapping."

    return True, {
        "student_id": student["id"],
        "subject_id": subject["id"],
        "class_id": subject["class_id"],
        "institute_id": subject.get("institute_id") or student.get("institute_id"),
        "teacher_id": selected_subject.get("teacher_id") or subject.get("teacher_id"),
        "enrollment": enrollment,
    }


def _session_email() -> str:
    email = (
        st.session_state.get("student_email")
        or st.session_state.get("user_email")
        or st.session_state.get("auth_user_email")
        or st.session_state.get("email")
    )
    if not email and isinstance(st.session_state.get("user"), dict):
        email = st.session_state["user"].get("email")
    return str(email or "").strip().lower()


def _session_auth_user_id() -> str:
    user = st.session_state.get("user")
    return str(
        st.session_state.get("auth_user_id")
        or st.session_state.get("user_id")
        or (user.get("id") if isinstance(user, dict) else "")
        or (user.get("user_id") if isinstance(user, dict) else "")
        or ""
    ).strip()


def _class_label(row: dict | None) -> str:
    row = row or {}
    class_name = row.get("class_name") or row.get("name") or row.get("grade") or row.get("class") or ""
    section = row.get("section") or ""
    if class_name and section:
        return f"{class_name}-{section}"
    return str(class_name or "")


def get_current_student_context(supabase=None) -> dict[str, Any]:
    # Remove cached old student data to avoid cross-institute leakage.
    for key in [
        "student_id",
        "student_email",
        "student_name",
        "user_name",
        "institute_id",
        "active_institute_id",
        "student_class_id",
        "student_class",
        "student_section",
        "roll_no",
        "user_roll",
        "student_profile",
        "student",
        "user_profile_found",
    ]:
        if key in st.session_state:
            try:
                del st.session_state[key]
            except Exception:
                pass

    if not supabase:
        supabase = get_supabase_client()
    email = _session_email()
    auth_user_id = _session_auth_user_id()
    ctx: dict[str, Any] = {
        "student_id": None,
        "auth_user_id": auth_user_id,
        "student_email": email,
        "student_name": "",
        "institute_id": None,
        "class_id": None,
        "class_name": "",
        "section": "",
        "roll_no": "",
        "user_profile": {},
        "user_profile_found": False,
        "student": {},
    }
    if not supabase or not (email or auth_user_id):
        return ctx

    try:
        profile = {}
        if auth_user_id:
            rows = supabase.table("user_profiles").select("*").eq("user_id", auth_user_id).limit(1).execute().data or []
            if not rows:
                rows = supabase.table("user_profiles").select("*").eq("id", auth_user_id).limit(1).execute().data or []
            profile = rows[0] if rows else {}
        if not profile and email:
            rows = supabase.table("user_profiles").select("*").eq("email", email).limit(1).execute().data or []
            profile = rows[0] if rows else {}

        ctx["user_profile"] = profile
        ctx["user_profile_found"] = bool(profile)

        if profile and str(profile.get("role") or "").strip().lower() != "student":
            return ctx

        student = {}
        if auth_user_id:
            rows = supabase.table("students").select("*").eq("user_id", auth_user_id).limit(1).execute().data or []
            student = rows[0] if rows else {}
        if not student and email:
            rows = supabase.table("students").select("*").eq("email", email).limit(1).execute().data or []
            student = rows[0] if rows else {}
        if student:
            # Sync institute_id into user_profiles after the student row exists.
            if profile and not profile.get("institute_id") and profile.get("id") and student.get("institute_id"):
                try:
                    student_institute_id = student.get("institute_id")
                    supabase.table("user_profiles").update({"institute_id": student_institute_id}).eq("id", profile.get("id")).execute()
                    profile["institute_id"] = student_institute_id
                    st.cache_data.clear()
                except Exception as exc:
                    _show_debug("Developer Debug", {"user_profile_institute_sync_error": str(exc)})
            ctx.update(
                {
                    "student_id": str(student.get("id") or ""),
                    "student_email": str(student.get("email") or email).lower(),
                    "student_name": student.get("name") or student.get("full_name") or ctx.get("student_name"),
                    "institute_id": student.get("institute_id") or ctx.get("institute_id"),
                    "class_id": student.get("class_id") or ctx.get("class_id"),
                    "class_name": student.get("class_name") or ctx.get("class_name"),
                    "section": student.get("section") or ctx.get("section"),
                    "roll_no": student.get("roll_no") or ctx.get("roll_no"),
                    "student": student,
                }
            )
    except Exception as exc:
        _show_debug("Developer Debug", {"student_context_error": str(exc)})
    return ctx


def _identity_from_context(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "student_id": ctx.get("student_id"),
        "user_id": ctx.get("auth_user_id") or st.session_state.get("auth_user_id") or st.session_state.get("user_id"),
        "auth_user_id": ctx.get("auth_user_id") or st.session_state.get("auth_user_id") or st.session_state.get("user_id"),
        "institute_id": ctx.get("institute_id"),
        "user_email": ctx.get("student_email"),
        "user_name": ctx.get("student_name"),
        "roll_no": ctx.get("roll_no"),
        "name": ctx.get("student_name"),
    }


def _load_joined_subjects(supabase, student_id: str) -> list[dict[str, Any]]:
    try:
        subjects = get_student_enrolled_subjects(supabase, student_id)
    except Exception as exc:
        _show_debug("Developer Debug", {"joined_subjects_error": str(exc)})
        subjects = []
    clean: list[dict[str, Any]] = []
    for subject in subjects:
        subject_id = subject.get("subject_id") or subject.get("id")
        class_id = subject.get("class_id")
        if not subject_id:
            continue
        clean.append(
            {
                **subject,
                "subject_id": str(subject_id),
                "subject_name": subject.get("subject_name") or subject.get("name") or "Subject",
                "subject_code": subject.get("subject_code") or subject.get("code") or "",
                "class_id": str(class_id or "") if class_id else "",
                "institute_id": str(subject.get("institute_id") or "") if subject.get("institute_id") else "",
                "enrollment_class_id": str(subject.get("enrollment_class_id") or "") if subject.get("enrollment_class_id") else "",
                "enrollment_institute_id": str(subject.get("enrollment_institute_id") or "") if subject.get("enrollment_institute_id") else "",
                "class_name": subject.get("class_name") or "",
                "section": subject.get("section") or "",
                "class_label": subject.get("class_label") or _class_label(subject.get("class") or subject),
                "teacher_id": str(subject.get("teacher_id") or "") if subject.get("teacher_id") else "",
                "teacher_name": subject.get("teacher_name") or subject.get("teacher_email") or "",
            }
        )
    return clean


def _subject_option_label(subject: dict[str, Any]) -> str:
    name = subject.get("subject_name") or "Subject"
    code = subject.get("subject_code") or ""
    class_label = subject.get("class_label") or "Class not linked"
    teacher_name = subject.get("teacher_name") or "Teacher not linked"
    return f"{name} {code} - Class {class_label} - {teacher_name}".strip()


def _check_face_enrolled_by_student_id(supabase, student_id: str) -> tuple[bool, Any]:
    auth_user_id = _session_auth_user_id()
    if not supabase or not (student_id or auth_user_id):
        return False, None
    lookups = []
    if student_id:
        lookups.append(("student_id", student_id))
    if auth_user_id:
        lookups.append(("user_id", auth_user_id))
    last_error = None
    for column, value in lookups:
        try:
            query = supabase.table("face_embeddings").select("*").eq(column, value)
            try:
                rows = query.eq("status", "active").limit(1).execute().data or []
            except Exception:
                rows = query.limit(1).execute().data or []
            if rows:
                return True, rows[0]
        except Exception as exc:
            last_error = exc
    if last_error:
        _show_debug("Developer Debug", {"face_embedding_lookup_error": str(last_error)})
    return False, None


def show_faceid() -> None:
    if st.session_state.get("faceid_step") == "confirmed":
        _confirmation_screen()
        return

    st.markdown(
        """
        <div class="faceid-page-header">
          <div class="faceid-page-kicker">STUDENT ATTENDANCE</div>
          <div class="faceid-page-title">FaceID Attendance</div>
          <div class="faceid-page-copy">
            Verify your identity with a clear photo, then securely record attendance for the selected subject.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    supabase = get_supabase_client()
    ctx = get_current_student_context(supabase) if supabase else {}
    identity = _identity_from_context(ctx) if ctx else None
    enrolled = False
    if supabase and identity:
        try:
            enrolled, _ = _check_face_enrolled_by_student_id(supabase, str(ctx.get("student_id") or ""))
        except Exception:
            enrolled = False

    ai_ready = is_deepface_available()
    if not ai_ready:
        show_faceid_unavailable()
        _show_debug("Developer Debug", deepface_error_message() or "FaceID engine unavailable.")
        return

    tab1, tab2 = st.tabs(["Mark Attendance", "Enroll FaceID"])
    with tab1:
        _mark_tab(ai_ready, ctx, enrolled)
    with tab2:
        _enroll_tab(ai_ready)

    back_left, back_col, back_right = st.columns([0.12, 0.76, 0.12])
    with back_col:
        if st.button("Back to Dashboard", key="faceid_back"):
            st.session_state.pop("faceid_step", None)
            nav_student("dashboard")


def _legacy_show_faceid() -> None:
    st.markdown("### ðŸªª FaceID Attendance")

    ai_ready = is_deepface_available()
    if not ai_ready:
        show_faceid_unavailable()
        _show_debug("Developer Debug", deepface_error_message() or "FaceID engine unavailable.")
        return
        err = deepface_error_message() or "DeepFace could not load."
        st.markdown(
            f"""
            <div class="sc-alert warning">
              âš ï¸ <strong>Real AI attendance disabled</strong> â€” {err}
              <div style="margin-top:6px;">Activate Python 3.11 venv and run: <code>pip install deepface tf-keras tensorflow opencv-python-headless</code></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab1, tab2 = st.tabs(["ðŸªª Mark Attendance", "ðŸ“¸ Enroll My Face"])
    with tab1:
        _mark_tab(ai_ready)
    with tab2:
        _enroll_tab(ai_ready)

    if st.button("â† Back to Dashboard", key="faceid_back"):
        st.session_state.pop("faceid_step", None)
        nav_student("dashboard")


def _get_identity(supabase) -> dict[str, Any] | None:
    ctx = get_current_student_context(supabase)
    if not ctx.get("student_id"):
        return None
    return _identity_from_context(ctx)


def _enroll_tab(ai_ready: bool) -> None:
    supabase = get_supabase_client()
    identity = _get_identity(supabase) if supabase else None

    st.markdown("#### Enroll Your Face")
    st.caption("Enroll once. After enrollment you can mark attendance with FaceID.")

    if not supabase:
        st.warning("Supabase is not configured. Add .streamlit/secrets.toml.")
        return

    if not identity or not identity.get("student_id"):
        st.warning("Student profile not found. Contact admin.")
        return

    st.caption(f"Student: {identity.get('user_name') or 'Student'} | Roll: {identity.get('roll_no') or 'Not set'}")

    col1, col2 = st.columns(2)
    with col1:
        cam = st.camera_input("Take selfie", key="enroll_cam")
    with col2:
        up = st.file_uploader("Or upload photo", type=["jpg", "jpeg", "png"], key="enroll_up")

    img = cam if cam else up
    img_bytes = img.getvalue() if img else None
    if not img_bytes:
        return

    if st.button(
        "Save My Face",
        type="primary",
        use_container_width=True,
        key="enroll_save",
        disabled=not ai_ready,
    ):
        if not ai_ready:
            show_faceid_unavailable()
            _show_debug("Developer Debug", deepface_error_message() or "FaceID engine unavailable.")
            return

        quality = check_image_quality(img_bytes)
        if not quality.get("ok"):
            st.error(f"Face enrollment failed: {quality.get('message')}")
            return

        with st.spinner("Extracting face embedding..."):
            embedding, error = generate_face_embedding(img_bytes)

        if error or embedding is None:
            st.error("Face enrollment failed. Please use a clear front-facing photo and try again.")
            _show_debug("Developer Debug", error or "Face embedding could not be generated.")
            return

        result = save_face_embedding_to_supabase(
            supabase=supabase,
            student_identity=identity,
            embedding=embedding,
        )

        if isinstance(result, dict) and result.get("error"):
            st.error("Face enrollment failed.")
            _show_debug("Developer Debug", result.get("error"))
            return

        enrolled, row = check_face_enrolled(supabase, identity)
        if not enrolled:
            st.error("Face saved, but verification query failed. Please try again.")
            return

        st.success("Face saved successfully in Supabase.")
        st.caption(f"User ID: {identity.get('user_id') or 'not set'} | Email: {identity.get('user_email') or 'not set'}")
        st.balloons()


def _mark_tab(ai_ready: bool, ctx: dict[str, Any] | None = None, enrolled: bool | None = None) -> None:
    step = st.session_state.get("faceid_step", "scan")
    if step == "confirmed":
        _confirmation_screen()
        return

    supabase = get_supabase_client()
    ctx = ctx or (get_current_student_context(supabase) if supabase else {})
    identity = _identity_from_context(ctx) if ctx else None

    if not supabase:
        st.warning("Supabase is not configured. Add .streamlit/secrets.toml.")
        return

    if not ctx.get("student_id"):
        st.warning("Student profile not found. Contact admin.")
        return

    if not ctx.get("class_id"):
        st.warning("Your class is not assigned yet. Contact admin.")
        return

    if enrolled is None:
        try:
            enrolled, _ = _check_face_enrolled_by_student_id(supabase, str(ctx.get("student_id") or ""))
        except Exception:
            enrolled = False

    subjects = _load_joined_subjects(supabase, str(ctx["student_id"]))

    # Safety filter: use enrolled subjects. Prefer matching institute when the
    # profile is complete, but do not hide a valid enrollment solely because the
    # enrollment row lacks denormalized institute data.
    student_institute_id = str(ctx.get("institute_id") or "").strip()
    if student_institute_id:
        subjects = [
            s
            for s in subjects
            if not str(s.get("institute_id") or s.get("enrollment_institute_id") or "").strip()
            or str(s.get("institute_id") or s.get("enrollment_institute_id") or "").strip() == student_institute_id
        ]


    st.markdown(
        '<div class="faceid-step-label"><span>1</span><div><strong>FaceID status</strong>'
        '<small>Confirm that your face profile is ready.</small></div></div>',
        unsafe_allow_html=True,
    )
    if enrolled:
        st.markdown(
            '<div class="faceid-status faceid-status-ready">'
            '<span class="faceid-status-icon">&#10003;</span>'
            '<div><strong>FaceID enrolled</strong><small>Your identity profile is ready for verification.</small></div>'
            '<span class="faceid-status-badge">Ready</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("FaceID is not enrolled yet. Please enroll FaceID first.")
        if st.button("Enroll FaceID", key="faceid_go_enroll", use_container_width=True):
            st.info("Open the Enroll FaceID tab and save your face before marking attendance.")
        return

    st.markdown(
        '<div class="faceid-step-label"><span>2</span><div><strong>Select subject</strong>'
        '<small>Choose the class where attendance should be recorded.</small></div></div>',
        unsafe_allow_html=True,
    )
    if subjects:
        subject_options = [_subject_option_label(subject) for subject in subjects]
        selected_label = st.selectbox(
            "Select Subject",
            subject_options,
            index=0,
            key="faceid_subject_select",
        )
        selected_subject = subjects[subject_options.index(selected_label)]
    else:
        st.warning("No subjects found for your class.")
        return
    selected_subject_id = (selected_subject or {}).get("subject_id")
    selected_subject_code = str(selected_subject.get("subject_code") or selected_subject.get("code") or "").strip()
    subject_class_id = str(selected_subject.get("class_id") or "").strip()
    subject_institute_id = str(selected_subject.get("institute_id") or "").strip()
    enrollment_class_id = str(selected_subject.get("enrollment_class_id") or "").strip()
    enrollment_institute_id = str(selected_subject.get("enrollment_institute_id") or "").strip()
    ctx_class_id = str(ctx.get("class_id") or "").strip()
    ctx_institute_id = str(ctx.get("institute_id") or "").strip()
    has_enrollment = bool(selected_subject.get("enrollment"))
    if not has_enrollment and subject_class_id and ctx_class_id and subject_class_id != ctx_class_id:
        st.error("This subject is linked to a different class than your student profile. Contact admin.")
        _show_debug(
            "Developer Debug",
            {
                "student_id": ctx.get("student_id"),
                "student_class_id": ctx_class_id,
                "subject_id": selected_subject_id,
                "subject_class_id": subject_class_id,
                "enrollment_class_id": enrollment_class_id,
                "student_institute_id": ctx_institute_id,
                "subject_institute_id": subject_institute_id,
                "enrollment_institute_id": enrollment_institute_id,
                "subject_code": selected_subject_code,
            },
        )
        return
    if not has_enrollment and subject_institute_id and ctx_institute_id and subject_institute_id != ctx_institute_id:
        st.error("Your student profile is not linked to this subject's institute. Ask admin to reassign your student profile.")
        _show_debug(
            "Developer Debug",
            {
                "student_id": ctx.get("student_id"),
                "student_class_id": ctx_class_id,
                "subject_id": selected_subject_id,
                "subject_class_id": subject_class_id,
                "enrollment_class_id": enrollment_class_id,
                "student_institute_id": ctx_institute_id,
                "subject_institute_id": subject_institute_id,
                "enrollment_institute_id": enrollment_institute_id,
                "subject_code": selected_subject_code,
            },
        )
        return
    selected_class_id = selected_subject.get("class_id") or enrollment_class_id or ctx.get("class_id")
    selected_teacher_id = selected_subject.get("teacher_id")
    selected_subject = {**selected_subject, "class_id": selected_class_id}
    st.session_state["selected_subject_id"] = selected_subject_id
    st.session_state["selected_class_id"] = selected_class_id
    st.session_state["selected_teacher_id"] = selected_teacher_id

    st.markdown(
        """
        <style>
          .faceid-page-header {
              padding: 8px 0 22px;
          }
          .faceid-page-kicker {
              color: #6366f1;
              font-size: 12px;
              font-weight: 800;
              letter-spacing: 0.12em;
              margin-bottom: 7px;
          }
          .faceid-page-title {
              color: #111827;
              font-size: clamp(30px, 3vw, 42px);
              font-weight: 800;
              letter-spacing: -0.035em;
              line-height: 1.12;
          }
          .faceid-page-copy {
              color: #64748b;
              font-size: 15px;
              line-height: 1.65;
              margin-top: 9px;
              max-width: 720px;
          }
          .faceid-step-label {
              align-items: center;
              display: flex;
              gap: 12px;
              margin: 20px 0 10px;
          }
          .faceid-step-label > span {
              align-items: center;
              background: #eef2ff;
              border: 1px solid #dfe3ff;
              border-radius: 10px;
              color: #4f46e5;
              display: flex;
              flex: 0 0 34px;
              font-size: 14px;
              font-weight: 800;
              height: 34px;
              justify-content: center;
          }
          .faceid-step-label strong {
              color: #172033;
              display: block;
              font-size: 17px;
              line-height: 1.25;
          }
          .faceid-step-label small {
              color: #7c8799;
              display: block;
              font-size: 12px;
              margin-top: 2px;
          }
          .faceid-status {
              align-items: center;
              border: 1px solid #bbf7d0;
              border-radius: 14px;
              display: flex;
              gap: 12px;
              padding: 14px 16px;
          }
          .faceid-status-ready {
              background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
          }
          .faceid-status-icon {
              align-items: center;
              background: #16a34a;
              border-radius: 999px;
              color: #ffffff;
              display: flex;
              flex: 0 0 28px;
              font-size: 14px;
              font-weight: 800;
              height: 28px;
              justify-content: center;
          }
          .faceid-status strong {
              color: #166534;
              display: block;
              font-size: 14px;
          }
          .faceid-status small {
              color: #4b7b5e;
              display: block;
              font-size: 12px;
              margin-top: 2px;
          }
          .faceid-status-badge {
              background: #dcfce7;
              border: 1px solid #bbf7d0;
              border-radius: 999px;
              color: #15803d;
              font-size: 11px;
              font-weight: 800;
              margin-left: auto;
              padding: 5px 10px;
              text-transform: uppercase;
          }
          .faceid-guide {
              align-items: flex-start;
              background: transparent;
              border: 0;
              border-bottom: 1px solid #edf0f5;
              border-radius: 0;
              box-sizing: border-box !important;
              display: grid;
              gap: 14px;
              grid-template-columns: 50px minmax(0, 1fr);
              margin: 0 0 20px;
              max-width: 100%;
              min-width: 0;
              padding: 0 0 18px;
              width: auto;
          }
          .faceid-guide-icon {
              background: #eef2ff;
              border: 1px solid #d9ddff;
              border-radius: 13px;
              display: flex;
              flex: 0 0 50px;
              height: 50px;
              align-items: center;
              justify-content: center;
          }
          .faceid-guide-icon svg {
              height: 28px;
              width: 28px;
          }
          .faceid-guide-copy {
              min-width: 0;
              padding-top: 2px;
          }
          .faceid-guide-title {
              color: #172033;
              font-size: 15px;
              font-weight: 800;
              line-height: 1.3;
          }
          .faceid-guide-text {
              color: #64748b;
              font-size: 13px;
              margin-top: 3px;
          }
          .faceid-guide-tips {
              display: flex;
              flex-wrap: wrap;
              gap: 7px;
              justify-content: flex-start;
              margin-top: 11px;
              min-width: 0;
          }
          .faceid-guide-tip {
              background: #f8fafc;
              border: 1px solid #e5eaf2;
              border-radius: 999px;
              color: #475569;
              font-size: 11px;
              font-weight: 600;
              padding: 6px 9px;
              white-space: nowrap;
          }
          .st-key-faceid_capture_card {
              background: #ffffff;
              border: 1px solid #e4e8f2 !important;
              border-radius: 20px !important;
              box-sizing: border-box !important;
              box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
              max-width: 100% !important;
              min-width: 0 !important;
              overflow: hidden;
              padding: 22px !important;
              width: 100% !important;
          }
          .st-key-faceid_capture_card > div,
          .st-key-faceid_capture_card [data-testid="stVerticalBlock"],
          .st-key-faceid_capture_card [data-testid="stElementContainer"],
          .st-key-faceid_capture_card .element-container {
              box-sizing: border-box !important;
              max-width: 100% !important;
              min-width: 0 !important;
          }
          .faceid-capture-title {
              color: #172033;
              font-size: 19px;
              font-weight: 800;
              letter-spacing: -0.02em;
              margin-bottom: 4px;
          }
          .faceid-capture-copy {
              color: #7c8799;
              font-size: 12px;
              margin-bottom: 18px;
          }
          div[data-testid="stCameraInput"] {
              background: #0f1115;
              border: 1px solid #dfe3ec;
              border-radius: 16px;
              box-shadow: 0 8px 24px rgba(15, 23, 42, 0.1);
              margin: 8px auto 0;
              max-width: 620px !important;
              overflow: hidden;
              width: 100% !important;
          }
          div[data-testid="stCameraInput"] video {
              aspect-ratio: 16 / 9;
              border-radius: 0 !important;
              display: block;
              height: auto !important;
              max-height: 315px;
              object-fit: cover;
              width: 100%;
          }
          div[data-testid="stCameraInput"] img {
              aspect-ratio: 16 / 9;
              display: block;
              height: auto !important;
              max-height: 315px;
              object-fit: cover;
              width: 100%;
          }
          div[data-testid="stCameraInput"] button,
          button[data-testid="stCameraInputButton"] {
              background: #ffffff !important;
              color: #111827 !important;
              -webkit-text-fill-color: #111827 !important;
              border: 0 !important;
              border-top: 1px solid #e5e7eb !important;
              border-radius: 0 !important;
              font-weight: 700 !important;
              min-height: 50px !important;
              box-shadow: none !important;
          }
          div[data-testid="stCameraInput"] button:hover,
          button[data-testid="stCameraInputButton"]:hover {
              background: #eef2ff !important;
              color: #3730a3 !important;
              border-color: #818cf8 !important;
          }
          div[data-testid="stCameraInput"] button svg,
          div[data-testid="stCameraInput"] button svg *,
          button[data-testid="stCameraInputButton"] svg,
          button[data-testid="stCameraInputButton"] svg * {
              color: #111827 !important;
              fill: #111827 !important;
              stroke: #111827 !important;
          }
          .st-key-faceid_workspace [data-testid="stFileUploaderDropzone"] {
              background: #f8fafc;
              border-color: #cbd5e1;
              border-radius: 14px;
          }
          .st-key-faceid_verify button {
              border: 0;
              box-sizing: border-box !important;
              box-shadow: 0 10px 24px rgba(99, 102, 241, 0.22);
              font-weight: 800;
              margin: 0 !important;
              max-width: 100% !important;
              min-height: 48px;
              width: 100% !important;
          }
          .st-key-faceid_verify,
          .st-key-faceid_verify > div,
          .st-key-faceid_verify [data-testid="stButton"] {
              box-sizing: border-box !important;
              margin-left: 0 !important;
              margin-right: 0 !important;
              max-width: 100% !important;
              min-width: 0 !important;
              width: 100% !important;
          }
          .st-key-faceid_capture_card .faceid-step-label {
              border-top: 1px solid #edf0f5;
              margin-top: 18px;
              padding-top: 16px;
          }
          .st-key-faceid_capture_card [data-testid="stDateInput"] input {
              border-color: #d9deea !important;
              box-shadow: none !important;
          }
          .st-key-faceid_capture_card [data-testid="stDateInput"] input:focus {
              border-color: #818cf8 !important;
              box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
          }
          .st-key-faceid_workspace [data-testid="stHorizontalBlock"] {
              align-items: flex-start;
              max-width: 100%;
              min-width: 0;
          }
          .st-key-faceid_workspace [data-testid="column"] {
              max-width: 100%;
              min-width: 0;
          }
          .st-key-faceid_back {
              margin-top: 12px;
              max-width: 210px;
          }
          .st-key-faceid_back button {
              background: #ffffff !important;
              border: 1px solid #dfe3ec !important;
              box-shadow: 0 5px 16px rgba(15, 23, 42, 0.06) !important;
              font-weight: 700 !important;
              width: 100%;
          }
          @media (max-width: 900px) {
              .st-key-faceid_capture_card {
                  padding: 18px !important;
              }
              div[data-testid="stCameraInput"] video,
              div[data-testid="stCameraInput"] img {
                  max-height: none;
              }
              .faceid-status-badge {
                  display: none;
              }
          }
          @media (max-width: 600px) {
              .faceid-guide {
                  grid-template-columns: 42px minmax(0, 1fr);
                  padding-bottom: 15px;
              }
              .faceid-guide-icon {
                  border-radius: 11px;
                  flex-basis: 42px;
                  height: 42px;
              }
              .faceid-guide-tip {
                  white-space: normal;
              }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="faceid-step-label"><span>3</span><div><strong>Capture and verify</strong>'
        '<small>Use a live camera photo or upload a recent image.</small></div></div>',
        unsafe_allow_html=True,
    )

    with st.container(key="faceid_workspace"):
        side_left, main_col, side_right = st.columns([0.12, 0.76, 0.12])
        with main_col:
            with st.container(border=True, key="faceid_capture_card"):
                st.markdown(
                    """
                    <div class="faceid-guide">
                      <div class="faceid-guide-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="1.7"
                             stroke-linecap="round" stroke-linejoin="round">
                          <circle cx="12" cy="8" r="3"/>
                          <path d="M6 21v-1a6 6 0 0 1 12 0v1"/>
                          <path d="M4 6C4 4.9 4.9 4 6 4M20 6C20 4.9 19.1 4 18 4"/>
                        </svg>
                      </div>
                      <div class="faceid-guide-copy">
                        <div class="faceid-guide-title">Prepare for a clear photo</div>
                        <div class="faceid-guide-text">Center your face and look directly at the camera.</div>
                        <div class="faceid-guide-tips">
                          <span class="faceid-guide-tip">Good lighting</span>
                          <span class="faceid-guide-tip">No mask or dark glasses</span>
                          <span class="faceid-guide-tip">One face only</span>
                        </div>
                      </div>
                    </div>
                    <div class="faceid-capture-title">Capture face photo</div>
                    <div class="faceid-capture-copy">Your image is used only to verify your enrolled FaceID profile.</div>
                    """,
                    unsafe_allow_html=True,
                )

                date_col, method_col = st.columns([1, 1.25], gap="medium")
                with date_col:
                    att_date = st.date_input("Attendance date", value=date.today(), key="faceid_date")
                with method_col:
                    method = st.radio("Photo method", ["Camera", "Upload"], horizontal=True, key="faceid_method")

                img_bytes = None
                if method == "Camera":
                    st.caption("Camera preview")
                    cam = st.camera_input(
                        "Capture face photo",
                        key="faceid_cam",
                        label_visibility="collapsed"
                    )
                    if cam:
                        img_bytes = cam.getvalue()
                else:
                    up = st.file_uploader(
                        "Upload a clear face photo",
                        type=["jpg", "jpeg", "png"],
                        key="faceid_up",
                    )
                    if up:
                        img_bytes = up.getvalue()
                        st.image(up, width=180)

                st.markdown(
                    '<div class="faceid-step-label"><span>4</span><div><strong>Verify and mark</strong>'
                    '<small>The button becomes available after a photo is captured.</small></div></div>',
                    unsafe_allow_html=True,
                )
                missing_ids = not all([
                    ctx.get("student_id"),
                    selected_subject_id,
                    ctx.get("student_email"),
                ])
                if missing_ids:
                    st.warning("Cannot mark attendance because student, subject, or email details are missing.")

                disabled = missing_ids or not img_bytes or not enrolled
                if st.button("Verify & Mark", type="primary", use_container_width=True, key="faceid_verify", disabled=disabled):
                    try:
                        _verify_and_mark(
                            supabase=supabase,
                            ctx=ctx,
                            identity=identity,
                            img_bytes=img_bytes,
                            selected_subject=selected_subject,
                            att_date=str(att_date),
                            ai_ready=ai_ready,
                        )
                    except Exception as exc:
                        st.error("Attendance could not be saved.")
                        _show_faceid_dev_error(
                            exc,
                            {
                                "student_id": ctx.get("student_id"),
                                "class_id": selected_class_id,
                                "subject_id": selected_subject_id,
                                "student_email": ctx.get("student_email"),
                                "subject_code": selected_subject_code,
                            },
                        )


def _build_debug_payload(
    *,
    ctx: dict[str, Any] | None,
    identity: dict[str, Any],
    selected_subject: dict[str, Any] | None,
    face_embedding_found: bool | None = None,
    verification_score: Any = None,
    session_id: str | None = None,
    exception: Exception | str | None = None,
    supabase_response: Any = None,
) -> dict[str, Any]:
    ctx = ctx or {}
    selected_subject = selected_subject or {}
    student = ctx.get("student") if isinstance(ctx.get("student"), dict) else {}
    exc_text = ""
    if exception:
        exc_text = str(exception) if isinstance(exception, str) else f"{exception.__class__.__name__}: {exception}"
    return {
        "auth_user_id": identity.get("auth_user_id") or ctx.get("auth_user_id") or _session_auth_user_id(),
        "student_email": identity.get("user_email") or ctx.get("student_email") or _session_email(),
        "user_profile_found": bool(ctx.get("user_profile_found")),
        "student_id": identity.get("student_id") or ctx.get("student_id"),
        "student_user_id": student.get("user_id") or identity.get("user_id"),
        "institute_id": identity.get("institute_id") or ctx.get("institute_id"),
        "class_id": selected_subject.get("class_id") or ctx.get("class_id"),
        "subject_id": selected_subject.get("subject_id") or selected_subject.get("id"),
        "face_embedding_found": face_embedding_found,
        "verification_score": verification_score,
        "confidence": verification_score,
        "session_id": session_id,
        "exact_exception_message": exc_text,
        "exact_supabase_response": str(supabase_response) if supabase_response is not None else "",
    }


def _render_faceid_save_failure(debug_payload: dict[str, Any], *, rls: bool = False) -> None:
    if _debug_enabled():
        with st.expander("Developer Debug", expanded=False):
            st.code(json.dumps(debug_payload, indent=2, default=str))
    if rls:
        st.error("Attendance could not be saved. Contact admin.")
    else:
        st.error("Attendance could not be saved. Please try again or ask your teacher to mark manual attendance.")


def _verify_and_mark(
    supabase,
    ctx: dict[str, Any] | None,
    identity: dict[str, Any],
    img_bytes: bytes,
    selected_subject: dict[str, Any],
    att_date: str,
    ai_ready: bool,
) -> None:
    """FaceID verify + mark.

    This function must never crash the full app.
    Only the single primary implementation is kept (legacy duplicated code removed).
    """

    face_embedding_found: bool | None = None
    score: float | None = None
    session_id: str | None = None
    save_response: Any = None

    ctx = ctx or {}
    selected_subject = selected_subject or {}

    try:
        student_id = str(identity.get("student_id") or ctx.get("student_id") or "").strip()
        subject_id = str(selected_subject.get("subject_id") or selected_subject.get("id") or "").strip()
        class_id = str(selected_subject.get("class_id") or ctx.get("class_id") or "").strip()
        student_email = str(ctx.get("student_email") or identity.get("user_email") or _session_email()).strip().lower()
        subject_code = str(selected_subject.get("subject_code") or selected_subject.get("code") or "").strip()
        subject_name = str(selected_subject.get("subject_name") or selected_subject.get("name") or "Selected Subject")

        if not student_id:
            st.error("Profile missing. Contact admin.")
            return
        if not class_id:
            st.error("Your class is not assigned yet. Contact admin.")
            return
        if not subject_id:
            st.error("No subject assigned yet. Contact admin.")
            return
        if not student_email:
            st.error("Student email missing. Contact admin.")
            return
        if not subject_code:
            subject_code = str(
                selected_subject.get("subject_name") or "SUBJ"
            ).strip().upper().replace(" ", "")[:8]

        quality = check_image_quality(img_bytes)
        if not quality.get("ok"):
            st.warning(quality.get("message") or "Face enrollment failed.")
            return

        enrolled, enrolled_row = _check_face_enrolled_by_student_id(supabase, student_id)
        face_embedding_found = bool(enrolled)
        if not enrolled:
            st.warning("FaceID is not enrolled yet. Please enroll your face first.")
            return

        if not ai_ready:
            show_faceid_unavailable()
            _show_debug("Developer Debug", deepface_error_message() or "FaceID engine unavailable.")
            return

        with st.spinner("Verifying..."):
            live_embedding, embed_error = generate_face_embedding(img_bytes)

        if embed_error or live_embedding is None:
            st.error("Face could not be verified. Please use a clear front-facing photo and try again.")
            _show_debug("Developer Debug", embed_error or "Face embedding could not be generated.")
            return

        try:
            stored_raw = (enrolled_row or {}).get("embedding")
            stored_embedding = stored_raw if isinstance(stored_raw, list) else json.loads(stored_raw or "[]")
            score = cosine_similarity(live_embedding, stored_embedding)
        except Exception as exc:
            debug_payload = _build_debug_payload(
                ctx=ctx,
                identity=identity,
                selected_subject=selected_subject,
                face_embedding_found=face_embedding_found,
                verification_score=score,
                session_id=session_id,
                exception=exc,
                supabase_response=enrolled_row,
            )
            _render_faceid_save_failure(debug_payload)
            st.error("Face enrollment data could not be verified. Please enroll again.")
            return

        if score is None or score < 0.40:
            st.error("Face did not match your enrolled FaceID. Please try again in better lighting.")
            return

        confidence = round(max(0.0, min(100.0, (score + 1) * 50)), 1)
        is_valid, validated_data = validate_student_subject_match(
            supabase,
            student_email,
            subject_code,
            selected_subject=selected_subject,
        )
        if not is_valid:
            st.error(str(validated_data))
            _show_debug(
                "Developer Debug",
                {
                    "student_id": student_id,
                    "class_id": class_id,
                    "subject_id": subject_id,
                    "student_email": student_email,
                    "subject_code": subject_code,
                    "validation_error": validated_data,
                },
            )
            return

        student_id = str(validated_data["student_id"])
        subject_id = str(validated_data["subject_id"])
        class_id = str(validated_data["class_id"])
        save_response = _mark_faceid_attendance_with_rpc(
            supabase,
            student_email=student_email,
            subject_code=subject_code,
        )
        message = str(save_response.get("message") or "").strip()
        if bool(save_response.get("ok")):
            st.cache_data.clear()
            st.session_state.faceid_step = "confirmed"
            st.session_state.faceid_subject = subject_name
            st.session_state.faceid_confidence = confidence
            st.session_state.faceid_student_name = (
                ctx.get("student_name")
                or identity.get("user_name")
                or identity.get("name")
                or "Student"
            )
            st.session_state.faceid_student_roll = (
                ctx.get("roll_no")
                or identity.get("roll_no")
                or "Not set"
            )
            st.session_state.faceid_rpc_message = message or "FaceID attendance saved successfully."
            st.rerun()
            return

        st.error(message or "Attendance could not be saved. Please try again or ask your teacher to mark manual attendance.")
        _show_debug(
            "Developer Debug",
            {
                "student_id": student_id,
                "class_id": class_id,
                "subject_id": subject_id,
                "student_email": student_email,
                "subject_code": subject_code,
                "verification_score": confidence,
                "rpc_result": save_response,
            },
        )
        return

    except Exception as exc:
        raw = str(exc).lower()
        debug_payload = _build_debug_payload(
            ctx=ctx,
            identity=identity,
            selected_subject=selected_subject,
            face_embedding_found=face_embedding_found,
            verification_score=score,
            session_id=session_id,
            exception=exc,
            supabase_response=save_response,
        )
        _show_faceid_dev_error(
            exc,
            {
                "student_id": ctx.get("student_id") or identity.get("student_id"),
                "class_id": selected_subject.get("class_id") or ctx.get("class_id"),
                "subject_id": selected_subject.get("subject_id") or selected_subject.get("id"),
                "student_email": ctx.get("student_email") or identity.get("user_email") or _session_email(),
                "subject_code": selected_subject.get("subject_code") or selected_subject.get("code"),
            },
        )
        _render_faceid_save_failure(
            debug_payload,
            rls=("row-level security" in raw or "rls" in raw or "42501" in raw),
        )
        return


def _confirmation_screen() -> None:
    subj = st.session_state.get("faceid_subject", "Selected Subject")
    name = st.session_state.get("faceid_student_name") or st.session_state.get("user_name") or "Student"
    roll = st.session_state.get("faceid_student_roll") or st.session_state.get("user_roll") or "Not set"
    conf = st.session_state.get("faceid_confidence", "Demo")
    rpc_message = str(st.session_state.get("faceid_rpc_message") or "Your attendance has been recorded.").strip()
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    st.markdown(
        f"""
        <div class="sc-confirm-card">
          <div class="sc-confirm-icon" aria-label="Attendance successful">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
              stroke="#ffffff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12.5l4.2 4.2L19 7"/>
            </svg>
          </div>
          <h2 style="margin:0 0 8px;color:#10B981;">Attendance Marked!</h2>
          <p style="color:#6B7280;margin:0 0 24px;">{html.escape(rpc_message)}</p>
          <div style="background:#F5F7FF;border-radius:16px;padding:20px;text-align:left;margin-bottom:24px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <span style="color:#6B7280;">Student</span><strong>{html.escape(str(name))}</strong></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <span style="color:#6B7280;">Roll</span><strong>{html.escape(str(roll))}</strong></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <span style="color:#6B7280;">Subject</span><strong>{html.escape(str(subj))}</strong></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <span style="color:#6B7280;">Time</span><strong>{now}</strong></div>
            <div style="display:flex;justify-content:space-between;">
              <span style="color:#6B7280;">Confidence</span>
              <strong>{html.escape(str(conf))}%</strong></div>
          </div>
          <span class="sc-badge ok" style="font-size:.95rem;padding:10px 24px;">Present</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Go to Dashboard", type="primary", use_container_width=True, key="conf_home"):
            for key in [
                "faceid_step",
                "faceid_subject",
                "faceid_confidence",
                "faceid_rpc_message",
                "faceid_student_name",
                "faceid_student_roll",
            ]:
                st.session_state.pop(key, None)
            nav_student("dashboard")
        if st.button("Mark Another Attendance", use_container_width=True, key="conf_again"):
            st.session_state.faceid_step = "scan"
            for key in [
                "faceid_subject",
                "faceid_confidence",
                "faceid_rpc_message",
                "faceid_student_name",
                "faceid_student_roll",
            ]:
                st.session_state.pop(key, None)
            st.rerun()
