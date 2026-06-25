"""Sidebars for all portals."""
from __future__ import annotations

import html
import streamlit as st  # type: ignore[import]

from src.components.avatar import avatar_html
from src.components.branding import render_sidebar_brand
from src.database.client import get_supabase_client
from src.services.admin_context import get_current_institute_id
from src.services.institute_service import get_institute_by_id
from src.services.profile_photo_service import fetch_user_profile
from src.services.subscription_access import can_access_admin_portal, get_current_subscription
from src.utils.session import logout, nav_founder, nav_institute, nav_student, nav_teacher


def _brand() -> None:
    render_sidebar_brand()


def _sidebar_user(name: str, role: str, email: str = "") -> dict:
    email_value = str(
        email
        or st.session_state.get("user_email")
        or st.session_state.get("email")
        or ""
    ).strip().lower()
    profile = {}
    try:
        profile = fetch_user_profile(get_supabase_client(), email_value)
    except Exception:
        profile = {}
    session_user = st.session_state.get("user")
    if not isinstance(session_user, dict):
        session_user = {}
    return {
        **session_user,
        **profile,
        "name": profile.get("full_name") or profile.get("name") or name,
        "full_name": profile.get("full_name") or profile.get("name") or name,
        "email": profile.get("email") or email_value,
        "role": profile.get("role") or role,
        "profile_photo_url": (
            profile.get("profile_photo_url")
            or st.session_state.get("profile_photo_url")
            or session_user.get("profile_photo_url")
            or ""
        ),
    }


