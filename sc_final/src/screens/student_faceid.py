"""Student FaceID attendance — enrollment + verification."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import streamlit as st

from src.database.client import get_supabase_client
from src.database.queries import get_subjects
from src.services.attendance_service import save_attendance_records
from src.services.face_ai_service import (
    check_face_enrolled,
    cosine_similarity,
    deepface_error_message,
    generate_face_embedding,
    is_deepface_available,
    save_face_embedding_to_supabase,
)
from src.services.face_service import check_image_quality
from src.services.student_identity import resolve_student_identity
from src.services.subject_service import get_subject_by_name
from src.utils.session import nav_student
from src.utils.user_guards import show_faceid_not_enrolled, show_faceid_unavailable


def show_faceid() -> None:
    st.markdown("### 🪪 FaceID Attendance")

    ai_ready = is_deepface_available()
    if not ai_ready:
        show_faceid_unavailable()
        with st.expander("Developer Debug", expanded=False):
            st.code(deepface_error_message() or "FaceID engine unavailable.")
        return
        err = deepface_error_message() or "DeepFace could not load."
        st.markdown(
            f"""
            <div class="sc-alert warning">
              ⚠️ <strong>Real AI attendance disabled</strong> — {err}
              <div style="margin-top:6px;">Activate Python 3.11 venv and run: <code>pip install deepface tf-keras tensorflow opencv-python-headless</code></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab1, tab2 = st.tabs(["🪪 Mark Attendance", "📸 Enroll My Face"])
    with tab1:
        _mark_tab(ai_ready)
    with tab2:
        _enroll_tab(ai_ready)

    if st.button("← Back to Dashboard", key="faceid_back"):
        st.session_state.pop("faceid_step", None)
        nav_student("dashboard")


def _get_identity(supabase) -> dict[str, Any] | None:
    student_id = resolve_student_identity(supabase, show_error=False)
    if not student_id:
        return None

    return {
        "student_id": student_id,
        "user_id": st.session_state.get("auth_user_id") or st.session_state.get("user_id"),
        "auth_user_id": st.session_state.get("auth_user_id") or st.session_state.get("user_id"),
        "institute_id": st.session_state.get("institute_id")
        or (st.session_state.get("student_profile") or {}).get("institute_id"),
        "user_email": st.session_state.get("student_email") or st.session_state.get("user_email"),
        "user_name": st.session_state.get("student_name") or st.session_state.get("user_name"),
        "roll_no": st.session_state.get("roll_no") or st.session_state.get("user_roll"),
        "name": st.session_state.get("student_name") or st.session_state.get("user_name"),
    }


def _enroll_tab(ai_ready: bool) -> None:
    supabase = get_supabase_client()
    identity = _get_identity(supabase) if supabase else None

    st.markdown("#### 📸 Enroll Your Face")
    st.caption("Enroll once. After enrollment you can mark attendance with FaceID.")

    if not supabase:
        st.warning("Supabase is not configured. Add .streamlit/secrets.toml.")
        return

    if not identity or not identity.get("student_id"):
        st.warning("Please login first.")
        return

    st.caption(f"Student: {identity.get('user_name') or 'Student'} | Roll: {identity.get('roll_no') or '—'}")

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
        "✅ Save My Face",
        type="primary",
        use_container_width=True,
        key="enroll_save",
        disabled=not ai_ready,
    ):
        if not ai_ready:
            show_faceid_unavailable()
            with st.expander("Developer Debug", expanded=False):
                st.code(deepface_error_message() or "FaceID engine unavailable.")
            return

        quality = check_image_quality(img_bytes)
        if not quality.get("ok"):
            st.error(f"Face enrollment failed: {quality.get('message')}")
            return

        with st.spinner("Extracting face embedding..."):
            embedding, error = generate_face_embedding(img_bytes)

        if error or embedding is None:
            st.error("Face enrollment failed. Please use a clear front-facing photo and try again.")
            with st.expander("Developer Debug", expanded=False):
                st.code(error or "Face embedding could not be generated.")
            return

        result = save_face_embedding_to_supabase(
            supabase=supabase,
            student_identity=identity,
            embedding=embedding,
        )

        if isinstance(result, dict) and result.get("error"):
            st.error("Face enrollment failed.")
            with st.expander("Developer Debug", expanded=False):
                st.code(result.get("error"))
            return

        enrolled, row = check_face_enrolled(supabase, identity)
        if not enrolled:
            st.error("Face saved, but verification query failed. Please try again.")
            return

        st.success("Face saved successfully in Supabase.")
        st.caption(f"User ID: {identity.get('user_id') or 'not set'} | Email: {identity.get('user_email') or 'not set'}")
        st.balloons()


