"""Institute Admin dashboard — full version."""
import datetime as dt

import streamlit as st


from src.services.admin_context import get_current_institute_id
from src.services.institute_service import get_institute_by_id, init_institute_state, _db
from src.services.payment_service import create_razorpay_order, is_razorpay_connected
from src.services.subscription_access import (
    can_access_admin_portal,
    get_current_subscription,
    render_admin_context_bar,
    render_billing_workspace,
)


from src.utils.session import nav_institute
from src.components.ui import db_status_banner
from src.utils.user_guards import show_payment_not_configured


def _date_only(value) -> str:
    text = str(value or "").strip()
    return text[:10] if text else ""


def _is_past(value) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed < dt.datetime.now(dt.timezone.utc)


def _plan_by_id(db, plan_id: str) -> dict:
    if not db or not plan_id:
        return {}
    try:
        rows = db.table("plans").select("*").eq("id", plan_id).limit(1).execute().data or []
        return rows[0] if rows else {}
    except Exception:
        return {}


def _plan_by_code(db, plan_code: str) -> dict:
    if not db or not plan_code:
        return {}
    try:
        rows = db.table("plans").select("*").eq("plan_code", plan_code).limit(1).execute().data or []
        return rows[0] if rows else {}
    except Exception:
        return {}


def _subscription_for_institute(institute_id: str) -> tuple[dict, dict]:
    db = _db()
    if not db or not institute_id:
        return {}, {}
    try:
        rows = (
            db.table("subscriptions")
            .select("*")
            .eq("institute_id", institute_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            return {}, {}
        sub = rows[0]
        return sub, _plan_by_id(db, str(sub.get("plan_id") or ""))
    except Exception:
        return {}, {}


def _plan_display_name(plan: dict, fallback_code: str = "") -> str:
    code = str(plan.get("plan_code") or fallback_code or "").strip().lower()
    name = plan.get("display_name") or plan.get("name") or code.title() or "Current"
    return f"{name} Plan" if not str(name).lower().endswith("plan") else str(name)


def _status_label(status: str) -> str:
    value = str(status or "").strip().lower()
    labels = {
        "pending_payment": "Payment Pending",
        "payment_pending": "Payment Pending",
        "pending": "Payment Pending",
        "active": "Active",
        "demo": "Active",
        "expired": "Expired",
        "cancelled": "Cancelled",
    }
    return labels.get(value, value.replace("_", " ").title() if value else "Unknown")


def _dev_mode() -> bool:
    try:
        from src.database.client import read_app_secrets

        env = str(read_app_secrets().get("APP_ENV") or "").strip().lower()
    except Exception:
        env = ""
    return env == "development"


def _mark_payment_success_dev(institute_id: str, plan_code: str) -> tuple[bool, str]:
    db = _db()
    if not db or not institute_id:
        return False, "Supabase is not configured."
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    plan = _plan_by_code(db, plan_code)
    plan_id = str(plan.get("id") or "")
    try:
        existing = db.table("subscriptions").select("id").eq("institute_id", institute_id).limit(1).execute().data or []
        sub_payload = {
            "institute_id": institute_id,
            "status": "active",
            "billing_cycle": plan.get("billing_cycle") or "monthly",
            "starts_at": now,
            "ends_at": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=30)).isoformat(),
            "updated_at": now,
        }
        if plan_id:
            sub_payload["plan_id"] = plan_id
        if existing:
            update_payload = {key: value for key, value in sub_payload.items() if key != "institute_id"}
            db.table("subscriptions").update(update_payload).eq("institute_id", institute_id).execute()
        else:
            db.table("subscriptions").insert(sub_payload).execute()
        db.table("institutes").update({"status": "active", "subscription_status": "active", "updated_at": now}).eq("id", institute_id).execute()
        st.session_state.subscription_status = "active"
        if isinstance(st.session_state.get("current_institute"), dict):
            st.session_state.current_institute["status"] = "active"
            st.session_state.current_institute["subscription_status"] = "active"
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _start_payment(plan_code: str, institute_id: str) -> None:
    """Launch Razorpay Checkout popup.

    Important: Do NOT navigate to payment_success here.
    payment_success must be reached from Razorpay handler that provides:
    razorpay_payment_id, razorpay_order_id, razorpay_signature.
    """

    import json
    import streamlit.components.v1 as components

    user_id = st.session_state.get("user_id") or st.session_state.get("auth_user_id")
    if not institute_id or not user_id:
        st.warning("Please login first.")
        return

    if not is_razorpay_connected():
        show_payment_not_configured()
        return

    try:
        order = create_razorpay_order(
            plan_code=plan_code,
            institute_id=str(institute_id),
            user_id=str(user_id),
        )
    except Exception:
        st.warning("Payment setup is not configured yet.")
        return

    # Where to redirect after Razorpay completes
    q_page_base = st.secrets.get("APP_BASE_URL", "http://localhost:8507")

    key_id = st.secrets.get("RAZORPAY_KEY_ID")
    if not key_id:
        st.warning("RAZORPAY_KEY_ID missing in secrets.")
        return

    order_id = str(order.get("order_id") or "")
    amount = int(order.get("amount") or 0)
    currency = str(order.get("currency") or "INR")
    plan_id = str(order.get("plan_id") or "")
    billing_cycle = str(order.get("billing_cycle") or "monthly")

    if not order_id or amount <= 0:
        st.warning("Could not create Razorpay order.")
        return

    redirect_base = f"{q_page_base}/?page=payment_success"

    html = f"""
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <button id="rzp-button"
        style=
            "width:100%;padding:16px 20px;border:none;border-radius:14px;background:linear-gradient(90deg,#6366f1,#ec4899);color:white;font-size:16px;font-weight:700;cursor:pointer;"
    >
        Pay Now
    </button>

    <script>
    var options = {{
        "key": {json.dumps(str(key_id))},
        "amount": {json.dumps(int(amount))},
        "currency": {json.dumps(str(currency))},
        "name": "SnapClass AI",
        "description": {json.dumps(str(plan_code).strip().title() + " Plan Subscription")},
        "order_id": {json.dumps(str(order_id))},
        "handler": function (response) {{
            const params = new URLSearchParams({{
                page: "payment_success",
                institute_id: {json.dumps(str(institute_id))},
                plan_code: {json.dumps(str(plan_code).strip().lower())},
                plan_id: {json.dumps(plan_id)},
                billing_cycle: {json.dumps(billing_cycle)},
                amount: {json.dumps(str(amount))},
                currency: {json.dumps(str(currency))},
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_signature: response.razorpay_signature
            }});

            window.location.href = {json.dumps(redirect_base)} + "&" + params.toString();
        }},
        "prefill": {{
            "email": {json.dumps(str(st.session_state.get('admin_email') or st.session_state.get('user_email') or ''))}
        }},
        "theme": {{
            "color": "#6366f1"
        }},
    }};

    var rzp = new Razorpay(options);
    document.getElementById('rzp-button').onclick = function(e) {{
        rzp.open();
        e.preventDefault();
    }};
    </script>
    """

    components.html(html, height=90)