def _user_chip(user: dict, role_label: str) -> None:
    name = str(user.get("full_name") or user.get("name") or "User")
    email = str(user.get("email") or "")
    avatar_class = "sidebar-avatar" if user.get("profile_photo_url") else "sidebar-avatar sidebar-avatar-fallback"
    st.markdown(
        f"""
        <div class="sidebar-user-card">
          {avatar_html(user, size=48, border_color="#FFFFFF", css_class=avatar_class)}
          <div class="sidebar-user-info">
            <div class="sidebar-user-name">{html.escape(name)}</div>
            <div class="sidebar-user-role">{html.escape(role_label)}</div>
            <div class="sidebar-user-email">{html.escape(email)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section(title: str) -> None:
    st.markdown(
        f'<div class="sidebar-section-title">{html.escape(title)}</div>',
        unsafe_allow_html=True,
    )


def _nav_btn(label: str, key: str) -> bool:
    return st.button(label, key=key, use_container_width=True)


def student_sidebar() -> None:
    with st.sidebar:
        _brand()
        name = (st.session_state.get("user_name", "") or "Student").replace(" Demo", "").strip() or "Student"
        _user_chip(_sidebar_user(name, "student"), "Student")
        _section("MAIN")
        if _nav_btn("Dashboard", "snav_dashboard"):
            nav_student("dashboard")
        if _nav_btn("FaceID Attendance", "snav_faceid"):
            nav_student("faceid")
        if _nav_btn("My Subjects", "snav_subjects"):
            nav_student("subjects")
        if _nav_btn("Attendance History", "snav_history"):
            nav_student("history")
        _section("INSIGHTS")
        if _nav_btn("Analytics", "snav_analytics"):
            nav_student("analytics")
        if _nav_btn("Reports", "snav_reports"):
            nav_student("reports")
        _section("ACCOUNT")
        if _nav_btn("Profile", "snav_profile"):
            nav_student("profile")
        st.divider()
        if _nav_btn("Logout", "student_logout"):
            logout()


def teacher_sidebar() -> None:
    with st.sidebar:
        _brand()
        name = (st.session_state.get("user_name", "") or "Teacher").replace(" Demo", "").strip() or "Teacher"
        _user_chip(_sidebar_user(name, "teacher"), "Teacher")
        _section("MAIN")
        if _nav_btn("Dashboard", "tnav_dashboard"):
            nav_teacher("dashboard")
        if _nav_btn("Manual Attendance", "tnav_manual"):
            nav_teacher("manual_att")
        if _nav_btn("AI Attendance", "tnav_ai"):
            nav_teacher("ai_att")
        if _nav_btn("My Classes", "tnav_classes"):
            nav_teacher("classes")
        if _nav_btn("Students", "tnav_students"):
            nav_teacher("students")
        _section("INSIGHTS")
        if _nav_btn("Analytics", "tnav_analytics"):
            nav_teacher("analytics")
        if _nav_btn("Reports", "tnav_reports"):
            nav_teacher("reports")
        _section("ACCOUNT")
        if _nav_btn("Profile", "tnav_profile"):
            nav_teacher("profile")
        st.divider()
        if _nav_btn("Logout", "teacher_logout"):
            logout()


def institute_sidebar() -> None:
    with st.sidebar:
        _brand()
        name = st.session_state.get("admin_name", "") or st.session_state.get("user_name", "Admin")
        inst_nm = st.session_state.get("active_institute_name", "My Institute")
        _user_chip(_sidebar_user(name, "institute_admin"), inst_nm)

        institute_id = str(get_current_institute_id() or st.session_state.get("institute_id") or "")
        institute = st.session_state.get("current_institute") or {}
        if institute_id and (not institute or not institute.get("name")):
            institute = get_institute_by_id(institute_id) or institute
            if institute:
                st.session_state.current_institute = institute
        subscription = get_current_subscription(institute_id)
        locked = bool(institute_id and not can_access_admin_portal(institute, subscription))

        if locked:
            _section("SUBSCRIPTION")
            if _nav_btn("Billing / Pay Now", "inav_billing_pay"):
                st.session_state.page = "payment"
                st.rerun()
            st.divider()
            if _nav_btn("Logout", "inst_logout"):
                logout()
            return

        _section("MAIN")
        if _nav_btn("Dashboard", "inav_dash"):
            nav_institute("institute_dashboard")
        if _nav_btn("My Institute", "inav_myinst"):
            nav_institute("my_institute")
        if _nav_btn("Teachers", "inav_teach"):
            nav_institute("teachers")
        if _nav_btn("Students", "inav_stud"):
            nav_institute("students")
        if _nav_btn("Classes & Subjects", "inav_cls"):
            nav_institute("classes_subjects")
        if _nav_btn("Attendance", "inav_att"):
            nav_institute("attendance")
        _section("INSIGHTS")
        if _nav_btn("Analytics", "inav_analytics"):
            nav_institute("analytics")
        if _nav_btn("Reports", "inav_reports"):
            nav_institute("reports")
        _section("SYSTEM")
        if _nav_btn("Settings", "inav_settings"):
            nav_institute("settings")
        st.divider()
        if _nav_btn("Logout", "inst_logout"):
            logout()


def founder_sidebar() -> None:
    with st.sidebar:
        _brand()
        founder_name = st.session_state.get("user_name") or "Founder"
        founder_role_label = st.session_state.get("role", "founder").replace("_", " ").title() or "Founder"
        _user_chip(_sidebar_user(founder_name, "founder"), founder_role_label)
        _section("SNAPCLASS HQ")
        if _nav_btn("Dashboard", "fnav_dash"):
            nav_founder("founder_dashboard")
        if _nav_btn("Institutes", "fnav_inst"):
            nav_founder("founder_institutes")
        if _nav_btn("Generate Code", "fnav_codes"):
            nav_founder("founder_codes")
        if _nav_btn("All Codes", "fnav_acodes"):
            nav_founder("founder_allcodes")
        if _nav_btn("Plans", "fnav_plans"):
            nav_founder("founder_plans")
        if _nav_btn("Leads", "fnav_leads"):
            nav_founder("founder_leads")
        if _nav_btn("Reports", "fnav_reps"):
            nav_founder("founder_reports")
        if _nav_btn("Settings", "fnav_set"):
            nav_founder("founder_settings")
        st.divider()
        if _nav_btn("Logout", "founder_logout"):
            logout()
