"""Student FaceID attendance — enrollment + verification."""
from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

from src.database.queries import get_subjects, save_attendance
from src.services.face_ai_service import (
    check_face_enrolled,
    generate_face_embedding,
    get_current_student_identity,
    identify_matching_face,
    is_deepface_available,
    save_face_embedding_to_supabase,
)

from src.services.face_service import check_image_quality
from src.utils.session import nav_student


def show_faceid() -> None:
    st.markdown("### 🪪 FaceID Attendance")
    ai_ready = is_deepface_available()
    if not ai_ready:
        from src.services.face_ai_service import deepface_error_message

        err = deepface_error_message() or "DeepFace could not load."

        st.markdown(
            f"""
        <div class="sc-alert warning">
          ⚠️ <strong>Real AI attendance disabled</strong> — {err}
          <div style="margin-top:6px;">Activate Python 3.11 venv and run: <code>pip install deepface tf-keras tensorflow opencv-python-headless</code></div>
        </div>""",
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


def _enroll_tab(ai_ready: bool) -> None:
    roll = st.session_state.get("user_roll", "SC001")
    name = st.session_state.get("user_name", "Student")
    user_id = st.session_state.get("user_id")
    user_email = st.session_state.get("user_email")

    st.markdown(f"#### 📸 Enroll Your Face — {name} ({roll})")
    st.caption("Enroll once. After enrollment you can mark attendance with FaceID.")

    col1, col2 = st.columns(2)
    with col1:
        cam = st.camera_input("Take selfie", key="enroll_cam")
    with col2:
        up = st.file_uploader("Or upload photo", type=["jpg", "jpeg", "png"], key="enroll_up")

    img = cam if cam else up
    img_bytes = img.getvalue() if img else None

    if not img_bytes:
        return

    button_disabled = not ai_ready
    if st.button(
        "✅ Save My Face",
        type="primary",
        use_container_width=True,
        key="enroll_save",
        disabled=button_disabled,
    ):
        if not ai_ready:
            from src.services.face_ai_service import deepface_error_message

            err = deepface_error_message() or "DeepFace could not load."
            st.error("Face enrollment failed: DeepFace could not load.")
            st.code(err)
            return

        quality = check_image_quality(img_bytes)
        if not quality.get("ok"):
            st.error(f"Face enrollment failed: {quality.get('message')}")
            st.stop()

        with st.spinner("Extracting face embedding…"):
            embedding, error = generate_face_embedding(img_bytes)

        if error or embedding is None:
            st.error(f"Face enrollment failed: {error or 'Face embedding could not be generated.'}")
            st.stop()

        # Resolve identity via the shared resolver.
        from src.services.student_identity import resolve_student_identity

        db = __import__("src.database.client", fromlist=["get_supabase"]).get_supabase()
        if db is None:
            st.error("Face enrollment failed: Supabase client unavailable.")
            st.stop()

        resolved_student_id = resolve_student_identity(db)
        if not resolved_student_id:
            st.error("Face enrollment failed: student identity could not be resolved.")
            st.stop()

        student_identity = {
            "student_id": st.session_state.get("student_id"),
            "user_email": st.session_state.get("student_email") or st.session_state.get("user_email"),
            "roll_no": st.session_state.get("roll_no") or st.session_state.get("user_roll"),
            "user_name": st.session_state.get("student_name") or st.session_state.get("user_name"),
            "name": st.session_state.get("student_name") or st.session_state.get("user_name"),
        }

        result = save_face_embedding_to_supabase(
            supabase=db,
            student_identity=student_identity,
            embedding=embedding,
        )


        if isinstance(result, dict) and result.get("error"):
            st.error("Face enrollment failed.")
            st.code(result.get("error"))
            st.stop()

        st.success("Face saved successfully in Supabase.")
        st.json(result)
        st.caption(
            f"User ID: {user_id or 'not set'} | Email: {user_email or 'not set'}"
        )
        st.balloons()



def _mark_tab(ai_ready: bool) -> None:
    step = st.session_state.get("faceid_step", "scan")
    if step == "confirmed":
        _confirmation_screen()
        return

    roll = st.session_state.get("user_roll", "SC001")
    subjects = get_subjects()
    subj_list = subjects["subject"].tolist() if not subjects.empty else ["Mathematics"]

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

        subj = st.selectbox("Subject", subj_list, key="faceid_subj")
        att_date = st.date_input("Date", value=date.today(), key="faceid_date")
        method = st.radio(
            "Method",
            ["📷 Camera", "🖼️ Upload"],
            horizontal=True,
            key="faceid_method",
        )
        img_bytes = None

        if method == "📷 Camera":
            cam = st.camera_input("Look at camera", key="faceid_cam")
            if cam:
                img_bytes = cam.getvalue()
        else:
            up = st.file_uploader(
                "Upload face photo",
                type=["jpg", "jpeg", "png"],
                key="faceid_up",
            )
            if up:
                img_bytes = up.getvalue()
                st.image(up, width=160)

        if img_bytes:
            if st.button(
                "🤖 Verify & Mark",
                type="primary",
                use_container_width=True,
                key="faceid_verify",
            ):
                _verify_and_mark(img_bytes, roll, subj, str(att_date), ai_ready)

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        # Demo simulate scan intentionally removed for real DeepFace-based attendance.



def _verify_and_mark(img_bytes: bytes, roll: str, subj: str, att_date: str, ai_ready: bool) -> None:
    q = check_image_quality(img_bytes)
    if not q["ok"]:
        st.warning(q["message"])
        return

    # Resolve identity via the shared resolver.
    from src.services.student_identity import resolve_student_identity
    from src.services.face_ai_service import _get_supabase

    supabase = _get_supabase()
    resolved_student_id = resolve_student_identity(supabase)
    if not resolved_student_id:
        st.warning("Student identity missing. Please login again.")
        st.stop()

    student_identity = {
        "student_id": st.session_state.get("student_id"),
        "user_email": st.session_state.get("student_email") or st.session_state.get("user_email"),
        "roll_no": st.session_state.get("roll_no") or st.session_state.get("user_roll"),
        "user_name": st.session_state.get("student_name") or st.session_state.get("user_name"),
        "name": st.session_state.get("student_name") or st.session_state.get("user_name"),
    }

    enrolled, _row = check_face_enrolled(supabase, student_identity)


    if not enrolled:
        st.warning("Face not enrolled yet. Please enroll your face first.")
        st.info("Go to FaceID Attendance → Enroll My Face.")
        st.stop()


    if not ai_ready:
        st.error(
            "Real AI attendance requires DeepFace. Activate Python 3.11 venv and run: pip install deepface tf-keras tensorflow opencv-python-headless"
        )
        return

    with st.spinner("Verifying…"):
        match = identify_matching_face(img_bytes, threshold=0.40)

    if match.get("match"):
        st.success(f"✅ Verified! Confidence: {match.get('confidence', 0):.1f}%")
        _mark_present(roll, subj, att_date, match.get("confidence", 0))
    else:
        st.error("❌ No enrolled student matched")


def _mark_present(roll: str, subj: str, att_date: str, confidence: Any = "Demo") -> None:
    save_attendance([{"roll": roll, "subject": subj, "date": att_date, "status": "present", "marked_by": "faceid"}])
    st.session_state.faceid_step = "confirmed"
    st.session_state.faceid_subject = subj
    st.session_state.faceid_confidence = confidence
    st.rerun()


def _confirmation_screen() -> None:
    from datetime import datetime

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
    </div>""",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏠 Dashboard", type="primary", use_container_width=True, key="conf_home"):
            for k in ["faceid_step", "faceid_subject", "faceid_confidence"]:
                st.session_state.pop(k, None)
            nav_student("dashboard")
        if st.button("🪪 Mark Another", use_container_width=True, key="conf_again"):
            st.session_state.faceid_step = "scan"
            st.rerun()