def _render_subscription_banner(institute_id: str) -> None:
    sub, plan = _subscription_for_institute(institute_id)
    inst = st.session_state.get("current_institute") or {}
    selected_plan = str(st.session_state.get("selected_plan_code") or inst.get("plan") or "").strip().lower()
    plan_code = str(plan.get("plan_code") or selected_plan or "").strip().lower()
    if not plan and selected_plan:
        plan = _plan_by_code(_db(), selected_plan)
        plan_code = str(plan.get("plan_code") or selected_plan).strip().lower()
    plan_name = _plan_display_name(plan, plan_code)
    status = str(
        inst.get("subscription_status")
        or st.session_state.get("subscription_status")
        or sub.get("status")
        or ""
    ).strip().lower()

    expires_at = sub.get("ends_at")
    expired = status == "expired" or (status == "active" and _is_past(expires_at))

    if not sub and not status:
        st.info("Demo Plan active.")
        return

    if status in {"pending_payment", "payment_pending", "pending"}:
        return

    if expired:
        st.warning("Subscription expired. Please complete payment to continue.")
        if plan_code and st.button("Pay Now", type="primary", key="admin_expired_pay_now"):
            _start_payment(plan_code, institute_id)
        return

    if status in {"active", "demo"}:
        st.success(f"{plan_name} active.")
        return

    st.info(f"{plan_name} status: {_status_label(status)}.")


