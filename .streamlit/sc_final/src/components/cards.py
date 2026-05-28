import streamlit as st
from src.utils.helpers import attendance_color, progress_bar_html

def stat_card(label: str, value, subtitle: str = "", color: str = "blue", icon: str = "📊"):
    st.markdown(f'''
    <div class="sc-stat {color}">
      <div class="sc-stat-icon">{icon}</div>
      <div class="sc-stat-label">{label}</div>
      <div class="sc-stat-value">{value}</div>
      <div class="sc-stat-sub">{subtitle}</div>
    </div>''', unsafe_allow_html=True)

def subject_card(subject: str, teacher: str, present: int, total: int, attendance: float):
    kind = attendance_color(attendance)
    badge_color = {"ok":"#10B981","warn":"#F59E0B","danger":"#EF4444"}.get(kind,"#5B6CFF")
    bar = progress_bar_html(attendance, badge_color)
    label_map = {"ok":"✅ Good Standing","warn":"⚠️ Low Attendance","danger":"🚨 Critical"}
    st.markdown(f'''
    <div class="sc-subject-card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <h4>{subject}</h4>
          <p>👤 {teacher} &nbsp;•&nbsp; {present}/{total} classes</p>
        </div>
        <span class="sc-badge {kind}">{attendance}%</span>
      </div>
      {bar}
      <p style="margin:8px 0 0;font-size:.82rem;color:#6B7280;">{label_map.get(kind,"")}</p>
    </div>''', unsafe_allow_html=True)

def class_item(subject: str, time: str, teacher: str, status: str):
    color_map = {"Present":"ok","Upcoming":"primary","Absent":"danger"}
    kind = color_map.get(status, "info")
    st.markdown(f'''
    <div class="sc-class-item">
      <div>
        <div style="font-weight:600">{subject}</div>
        <div style="color:#6B7280;font-size:.85rem">{teacher} • {time}</div>
      </div>
      <span class="sc-badge {kind}">{status}</span>
    </div>''', unsafe_allow_html=True)

def alert_card(message: str, kind: str = "info"):
    icons = {"warning":"⚠️","danger":"🚨","success":"✅","info":"ℹ️"}
    st.markdown(f'''
    <div class="sc-alert {kind}">
      <span>{icons.get(kind,"ℹ️")}</span>
      <span>{message}</span>
    </div>''', unsafe_allow_html=True)

def feature_card(title: str, desc: str, icon: str = "⚡", gradient: str = "linear-gradient(135deg,#5B6CFF,#818cf8)"):
    st.markdown(f'''
    <div class="sc-feature-card">
      <div class="sc-feature-icon" style="background:{gradient};">{icon}</div>
      <h4 style="margin:0 0 8px;">{title}</h4>
      <p style="color:#6B7280;font-size:.9rem;margin:0;">{desc}</p>
    </div>''', unsafe_allow_html=True)

def portal_card(icon: str, title: str, desc: str, color_class: str):
    st.markdown(f'''
    <div class="sc-card" style="text-align:center;">
      <div class="sc-portal-icon {color_class}">{icon}</div>
      <h3 style="margin:0 0 8px;">{title}</h3>
      <p style="color:#6B7280;margin:0 0 4px;font-size:.95rem;">{desc}</p>
    </div>''', unsafe_allow_html=True)
