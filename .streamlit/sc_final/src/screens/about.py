"""About page — separate from landing."""
import streamlit as st
from src.components.public_nav import render_public_nav
from src.components.navigation import go_to

def show_about():
    render_public_nav(show_links=False)
    if st.button("← Back to Home", key="about_back"): go_to("landing")
    st.markdown("""
    <div style="max-width:800px;margin:40px auto;">
      <h1 style="text-align:center;font-family:Poppins,sans-serif;
        background:linear-gradient(135deg,#5B6CFF,#FF4FA3);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        Attendance that just works.
      </h1>
      <p style="text-align:center;color:#6B7280;font-size:1.1rem;margin-bottom:40px;">
        SnapClass AI removes the friction of daily attendance — for students, teachers, and admins.
      </p>
    </div>""", unsafe_allow_html=True)

    c1,c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("""
        <div class="sc-card">
          <h3>Why SnapClass AI?</h3>
          <ul style="color:#6B7280;line-height:2;">
            <li>AI-powered class photo attendance</li>
            <li>FaceID for individual student check-in</li>
            <li>Manual attendance with instant save</li>
            <li>Low-attendance alerts via email</li>
            <li>Multi-institute management from one panel</li>
            <li>Secure access code system for institutes</li>
          </ul>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="sc-card">
          <h3>Built for Everyone</h3>
          <p style="color:#6B7280;line-height:1.8;">
            <strong>Students</strong> — Track your own attendance, get alerts when it drops below 75%.<br><br>
            <strong>Teachers</strong> — Mark attendance in seconds, view class analytics, export reports.<br><br>
            <strong>Institute Admins</strong> — Manage teachers, students, classes, and subjects.<br><br>
            <strong>Founders</strong> — Create and manage multiple institutes from SnapClass HQ.
          </p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Get Started — Choose Your Portal", type="primary",
                     use_container_width=True, key="about_start"):
            go_to("landing")