def show_institute_dashboard():
    init_institute_state()
    db_status_banner()
    inst_id  = get_current_institute_id()
    inst     = st.session_state.get("current_institute") or {}
    if inst_id and (not inst or not inst.get("name")):
        loaded = get_institute_by_id(str(inst_id))
        if loaded:
            inst = loaded
            st.session_state["current_institute"] = loaded
    admin_n  = st.session_state.get("admin_name", st.session_state.get("user_name","Admin"))
    inst_nm  = inst.get("name", st.session_state.get("active_institute_name","My Institute"))
    sub = get_current_subscription(str(inst_id or ""))
    legacy_sub, plan = _subscription_for_institute(str(inst_id or ""))
    if not sub:
        sub = legacy_sub
    selected_plan = str(st.session_state.get("selected_plan_code") or inst.get("plan") or "").strip().lower()
    if not plan and selected_plan:
        plan = _plan_by_code(_db(), selected_plan)
    status = str(
        inst.get("subscription_status")
        or st.session_state.get("subscription_status")
        or sub.get("status")
        or ""
    ).strip().lower()

    if not can_access_admin_portal(inst, sub):
        render_billing_workspace(inst, sub)
        return

    st.markdown(f"<h1>Welcome, {admin_n}! 🏫</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#6B7280;margin-top:-8px;'>{inst_nm} — Institute Overview</p>",
                unsafe_allow_html=True)

    render_admin_context_bar(inst, sub, payment_pending=False)

    _render_subscription_banner(str(inst_id or ""))


    def _count(table):
        db = _db()
        if db and inst_id:
            try: return len(db.table(table).select("id").eq("institute_id",inst_id).execute().data or [])
            except Exception: pass
        return len([x for x in st.session_state.get(table,[]) if x.get("institute_id")==inst_id])

    n_teachers = _count("teachers")
    n_students = _count("students")
    n_classes  = _count("classes")
    n_subjects = _count("subjects")
    n_assignments = _count("teacher_assignments")
    n_attendance = _count("attendance_sessions")

    c1,c2,c3,c4 = st.columns(4,gap="medium")
    for col,label,val,color,icon in [
        (c1,"Teachers",  n_teachers,"pink",  "👩‍🏫"),
        (c2,"Students",  n_students,"blue",  "👨‍🎓"),
        (c3,"Classes",   n_classes, "green", "🏫"),
        (c4,"Subjects",  n_subjects,"orange","📚"),
    ]:
        with col:
            st.markdown(f"""
            <div class="sc-stat {color}">
              <div class="sc-stat-icon">{icon}</div>
              <div class="sc-stat-label">{label}</div>
              <div class="sc-stat-value">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚡ Quick Actions")
    qa1,qa2,qa3,qa4 = st.columns(4,gap="medium")
    if qa1.button("➕ Add Teacher",  type="primary",use_container_width=True,key="qa_t"): nav_institute("teachers")
    if qa2.button("➕ Add Student",  type="primary",use_container_width=True,key="qa_s"): nav_institute("students")
    if qa3.button("➕ Add Class",    type="primary",use_container_width=True,key="qa_c"): nav_institute("classes_subjects")
    if qa4.button("➕ Add Subject",  type="primary",use_container_width=True,key="qa_sub"): nav_institute("classes_subjects")

    if not n_teachers and not n_students and not n_classes:
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown("""<div class="sc-alert info">ℹ️ <strong>Getting Started:</strong>
          Add Classes first → then Teachers → then Students.
          Use Quick Actions above or sidebar navigation.</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Setup Progress")
    has_classes = n_classes > 0
    has_subjects = n_subjects > 0
    has_teachers = n_teachers > 0
    has_students = n_students > 0
    has_assignments = n_assignments > 0 and has_teachers and has_classes and has_subjects
    has_attendance = n_attendance > 0
    checklist = [
        ("Create Class", has_classes),
        ("Add Teacher", has_teachers),
        ("Add Students", has_students),
        ("Create Subject", has_subjects),
        ("Assign Teacher", has_assignments),
        ("Start Attendance", has_attendance),
    ]
    cols = st.columns(3, gap="medium")
    for idx, (label, done) in enumerate(checklist):
        with cols[idx % 3]:
            status = "Done" if done else "Pending"
            tone = "ok" if done else "info"
            st.markdown(
                f'<div class="sc-alert {tone}"><strong>{status}</strong><br>{label}</div>',
                unsafe_allow_html=True,
            )

    # Institute info card
    if inst.get("logo_url"):
        st.image(inst.get("logo_url"), width=92)
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown("#### 🏫 Institute Profile")
    st.markdown(f"""
    <div class="sc-card" style="padding:22px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
        <div>
          <h3 style="margin:0 0 6px;">{inst.get("name","—")}</h3>
          <p style="margin:0;color:#6B7280;">
            🏛️ {inst.get("institute_type","School")} &nbsp;•&nbsp;
            📍 {inst.get("city","—")}, {inst.get("state","—")} &nbsp;•&nbsp;
            📧 {inst.get("admin_email","—")}
          </p>
        </div>
        <div style="display:flex;gap:8px;">
          <span class="sc-badge primary">{inst.get("plan","Demo")}</span>
          <span class="sc-badge ok">{inst.get("status","active").title()}</span>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)
    if st.button("✏️ Edit Institute Profile", key="inst_edit_btn"):
        nav_institute("my_institute")
