"""Landing page for SnapClass AI."""

import streamlit as st

from src.components.branding import render_brand_lockup
from src.components.navigation import go_to


def render_platform_features() -> None:
    feature_cards = [
        ("blue", "Manual Attendance", "Quick daily attendance with class, subject, and date selection."),
        ("pink", "FaceID Attendance", "Use AI-assisted attendance for faster classroom workflows."),
        ("green", "QR Subject Joining", "Let students join assigned subjects with controlled institute flows."),
        ("cyan", "Reports", "Export attendance records and review class-level summaries."),
        ("purple", "Analytics", "Track trends, low attendance, and institute-level performance."),
        ("yellow", "Parent Alerts", "Notify guardians and keep communication clear."),
    ]

    cards_html = "".join(
        f"""
        <div class="platform-feature-card">
          <div class="platform-feature-icon {color}">{index}</div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
        """
        for index, (color, title, description) in enumerate(feature_cards, start=1)
    )

    st.markdown(
        f"""
        <section class="platform-features-section" id="features">
          <div class="platform-features-header">
            <h2>Features</h2>
            <p>Everything your institute needs to manage attendance cleanly.</p>
          </div>
          <div class="platform-features-grid">{cards_html}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _inject_landing_css() -> None:
    st.markdown(
        """
        <style>
        .main .block-container {
          max-width: 1240px !important;
          padding: 18px 24px 72px !important;
        }

        .sc-landing-shell {
          position: relative;
          background: #f5f7fb;
        }

        .st-key-landing_nav {
          max-width: 1180px;
          margin: 4px auto 30px;
          padding: 10px 16px;
          background: rgba(255, 255, 255, 0.96);
          border: 1px solid rgba(226, 232, 240, 0.95);
          border-radius: 20px;
          box-shadow: 0 12px 32px rgba(15, 23, 42, 0.07);
          backdrop-filter: blur(14px);
        }

        .st-key-landing_nav [data-testid="stHorizontalBlock"] {
          align-items: center;
        }

        .st-key-landing_nav .snapclass-brand-lockup {
          min-height: 48px;
        }

        .st-key-landing_nav .stButton > button {
          min-height: 40px !important;
          border-radius: 999px !important;
          border: 1px solid transparent !important;
          box-shadow: none !important;
          background: transparent !important;
          color: #475569 !important;
          font-size: 0.86rem !important;
          font-weight: 650 !important;
          white-space: nowrap !important;
          padding: 8px 14px !important;
        }

        .st-key-landing_nav .stButton > button:hover {
          background: #F5F3FF !important;
          border-color: #EDE9FE !important;
          color: #6D4AFF !important;
          transform: none !important;
        }

        .sc-hero {
          text-align: center;
          padding: 14px 0 18px;
        }

        .sc-title {
          margin: 0 0 18px;
          font-size: clamp(40px, 6vw, 72px);
          font-weight: 900;
          line-height: 1.05;
          letter-spacing: 0;
          background: linear-gradient(135deg, #5B6CFF, #FF4FA3);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .sc-subtitle {
          max-width: 760px;
          margin: 0 auto;
          color: #6B7280;
          font-size: 18px;
          line-height: 1.6;
        }

        .sc-trust-line {
          margin-top: 18px;
          color: #4B5563;
          font-size: 14px;
          font-weight: 700;
        }

        .st-key-landing_ctas {
          max-width: 390px;
          margin: 0 auto 22px;
        }

        div[data-testid="stButton"] > button {
          border-radius: 14px !important;
          min-height: 50px !important;
          font-weight: 700 !important;
          width: 100% !important;
          white-space: nowrap !important;
        }

        .sc-section-title {
          text-align: center;
          font-size: 34px;
          font-weight: 850;
          color: #1F2937;
          margin: 0 0 8px;
        }

        .sc-section-subtitle {
          text-align: center;
          color: #6B7280;
          font-size: 16px;
          margin-bottom: 28px;
        }

        .portal-section {
          margin-top: 8px;
          margin-bottom: 44px;
        }

        .sc-portal-card {
          min-height: 272px;
          height: 100%;
          display: flex;
          flex-direction: column;
          justify-content: center;
          text-align: center;
          margin-bottom: 0;
          padding: 32px 22px 26px;
          background: #ffffff;
          border: 1px solid #E5E7EB;
          border-radius: 18px;
          box-shadow: 0 12px 32px rgba(31, 41, 55, 0.07);
        }

        .sc-portal-icon {
          width: 66px;
          height: 66px;
          border-radius: 18px;
          margin: 0 auto 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ffffff;
          font-size: 28px;
          font-weight: 900;
          box-shadow: 0 10px 24px rgba(91, 108, 255, 0.16);
        }

        .sc-portal-title {
          font-size: 21px;
          font-weight: 850;
          color: #1F2937;
          margin-bottom: 10px;
        }

        .sc-portal-desc {
          color: #6B7280;
          font-size: 14px;
          line-height: 1.55;
          min-height: 64px;
        }

        .platform-features-section {
          max-width: 1180px;
          margin: 0 auto;
          padding: 22px 0 34px;
        }

        .platform-features-header {
          text-align: center;
          margin-bottom: 28px;
        }

        .platform-features-header h2 {
          margin: 0 0 8px;
          color: #1F2937;
          font-size: 34px;
          font-weight: 850;
        }

        .platform-features-header p {
          margin: 0;
          color: #6B7280;
        }

        .platform-features-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 22px;
        }

        .platform-feature-card {
          background: #ffffff;
          border: 1px solid #E5E7EB;
          border-radius: 18px;
          padding: 26px;
          box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        }

        .platform-feature-card h3 {
          margin: 0 0 8px;
          color: #1F2937;
          font-size: 19px;
        }

        .platform-feature-card p {
          margin: 0;
          color: #6B7280;
          line-height: 1.55;
          font-size: 14px;
        }

        .platform-feature-icon {
          width: 42px;
          height: 42px;
          border-radius: 13px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ffffff;
          font-weight: 900;
          margin-bottom: 14px;
        }

        .platform-feature-icon.blue { background: #5B6CFF; }
        .platform-feature-icon.pink { background: #FF4FA3; }
        .platform-feature-icon.green { background: #10B981; }
        .platform-feature-icon.cyan { background: #06B6D4; }
        .platform-feature-icon.purple { background: #8B5CF6; }
        .platform-feature-icon.yellow { background: #F59E0B; }

        .sc-footer {
          text-align: center;
          padding: 36px 0 20px;
          color: #9CA3AF;
          font-size: 0.9rem;
        }

        @media (max-width: 960px) {
          .platform-features-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 760px) {
          .main .block-container {
            padding: 14px 14px 56px !important;
          }

          .st-key-landing_nav {
            padding: 10px 12px;
            margin-bottom: 22px;
          }

          .st-key-landing_nav .snapclass-brand-name {
            font-size: 1rem;
          }

          .st-key-landing_nav .snapclass-brand-icon {
            width: 38px;
            height: 38px;
          }

          .sc-hero {
            padding-top: 14px;
          }

          .sc-title {
            font-size: clamp(34px, 10vw, 46px);
          }

          .sc-subtitle {
            font-size: 16px;
          }

          .portal-section {
            margin-top: 14px;
            margin-bottom: 42px;
          }

          .sc-section-title,
          .platform-features-header h2 {
            font-size: 28px;
          }

          .platform-features-grid {
            grid-template-columns: 1fr;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_navbar() -> None:
    with st.container(key="landing_nav"):
        nav = st.columns([1.35, 0.7, 0.7, 0.7, 0.7], gap="small")

        with nav[0]:
            render_brand_lockup()
        with nav[1]:
            if st.button("About", key="nav_about", use_container_width=True):
                go_to("about")
        with nav[2]:
            if st.button("Features", key="nav_features", use_container_width=True):
                go_to("features")
        with nav[3]:
            if st.button("Pricing", key="nav_pricing", use_container_width=True):
                go_to("pricing")
        with nav[4]:
            if st.button("Contact", key="nav_contact", use_container_width=True):
                go_to("contact")


def _render_hero() -> None:
    st.markdown(
        """
        <section class="sc-hero" id="about">
          <div class="sc-title">AI Attendance for<br>Schools &amp; Coaching Institutes</div>
          <div class="sc-subtitle">
            Manage students, teachers, subjects, attendance, reports, analytics, and parent alerts
            with one intelligent platform.
          </div>
          <div class="sc-trust-line">Built for schools, coaching institutes, and tuition centres</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="landing_ctas"):
        c1, c2 = st.columns([1, 1], gap="small")
        with c1:
            if st.button("View Plans", key="landing_pricing", use_container_width=True, type="primary"):
                go_to("pricing")
        with c2:
            if st.button("Choose Portal", key="landing_choose_portal", use_container_width=True):
                st.session_state["landing_focus_portals"] = True
                st.rerun()


def _render_portals() -> None:
    st.markdown('<section class="portal-section" id="portals">', unsafe_allow_html=True)
    st.markdown('<div class="sc-section-title">Choose Your Portal</div>', unsafe_allow_html=True)
    if st.session_state.get("landing_focus_portals"):
        st.success("Choose the portal that matches your role.")
        st.session_state["landing_focus_portals"] = False
    st.markdown(
        '<div class="sc-section-subtitle">Pick the experience that matches your role</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="large")
    portals = [
        (
            c1,
            "🏛️",
            "Founder Portal",
            "Manage SnapClass operations, institutes, plans, and access codes.",
            "linear-gradient(135deg,#6366f1,#8b5cf6)",
            "founder_auth",
            "Founder Login",
        ),
        (
            c2,
            "🛡️",
            "Admin Portal",
            "Manage teachers, students, classes, subjects, attendance, and reports.",
            "linear-gradient(135deg,#6366f1,#8b5cf6)",
            "institute_login",
            "Admin Login",
        ),
        (
            c3,
            "🎓",
            "Teacher Portal",
            "Mark attendance with AI, manage classes, and review student records.",
            "linear-gradient(135deg,#8b5cf6,#ec4899)",
            "teacher_auth",
            "Teacher Login",
        ),
        (
            c4,
            "📖",
            "Student Portal",
            "Register or login to view attendance, subjects, and reports.",
            "linear-gradient(135deg,#8b5cf6,#ec4899)",
            "student_auth",
            "Student Login",
        ),
    ]

    for col, icon, title, desc, grad, dest, btn_label in portals:
        with col:
            st.markdown(
                f"""
                <div class="sc-portal-card">
                  <div class="sc-portal-icon" style="background:{grad};font-size:32px;">{icon}</div>
                  <div class="sc-portal-title">{title}</div>
                  <div class="sc-portal-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(btn_label, key=f"portal_{dest}", use_container_width=True, type="primary"):
                go_to(dest)

    st.markdown("</section>", unsafe_allow_html=True)


def show_landing() -> None:
    _inject_landing_css()
    st.markdown('<div class="sc-landing-shell">', unsafe_allow_html=True)
    _render_navbar()
    _render_hero()
    _render_portals()
    render_platform_features()

    st.markdown(
        """
        <div class="sc-footer" id="contact">
          <strong style="color:#5B6CFF;">SnapClass AI</strong> -
          Built for schools, coaching institutes, teachers, and students.<br>
          Python &middot; Streamlit &middot; Supabase
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


render_landing = show_landing
landing_page = show_landing
