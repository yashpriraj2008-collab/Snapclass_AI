"""Landing page â€” 4 portal cards + Platform Features section."""

import streamlit as st
from src.components.navigation import go_to



def render_platform_features():
    feature_cards = [
        ("blue", "&#129302;", "AI Attendance", "Upload class photos - AI detects and marks student attendance automatically."),
        ("pink", "&#128221;", "Manual Attendance", "Quick manual marking with class, subject, and date selection using editable tables."),
        ("green", "&#127891;", "Student Portal", "Students can track attendance, view subjects, check history, and access reports."),
        ("yellow", "&#128104;&#8205;&#127979;", "Teacher Dashboard", "Teachers can manage assigned classes, mark attendance, and view class analytics."),
        ("cyan", "&#128202;", "Analytics & Reports", "Deep attendance insights with charts, trends, CSV export, and report summaries."),
        ("purple", "&#127979;", "Institute Management", "Founders and admins manage institutes, access codes, users, plans, and operations."),
    ]
    stats = [
        ("500+", "Students Enrolled"),
        ("50+", "Teachers"),
        ("10+", "Institutes"),
        ("99%", "Uptime"),
    ]

    cards_html = "".join(
        f'<div class="platform-feature-card"><div class="platform-feature-icon {color}">{icon}</div>'
        f"<h3>{title}</h3><p>{description}</p></div>"
        for color, icon, title, description in feature_cards
    )
    stats_html = "".join(
        f'<div class="platform-stat"><h3>{value}</h3><p>{label}</p></div>'
        for value, label in stats
    )
    html = (
        '<section class="platform-features-section">'
        '<div class="platform-features-header"><h2>Platform Features</h2>'
        "<p>Everything your institute needs, one platform</p></div>"
        f'<div class="platform-features-grid">{cards_html}</div>'
        "</section>"
        f'<section class="platform-stats-strip">{stats_html}</section>'
    )
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def show_landing():
    st.markdown("""
    <style>
    .main .block-container{
      padding:32px 24px 72px !important;
      max-width:1240px !important;
    }

    /* Landing wrapper class to keep the page background stable */
    .sc-landing-fix{
      position: relative;
      background: #f5f7fb;
    }

    .sc-hero{
      text-align:center;
      padding:42px 0 56px;
    }

    .sc-title{
      font-size:clamp(40px,6vw,72px);
      font-weight:900;
      line-height:1.05;
      letter-spacing:-2px;
      background:linear-gradient(135deg,#5B6CFF,#FF4FA3);
      -webkit-background-clip:text;
      -webkit-text-fill-color:transparent;
      margin-bottom:20px;
    }

    .sc-subtitle{
      max-width:720px;
      margin:0 auto;
      color:#6B7280;
      font-size:18px;
      line-height:1.6;
    }

    .sc-section-title{
      text-align:center;
      font-size:36px;
      font-weight:850;
      color:#1F2937;
      margin:0 0 8px;
    }

    .sc-section-subtitle{
      text-align:center;
      color:#6B7280;
      font-size:16px;
      margin-bottom:28px;
    }

    .portal-section{
      margin-top:36px;
      margin-bottom:80px;
    }

    .sc-brand-box{
      display:inline-flex;
      width:fit-content;
      max-width:100%;
    }

    .sc-portal-card{
      background:white;
      border:1px solid #E5E7EB;
      border-radius:24px;
      padding:34px 24px 28px;
      text-align:center;
      box-shadow:0 12px 32px rgba(31,41,55,.07);
      margin-bottom:0;
      min-height:280px;
      display:flex;
      flex-direction:column;
      justify-content:center;
      height:100%;
    }

    .sc-portal-icon{
      width:68px;
      height:68px;
      border-radius:20px;
      margin:0 auto 18px;
      display:flex;
      align-items:center;
      justify-content:center;
      font-size:30px;
      box-shadow:0 10px 24px rgba(91,108,255,.16);
      flex-shrink:0;
    }

    .sc-portal-title{
      font-size:22px;
      font-weight:850;
      color:#1F2937;
      margin-bottom:10px;
    }

    .sc-portal-desc{
      color:#6B7280;
      font-size:14px;
      line-height:1.55;
      min-height:64px;
    }

    .portal-button-spacer{
      height:16px;
    }

    div[data-testid="stButton"] > button{
      border-radius:14px !important;
      min-height:52px !important;
      font-weight:700 !important;
      width:100% !important;
    }

    /* Keep top navigation labels on a single line */
    .stButton > button{
      white-space: nowrap !important;
      overflow: hidden !important;
      text-overflow: clip !important;
      padding: 0.45rem 0.6rem !important;
      font-size: 0.78rem !important;
      line-height: 1.1 !important;
      min-width: 0 !important;
    }

    .main .block-container .stColumns [data-testid="column"] .stButton > button{
      min-height: 44px !important;
    }

    /* Give the nav buttons more horizontal room */
    .main .block-container .stColumns:first-of-type{
      gap: 0.6rem !important;
    }

    .features-section{
      max-width:1500px;
      margin:0 auto;
      padding:40px 48px 32px;
    }

    .features-grid{
      display:grid;
      grid-template-columns:repeat(3,1fr);
      gap:28px 32px;
      margin-top:36px;
    }

    .sc-feat-card{
      background:#ffffff;
      border-radius:24px;
      padding:34px 36px;
      min-height:220px;
      height:auto;
      display:flex;
      flex-direction:column;
      justify-content:flex-start;
      box-shadow:0 10px 30px rgba(15, 23, 42, 0.06);
      border:1px solid rgba(15, 23, 42, 0.06);
    }

    .sc-feat-icon{
      width:52px;
      height:52px;
      border-radius:15px;
      display:flex;
      align-items:center;
      justify-content:center;
      font-size:24px;
      margin-bottom:14px;
      box-shadow:0 4px 12px rgba(0,0,0,.1);
    }

    .stats-card{
      margin:36px auto 80px;
      padding:34px 48px;
      border-radius:24px;
    }

    .sc-footer{
      text-align:center;
      padding:36px 0 20px;
      color:#9CA3AF;
      font-size:.9rem;
    }

    @media (max-width: 1024px){
      .main .block-container{
        padding:28px 20px 64px !important;
      }

      .sc-hero{
        padding:36px 0 46px;
      }

      .sc-title{
        font-size:clamp(38px,7vw,64px);
      }

      .sc-portal-card,
      .sc-feat-card{
        padding:30px 22px;
      }

      .features-section{
        padding-bottom:84px;
      }

      .features-grid{
        grid-template-columns: repeat(2,1fr);
        gap:24px;
      }

      .sc-feat-card{
        min-height:auto;
        padding:30px 22px;
      }
    }

    @media (max-width: 768px){
      .features-section{
        padding:28px 18px;
      }

      .features-grid{
        grid-template-columns:1fr;
        gap:20px;
      }

      .sc-feat-card{
        padding:28px 26px;
        min-height:auto;
      }

      .stats-card{
        margin:28px 18px 96px;
        padding:28px 22px;
      }

      .snapbot-widget,
      .snapbot-toggle-wrapper{
        right:18px;
        bottom:18px;
      }
    }

    @media (max-width: 640px){
      .main .block-container{
        padding:20px 14px 56px !important;
      }

      .sc-hero{
        padding:28px 0 40px;
      }

      .snapbot-widget,
      .snapbot-toggle-wrapper{
        right:16px;
        bottom:16px;
      }

      .sc-section-title{
        font-size:28px;
      }

      .sc-section-subtitle{
        font-size:14px;
        margin-bottom:22px;
      }

      .portal-section{
        margin-top:28px;
        margin-bottom:60px;
      }

      .features-section{
        margin-top:56px;
        padding-bottom:76px;
      }

      .sc-portal-card,
      .sc-feat-card{
        min-height:auto;
        padding:24px 18px;
      }

      .sc-portal-desc{
        min-height:auto;
      }

      .stats-card{
        padding:28px 20px;
      }
    }
    </style>""", unsafe_allow_html=True)

    st.markdown('<div class="sc-landing-fix">', unsafe_allow_html=True)

    # â”€â”€ Navbar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    nav = st.columns([2.5, 1, 1, 1, 1], gap="small")
    with nav[0]:
        st.markdown(
            """
            <div class="sc-brand-box">
              <div style="display:flex;align-items:center;gap:14px;background:white;
                border:1px solid #E5E7EB;border-radius:24px;padding:16px 22px;
                box-shadow:0 10px 30px rgba(31,41,55,.07);">
                <div style="width:46px;height:46px;border-radius:14px;
                  background:linear-gradient(135deg,#5B6CFF,#FF4FA3);color:white;
                  display:flex;align-items:center;justify-content:center;
                  font-size:20px;font-weight:900;">S</div>
                <div>
                  <div style="font-size:22px;font-weight:850;color:#1F2937;">SnapClass AI</div>
                  <div style="font-size:12px;color:#6B7280;font-weight:600;">AI Attendance Platform</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nav[1]:
        if st.button("About", use_container_width=True, key="nav_about"):
            go_to("about")
    with nav[2]:
        if st.button("Features", use_container_width=True, key="nav_features"):
            go_to("features")
    with nav[3]:
        if st.button("Pricing", use_container_width=True, key="nav_pricing"):
            go_to("pricing")
    with nav[4]:
        if st.button("Contact", use_container_width=True, key="nav_contact"):
            go_to("contact")

    # â”€â”€ Hero â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        """
        <div class="sc-hero">
          <div class="sc-title">AI Attendance for<br>Modern Education</div>
          <div class="sc-subtitle">
            Manage schools, coaching institutes, teachers, students and attendance
            with one intelligent platform.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # â”€â”€ Portal Cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown('<div class="portal-section">', unsafe_allow_html=True)
    st.markdown('<div class="sc-section-title">Choose Your Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sc-section-subtitle">Pick the experience that matches your role</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap="large")
    portals = [
        (c1, "&#127891;", "Student Portal", "View attendance, subjects, and track your academic progress.", "linear-gradient(135deg,#5B6CFF,#6C7BFF)", "student_auth", "Enter Student Portal"),
        (c2, "&#128104;&#8205;&#127979;", "Teacher Portal", "Mark attendance with AI, manage classes and student records.", "linear-gradient(135deg,#FF4FA3,#EC4899)", "teacher_auth", "Enter Teacher Portal"),
        (c3, "&#127979;", "Institute Admin", "Manage your institute, teachers, students, classes and attendance.", "linear-gradient(135deg,#10B981,#22C55E)", "institute_login", "Enter Institute Admin"),
        (c4, "&#127970;", "SnapClass HQ", "Founder control center to manage institutes and access codes.", "linear-gradient(135deg,#06B6D4,#3B82F6)", "founder_auth", "Enter SnapClass HQ"),
    ]

    for col, icon, title, desc, grad, dest, btn_label in portals:
        with col:
            st.markdown(
                f"""
                <div class="sc-portal-card">
                  <div class="sc-portal-icon" style="background:{grad};">{icon}</div>
                  <div class="sc-portal-title">{title}</div>
                  <div class="sc-portal-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(btn_label, key=f"portal_{dest}", use_container_width=True, type="primary"):
                go_to(dest)

    st.markdown("<br>", unsafe_allow_html=True)

    render_platform_features()

    # â”€â”€ Footer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(
        """
        <div class="sc-footer">
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