def _mark_tab(ai_ready: bool) -> None:
    step = st.session_state.get("faceid_step", "scan")
    if step == "confirmed":
        _confirmation_screen()
        return

    supabase = get_supabase_client()
    identity = _get_identity(supabase) if supabase else None

    if not supabase:
        st.warning("Supabase is not configured. Add .streamlit/secrets.toml.")
        return

    if not identity or not identity.get("student_id"):
        st.warning("Please login first.")
        return

    subjects_df = get_subjects()
    if not subjects_df.empty and "subject" in subjects_df.columns:
        subject_options = subjects_df["subject"].tolist()
    elif not subjects_df.empty and "name" in subjects_df.columns:
        subject_options = subjects_df["name"].tolist()
    else:
        subject_options = ["Mathematics"]

    st.markdown(
        """
        <style>
          .faceid-layout-card {
              background: #ffffff;
              border-radius: 28px;
              padding: 52px 32px;
              text-align: center;
              box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
              border: 1px solid #e5e7eb;
              min-height: 430px;
              display: flex;
              flex-direction: column;
              justify-content: center;
              align-items: center;
          }
          .faceid-icon-circle {
              width: 170px;
              height: 170px;
              border-radius: 50%;
              border: 4px solid #6366f1;
              background: #f1f3ff;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 64px;
              margin-bottom: 34px;
              box-shadow: 0 18px 40px rgba(99, 102, 241, 0.14);
          }
          .faceid-title {
              font-size: 40px;
              font-weight: 900;
              color: #111827;
              margin-bottom: 18px;
              letter-spacing: 0.5px;
          }
          .faceid-subtitle {
              font-size: 18px;
              color: #111827;
          }
          .faceid-right-card {
              background: transparent;
              padding-top: 4px;
          }
          @media (max-width: 900px) {
              .faceid-layout-card {
                  min-height: 320px;
                  padding: 34px 22px;
              }
              .faceid-title {
                  font-size: 30px;
              }
              .faceid-icon-circle {
                  width: 130px;
                  height: 130px;
                  font-size: 48px;
              }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1, 1.25], gap="large")

    with left_col:
        st.markdown(
            """
            <div class="faceid-layout-card">
                <div class="faceid-icon-circle">🪪</div>
                <div class="faceid-title">FaceID Attendance</div>
                <div class="faceid-subtitle">Position your face within the frame</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown('<div class="faceid-right-card">', unsafe_allow_html=True)

        subject_name = st.selectbox("Subject", subject_options, key="faceid_subj")
        att_date = st.date_input("Date", value=date.today(), key="faceid_date")
        method = st.radio("Method", ["📷 Camera", "🖼️ Upload"], horizontal=True, key="faceid_method")

        img_bytes = None
        if method == "📷 Camera":
            cam = st.camera_input("Look at camera", key="faceid_cam")
            if cam:
                img_bytes = cam.getvalue()
        else:
            up = st.file_uploader("Upload face photo", type=["jpg", "jpeg", "png"], key="faceid_up")
            if up:
                img_bytes = up.getvalue()
                st.image(up, width=160)

        if img_bytes and st.button("🤖 Verify & Mark", type="primary", use_container_width=True, key="faceid_verify"):
            _verify_and_mark(supabase, identity, img_bytes, subject_name, str(att_date), ai_ready)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")


def _resolve_subject_and_class(supabase, subject_name: str):
    subject_row = get_subject_by_name(supabase, subject_name)
    if not subject_row:
        return None, None

    subject_id = subject_row.get("id")
    class_id = subject_row.get("class_id")

    if not class_id:
        student_class_id = st.session_state.get("student_class_id")
        if student_class_id:
            class_id = student_class_id

    if not class_id and st.session_state.get("student_class"):
        try:
            class_name = st.session_state.get("student_class")
            class_res = supabase.table("classes").select("id").eq("class_name", class_name).limit(1).execute()
            if class_res.data:
                class_id = class_res.data[0].get("id")
        except Exception:
            class_id = None

    return subject_id, class_id


def _verify_and_mark(
    supabase,
    identity: dict[str, Any],
    img_bytes: bytes,
    subject_name: str,
    att_date: str,
    ai_ready: bool,
) -> None:
    q = check_image_quality(img_bytes)
    if not q["ok"]:
        st.warning(q["message"])
        return

    enrolled, enrolled_row = check_face_enrolled(supabase, identity)
    if not enrolled:
        show_faceid_not_enrolled()
        st.info("Go to FaceID Attendance → Enroll My Face.")
        return

    try:
        verified, _row2 = check_face_enrolled(
            supabase,
            {**identity, "student_id": identity.get("student_id")},
        )
        if not verified:
            st.warning("Face saved but verification query could not confirm the row. Try enrolling again.")
            return
    except Exception:
        pass

    if not ai_ready:
        show_faceid_unavailable()
        with st.expander("Developer Debug", expanded=False):
            st.code(deepface_error_message() or "FaceID engine unavailable.")
        return

    with st.spinner("Verifying..."):
        live_embedding, embed_error = generate_face_embedding(img_bytes)

    if embed_error or live_embedding is None:
        st.error("Face could not be verified. Please use a clear front-facing photo and try again.")
        with st.expander("Developer Debug", expanded=False):
            st.code(embed_error or "Face embedding could not be generated.")
        return

    import json

    try:
        stored_raw = (enrolled_row or {}).get("embedding")
        stored_embedding = stored_raw if isinstance(stored_raw, list) else json.loads(stored_raw or "[]")
        score = cosine_similarity(live_embedding, stored_embedding)
    except Exception:
        st.error("Face enrollment data could not be verified. Please enroll again.")
        return

    if score < 0.40:
        st.error("Face did not match your enrolled FaceID.")
        return

    subject_id, class_id = _resolve_subject_and_class(supabase, subject_name)
    student_id = identity.get("student_id")

    if not all([student_id, class_id, subject_id]):
        st.error("Attendance could not be saved: missing student/class/subject IDs.")
        return

    try:
        session_res = (
            supabase.table("attendance_sessions")
            .insert(
                {
                    "class_id": str(class_id),
                    "subject_id": str(subject_id),
                    "institute_id": identity.get("institute_id"),
                    "attendance_date": att_date,
                    "mode": "faceid",
                    "status": "completed",
                    "created_by": identity.get("user_id") or identity.get("auth_user_id") or student_id,
                }
            )
            .execute()
        )
        session_rows = session_res.data or []
        if not session_rows or not session_rows[0].get("id"):
            raise RuntimeError("attendance_sessions insert returned no id")

        confidence = round(max(0.0, min(100.0, (score + 1) * 50)), 1)

        result = save_attendance_records(
            supabase,
            session_rows[0]["id"],
            [
                {
                    "student_id": str(student_id),
                    "attendance_date": att_date,
                    "status": "present",
                    "verification_method": "faceid",
                    "confidence": confidence,
                }
            ],
            identity.get("user_id") or identity.get("auth_user_id"),
            attendance_date=att_date,
            verification_method="faceid",
            confidence=confidence,
        )
    except Exception as exc:
        result = {"success": False, "error": str(exc)}

    if not result.get("success"):
        st.error("Attendance could not be saved. Please try again or ask your teacher to mark manual attendance.")
        with st.expander("Developer Debug", expanded=False):
            st.code(result.get("error") or result.get("message") or "Unknown save failure")
        return

    st.session_state.faceid_step = "confirmed"
    st.session_state.faceid_subject = subject_name
    st.session_state.faceid_confidence = round(max(0.0, min(100.0, (score + 1) * 50)), 1)
    st.rerun()


def _confirmation_screen() -> None:
    subj = st.session_state.get("faceid_subject", "Mathematics")
    name = st.session_state.get("user_name", "Student")
    roll = st.session_state.get("user_roll", "SC001")
    conf = st.session_state.get("faceid_confidence", "Demo")
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    st.markdown(
        f"""
        <div class="sc-confirm-card">
          <div class="sc-confirm-icon">✅</div>
          <h2 style="margin:0 0 8px;color:#10B981;">Attendance Marked!</h2>
          <p style="color:#6B7280;margin:0 0 24px;">Your attendance has been recorded.</p>
          <div style="background:#F5F7FF;border-radius:16px;padding:20px;text-align:left;margin-bottom:24px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <span style="color:#6B7280;">Student</span><strong>{name}</strong></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <span style="color:#6B7280;">Roll</span><strong>{roll}</strong></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <span style="color:#6B7280;">Subject</span><strong>{subj}</strong></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <span style="color:#6B7280;">Time</span><strong>{now}</strong></div>
            <div style="display:flex;justify-content:space-between;">
              <span style="color:#6B7280;">Confidence</span>
              <strong>{conf}%</strong></div>
          </div>
          <span class="sc-badge ok" style="font-size:.95rem;padding:10px 24px;">✅ Present</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏠 Dashboard", type="primary", use_container_width=True, key="conf_home"):
            for key in ["faceid_step", "faceid_subject", "faceid_confidence"]:
                st.session_state.pop(key, None)
            nav_student("dashboard")
        if st.button("🪪 Mark Another", use_container_width=True, key="conf_again"):
            st.session_state.faceid_step = "scan"
            st.rerun()
