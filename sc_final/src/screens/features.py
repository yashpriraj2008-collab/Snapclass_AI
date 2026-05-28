"""Features page."""
import streamlit as st
from src.components.public_nav import render_public_nav
from src.components.navigation import go_to

def show_features():
    render_public_nav(show_links=False)
    if st.button("← Back to Home", key="feat_back"): go_to("landing")
    st.markdown("""
    <div style="text-align:center;padding:30px 0 20px;">
      <h1 style="font-family:Poppins,sans-serif;
        background:linear-gradient(135deg,#5B6CFF,#FF4FA3);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        Everything You Need
      </h1>
      <p style="color:#6B7280;font-size:1.1rem;">One platform. Every attendance need covered.</p>
    </div>""", unsafe_allow_html=True)

    features = [
        ("🤖","AI Class Photo Attendance","linear-gradient(135deg,#5B6CFF,#818cf8)",
         "Upload a group class photo — AI detects faces and marks attendance automatically. No manual work needed."),
        ("🪪","Student FaceID","linear-gradient(135deg,#FF4FA3,#f472b6)",
         "Students enroll their face once and check in using their camera. Fast, secure, contactless."),
        ("✏️","Manual Attendance","linear-gradient(135deg,#10B981,#34d399)",
         "Quick manual marking with class/subject/date selection. Editable table with present/absent checkboxes."),
        ("📊","Analytics & Charts","linear-gradient(135deg,#F59E0B,#fbbf24)",
         "Deep attendance insights with Plotly charts, weekly trends, subject-wise breakdowns, and monthly heatmaps."),
        ("📄","CSV & PDF Export","linear-gradient(135deg,#38BDF8,#7dd3fc)",
         "Download attendance reports as CSV or PDF. Student-wise, class-wise, and date-range reports."),
        ("📧","Email Alerts","linear-gradient(135deg,#8B5CF6,#a78bfa)",
         "Automatic email alerts when student attendance drops below 75%. Weekly report emails for teachers."),
        ("🏫","Institute Management","linear-gradient(135deg,#EC4899,#f472b6)",
         "Founders create institutes and generate access codes. Admins manage their own institute securely."),
        ("🔑","Secure Access Codes","linear-gradient(135deg,#06B6D4,#3B82F6)",
         "Cryptographically generated one-time access codes for institute admin onboarding. Expiry-controlled."),
        ("📱","Mobile Friendly","linear-gradient(135deg,#84CC16,#22C55E)",
         "Responsive layout works on desktop, tablet, and mobile browsers without any app install."),
    ]
    cols_row1 = st.columns(3, gap="large")
    cols_row2 = st.columns(3, gap="large")
    cols_row3 = st.columns(3, gap="large")
    all_cols = cols_row1 + cols_row2 + cols_row3
    for col,(icon,title,grad,desc) in zip(all_cols, features):
        with col:
            st.markdown(f"""
            <div class="sc-feat-card" style="margin-bottom:20px;">
              <div style="width:52px;height:52px;border-radius:15px;background:{grad};
                display:flex;align-items:center;justify-content:center;font-size:22px;
                margin-bottom:14px;box-shadow:0 4px 12px rgba(0,0,0,.1);">{icon}</div>
              <h4 style="margin:0 0 8px;font-size:.95rem;">{title}</h4>
              <p style="color:#6B7280;font-size:.85rem;margin:0;line-height:1.5;">{desc}</p>
            </div>""", unsafe_allow_html=True)
