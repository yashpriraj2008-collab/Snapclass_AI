"""About page - separate from landing."""

from textwrap import dedent

import streamlit as st  # type: ignore[import]

from src.components.navigation import go_to
from src.components.public_nav import render_public_nav


def render_about_section() -> None:
    """Render the About page HTML as UI, bypassing Markdown code-block parsing."""
    about_html = dedent(
        """
        <style>
        .about-section {
            max-width: 1180px;
            margin: 70px auto 40px auto;
            padding: 0 24px;
        }

        .about-title {
            text-align: center;
            font-size: 44px;
            font-weight: 800;
            margin-bottom: 14px;
            background: linear-gradient(90deg, #6366f1, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .about-subtitle {
            text-align: center;
            max-width: 780px;
            margin: 0 auto 42px auto;
            font-size: 18px;
            line-height: 1.7;
            color: #4b5563;
        }

        .about-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 28px;
            margin-bottom: 34px;
        }

        .about-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 24px;
            padding: 34px;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
        }

        .about-card h3 {
            font-size: 26px;
            font-weight: 800;
            color: #111827;
            margin-bottom: 22px;
        }

        .about-list {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .about-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            color: #374151;
            font-size: 16px;
            line-height: 1.55;
        }

        .about-icon {
            width: 24px;
            height: 24px;
            min-width: 24px;
            border-radius: 999px;
            background: #dcfce7;
            color: #16a34a;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 14px;
        }

        .role-block {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 14px;
            color: #374151;
            font-size: 16px;
            line-height: 1.6;
        }

        .role-block strong {
            color: #111827;
        }

        .steps-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 18px;
            margin-top: 30px;
        }

        .step-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 22px;
            padding: 24px;
            box-shadow: 0 14px 35px rgba(15, 23, 42, 0.07);
        }

        .step-number {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            background: linear-gradient(135deg, #6366f1, #ec4899);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            margin-bottom: 16px;
        }

        .step-card h4 {
            font-size: 18px;
            font-weight: 800;
            color: #111827;
            margin-bottom: 8px;
        }

        .step-card p {
            font-size: 15px;
            color: #6b7280;
            line-height: 1.55;
            margin: 0;
        }

        .about-cta {
            text-align: center;
            margin-top: 42px;
        }

        .about-cta a {
            display: inline-block;
            padding: 15px 32px;
            border-radius: 16px;
            background: linear-gradient(90deg, #6366f1, #ec4899);
            color: #ffffff !important;
            text-decoration: none;
            font-weight: 700;
            box-shadow: 0 16px 35px rgba(99, 102, 241, 0.25);
        }

        @media (max-width: 900px) {
            .about-grid {
                grid-template-columns: 1fr;
            }

            .steps-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .about-title {
                font-size: 34px;
            }
        }

        @media (max-width: 600px) {
            .steps-grid {
                grid-template-columns: 1fr;
            }

            .about-card {
                padding: 24px;
            }

            .about-title {
                font-size: 30px;
            }
        }
        </style>

        <section class="about-section" id="about">
            <h2 class="about-title">Attendance that just works.</h2>

            <p class="about-subtitle">
                SnapClass AI helps schools, coaching institutes, and tuition centres manage attendance,
                students, teachers, classes, reports, and analytics from one simple system.
            </p>

            <div class="about-grid">
                <div class="about-card">
                    <h3>Why SnapClass AI?</h3>
                    <div class="about-list">
                        <div class="about-item"><div class="about-icon">&#10003;</div><div>AI-powered class photo attendance for fast group marking.</div></div>
                        <div class="about-item"><div class="about-icon">&#10003;</div><div>FaceID check-in for individual student attendance.</div></div>
                        <div class="about-item"><div class="about-icon">&#10003;</div><div>Manual attendance with instant save and correction support.</div></div>
                        <div class="about-item"><div class="about-icon">&#10003;</div><div>Low-attendance alerts, analytics, reports, and CSV export.</div></div>
                        <div class="about-item"><div class="about-icon">&#10003;</div><div>Secure institute access codes for onboarding admins and students.</div></div>
                        <div class="about-item"><div class="about-icon">&#10003;</div><div>Designed for Indian schools, coaching centres, and tuition institutes.</div></div>
                    </div>
                </div>

                <div class="about-card">
                    <h3>Built for Every Role</h3>
                    <div class="role-block"><strong>Students</strong> &mdash; View attendance, subjects, reports, and FaceID status.</div>
                    <div class="role-block"><strong>Teachers</strong> &mdash; Mark manual or AI attendance, manage class records, and view analytics.</div>
                    <div class="role-block"><strong>Institute Admins</strong> &mdash; Add teachers, students, classes, subjects, and monitor attendance.</div>
                    <div class="role-block"><strong>Founders</strong> &mdash; Manage institutes, access codes, subscriptions, plans, and platform reports.</div>
                </div>
            </div>

            <div class="steps-grid">
                <div class="step-card">
                    <div class="step-number">1</div>
                    <h4>Create Institute</h4>
                    <p>Admin sets up institute profile, plan, and academic details.</p>
                </div>

                <div class="step-card">
                    <div class="step-number">2</div>
                    <h4>Add Classes</h4>
                    <p>Create classes, sections, subjects, teachers, and students.</p>
                </div>

                <div class="step-card">
                    <div class="step-number">3</div>
                    <h4>Mark Attendance</h4>
                    <p>Use manual attendance, FaceID, or AI class photo attendance.</p>
                </div>

                <div class="step-card">
                    <div class="step-number">4</div>
                    <h4>Track Reports</h4>
                    <p>View attendance history, analytics, low attendance, and exports.</p>
                </div>
            </div>

            <div class="about-cta">
                <a href="#portals">&#128640; Get Started &mdash; Choose Your Portal</a>
            </div>
        </section>
        """
    )
    st.html(about_html)


def show_about() -> None:
    render_public_nav(show_links=False)

    if st.button("Back to Home", key="about_back"):
        go_to("landing")

    render_about_section()
