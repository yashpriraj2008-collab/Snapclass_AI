"""Founder plans and pricing management page."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import html
from typing import Any

import streamlit as st

from src.components.ui import db_status_banner
from src.database.client import get_supabase


ALLOWED_PLAN_CODES = ("demo", "starter", "pro", "enterprise")
STATUS_OPTIONS = ("active", "pending_payment", "expired", "cancelled")

CANONICAL_PLANS: dict[str, dict[str, Any]] = {
    "demo": {
        "plan_code": "demo",
        "Plan name": "Demo",
        "Price": "Free",
        "Student limit": 50,
        "Teacher limit": 1,
        "AI attendance": "No",
        "billing_cycle": "forever",
        "amount_paise": 0,
        "sort_order": 1,
    },
    "starter": {
        "plan_code": "starter",
        "Plan name": "Starter",
        "Price": "INR 499/month",
        "Student limit": 200,
        "Teacher limit": 5,
        "AI attendance": "No",
        "billing_cycle": "monthly",
        "amount_paise": 49900,
        "sort_order": 2,
    },
    "pro": {
        "plan_code": "pro",
        "Plan name": "Pro",
        "Price": "INR 999/month",
        "Student limit": 1000,
        "Teacher limit": 20,
        "AI attendance": "Yes",
        "billing_cycle": "monthly",
        "amount_paise": 99900,
        "sort_order": 3,
    },
    "enterprise": {
        "plan_code": "enterprise",
        "Plan name": "Enterprise",
        "Price": "INR 4,999/month",
        "Student limit": "Unlimited",
        "Teacher limit": "Unlimited",
        "AI attendance": "Yes",
        "billing_cycle": "monthly",
        "amount_paise": 499900,
        "sort_order": 4,
    },
}


def _safe_text(value: Any, default: str = "-") -> str:
    text = str(value or "").strip()
    return text or default


def _norm_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text in ALLOWED_PLAN_CODES else "demo"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _query_all(table: str) -> tuple[list[dict[str, Any]], str | None]:
    db = get_supabase()
    if not db:
        return [], "Supabase client not configured."
    try:
        rows = db.table(table).select("*").execute().data or []
        return rows, None
    except Exception as exc:
        return [], str(exc)


def _is_active_row(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "").strip().lower()
    if status:
        return status == "active"
    is_active = row.get("is_active")
    return bool(True if is_active is None else is_active)


def _sort_key(row: dict[str, Any]) -> tuple[int, str]:
    plan_code = _norm_code(row.get("plan_code") or row.get("code"))
    try:
        order = int(row.get("sort_order") or CANONICAL_PLANS[plan_code]["sort_order"])
    except Exception:
        order = CANONICAL_PLANS[plan_code]["sort_order"]
    return order, plan_code


def _price_label(row: dict[str, Any], canonical: dict[str, Any]) -> str:
    amount = row.get("amount_paise")
    if amount is None:
        amount = row.get("price_paise")
    if amount is None:
        amount = row.get("price_inr")
        if amount not in {None, ""}:
            try:
                return f"INR {int(amount):,}/{row.get('billing_cycle') or canonical['billing_cycle']}"
            except Exception:
                pass
    try:
        paise = int(amount or canonical["amount_paise"])
    except Exception:
        paise = int(canonical["amount_paise"])
    if paise <= 0:
        return "Free"
    rupees = paise // 100
    cycle = str(row.get("billing_cycle") or canonical["billing_cycle"] or "monthly")
    suffix = "month" if cycle == "monthly" else cycle
    return f"INR {rupees:,}/{suffix}"


def _normalize_plan(row: dict[str, Any] | None, plan_code: str) -> dict[str, Any]:
    plan_code = _norm_code(plan_code)
    canonical = dict(CANONICAL_PLANS[plan_code])
    row = row or {}
    limits = _as_dict(row.get("limits"))
    flags = _as_dict(row.get("feature_flags"))

    display_name = row.get("display_name") or row.get("name") or row.get("plan_name")
    if display_name:
        canonical["Plan name"] = _safe_text(display_name, canonical["Plan name"])
    canonical["id"] = row.get("id") or ""
    canonical["billing_cycle"] = row.get("billing_cycle") or canonical["billing_cycle"]
    canonical["sort_order"] = row.get("sort_order") or canonical["sort_order"]
    canonical["Price"] = _price_label(row, canonical)
    canonical["Student limit"] = (
        limits.get("max_students")
        if "max_students" in limits
        else limits.get("students", row.get("max_students", canonical["Student limit"]))
    )
    canonical["Teacher limit"] = (
        limits.get("max_teachers")
        if "max_teachers" in limits
        else limits.get("teachers", row.get("max_teachers", canonical["Teacher limit"]))
    )
    ai_enabled = flags.get("ai_attendance", row.get("ai_attendance"))
    if ai_enabled is not None:
        canonical["AI attendance"] = "Yes" if bool(ai_enabled) else "No"
    return canonical


def _load_plans() -> tuple[list[dict[str, Any]], str | None]:
    rows, error = _query_all("plans")
    if error:
        return [_normalize_plan(None, code) for code in ALLOWED_PLAN_CODES], error

    rows_by_code: dict[str, dict[str, Any]] = {}
    for row in sorted(rows, key=_sort_key):
        code = _norm_code(row.get("plan_code") or row.get("code"))
        if code in ALLOWED_PLAN_CODES and _is_active_row(row):
            rows_by_code[code] = row

    plans = [_normalize_plan(rows_by_code.get(code), code) for code in ALLOWED_PLAN_CODES]
    return plans, None


def _load_institutes() -> tuple[list[dict[str, Any]], str | None]:
    rows, error = _query_all("institutes")
    if error:
        return [], error
    return sorted(rows, key=lambda row: str(row.get("name") or "").lower()), None


def _load_subscriptions() -> tuple[list[dict[str, Any]], str | None]:
    rows, error = _query_all("subscriptions")
    if error:
        return [], error
    return sorted(rows, key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True), None


def _plan_maps(plans: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_code = {str(plan["plan_code"]): plan for plan in plans}
    by_id = {str(plan["id"]): plan for plan in plans if plan.get("id")}
    return by_code, by_id


def _latest_subscriptions_by_institute(subscriptions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_institute: dict[str, dict[str, Any]] = {}
    for sub in subscriptions:
        institute_id = str(sub.get("institute_id") or "")
        if institute_id and institute_id not in by_institute:
            by_institute[institute_id] = sub
    return by_institute


def _db_subscription_status(status: str) -> str:
    status = str(status or "active").strip().lower()
    return status if status in {"active", "expired", "cancelled"} else "active"


def _unsupported_columns_from_error(error: Exception, payload: dict[str, Any]) -> list[str]:
    raw = str(error).lower()
    if "column" not in raw and "schema cache" not in raw and "could not find" not in raw:
        return []
    return [column for column in payload if column.lower() in raw]


def _update_with_supported_columns(table: str, row_id: str, payload: dict[str, Any]) -> tuple[bool, str]:
    db = get_supabase()
    if not db:
        return False, "Supabase client not configured."
    try:
        db.table(table).update(payload).eq("id", row_id).execute()
        return True, ""
    except Exception as exc:
        unsupported = _unsupported_columns_from_error(exc, payload)
        if not unsupported:
            return False, str(exc)

    retry = {key: value for key, value in payload.items() if key not in unsupported}
    try:
        db.table(table).update(retry).eq("id", row_id).execute()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _insert_with_supported_columns(table: str, payload: dict[str, Any]) -> tuple[bool, str]:
    db = get_supabase()
    if not db:
        return False, "Supabase client not configured."
    try:
        db.table(table).insert(payload).execute()
        return True, ""
    except Exception as exc:
        unsupported = _unsupported_columns_from_error(exc, payload)
        if not unsupported:
            return False, str(exc)

    retry = {key: value for key, value in payload.items() if key not in unsupported}
    try:
        db.table(table).insert(retry).execute()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _subscription_payload(institute_id: str, plan: dict[str, Any], status: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    plan_code = _norm_code(plan.get("plan_code"))
    ends_at = now + timedelta(days=3650 if plan_code == "demo" else 30)
    payload = {
        "institute_id": institute_id,
        "plan_id": plan.get("id") or None,
        "plan_code": plan_code,
        "plan_name": plan.get("Plan name") or plan_code.title(),
        "billing_cycle": plan.get("billing_cycle") or "monthly",
        "status": _db_subscription_status(status),
        "starts_at": now.isoformat(),
        "ends_at": ends_at.isoformat(),
        "start_date": now.date().isoformat(),
        "end_date": ends_at.date().isoformat(),
        "updated_at": now.isoformat(),
    }
    return {key: value for key, value in payload.items() if value is not None}


def ensure_subscription_rows(
    institutes: list[dict[str, Any]] | None = None,
    subscriptions: list[dict[str, Any]] | None = None,
    plans: list[dict[str, Any]] | None = None,
) -> tuple[int, list[str]]:
    institutes = institutes if institutes is not None else _load_institutes()[0]
    subscriptions = subscriptions if subscriptions is not None else _load_subscriptions()[0]
    plans = plans if plans is not None else _load_plans()[0]
    plans_by_code, _plans_by_id = _plan_maps(plans)
    sub_by_institute = _latest_subscriptions_by_institute(subscriptions)
    created = 0
    errors: list[str] = []

    for institute in institutes:
        institute_id = str(institute.get("id") or "")
        if not institute_id or institute_id in sub_by_institute:
            continue
        plan = plans_by_code.get(_norm_code(institute.get("plan"))) or plans_by_code.get("demo")
        if not plan or not plan.get("id"):
            errors.append(f"{_safe_text(institute.get('name'), 'Institute')}: missing active database plan row.")
            continue
        payload = _subscription_payload(institute_id, plan, str(institute.get("subscription_status") or "active"))
        ok, error = _insert_with_supported_columns("subscriptions", payload)
        if ok:
            created += 1
        else:
            errors.append(f"{_safe_text(institute.get('name'), 'Institute')}: {error}")
    return created, errors


def _resolve_plan_for_institute(
    institute: dict[str, Any],
    subscription: dict[str, Any],
    plans_by_code: dict[str, dict[str, Any]],
    plans_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    plan_id = str(subscription.get("plan_id") or "")
    if plan_id and plan_id in plans_by_id:
        return plans_by_id[plan_id]
    plan_code = _norm_code(subscription.get("plan_code") or institute.get("plan"))
    return plans_by_code.get(plan_code) or plans_by_code["demo"]


def _overview_rows(
    institutes: list[dict[str, Any]],
    subscriptions: list[dict[str, Any]],
    plans: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plans_by_code, plans_by_id = _plan_maps(plans)
    sub_by_institute = _latest_subscriptions_by_institute(subscriptions)
    rows: list[dict[str, Any]] = []

    for institute in institutes:
        institute_id = str(institute.get("id") or "")
        sub = sub_by_institute.get(institute_id, {})
        plan = _resolve_plan_for_institute(institute, sub, plans_by_code, plans_by_id)
        rows.append(
            {
                "Institute Name": _safe_text(institute.get("name"), "Unknown"),
                "Admin Email": _safe_text(institute.get("admin_email")),
                "Current Plan": plan["Plan name"],
                "Status": sub.get("status") or institute.get("subscription_status") or "active",
                "Students Limit": plan["Student limit"],
                "Teachers Limit": plan["Teacher limit"],
                "AI Enabled": plan["AI attendance"],
            }
        )
    return rows


def _update_subscription(institute: dict[str, Any], plan: dict[str, Any], status: str) -> tuple[bool, str]:
    db = get_supabase()
    if not db:
        return False, "Supabase client not configured."

    institute_id = str(institute.get("id") or "")
    if not institute_id:
        return False, "Missing institute id."
    if not plan.get("id"):
        return False, f"Missing active database plan row for {plan.get('Plan name') or plan.get('plan_code')}."

    institute_status = str(status or "active").strip().lower()
    institute_payload = {
        "plan": plan["plan_code"],
        "subscription_status": institute_status,
    }
    ok, error = _update_with_supported_columns("institutes", institute_id, institute_payload)
    if not ok:
        return False, error

    try:
        existing_rows = (
            db.table("subscriptions")
            .select("*")
            .eq("institute_id", institute_id)
            .limit(1)
            .execute()
            .data
            or []
        )
    except Exception as exc:
        return False, str(exc)

    payload = _subscription_payload(institute_id, plan, institute_status)
    if existing_rows:
        return _update_with_supported_columns("subscriptions", str(existing_rows[0]["id"]), payload)
    return _insert_with_supported_columns("subscriptions", payload)


def _inject_page_css() -> None:
    st.markdown(
        """
        <style>
        .plans-page-shell h3 { margin-bottom: 0.2rem; }
        .plans-subtitle { color: #6B7280; margin: 0 0 22px; }
        .plan-card {
          min-height: 220px;
          padding: 22px;
          background: #ffffff;
          border: 1px solid #E5E7EB;
          border-radius: 16px;
          box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        }
        .plan-card-title {
          color: #111827;
          font-size: 22px;
          font-weight: 850;
          margin-bottom: 6px;
        }
        .plan-card-price {
          color: #4F46E5;
          font-size: 24px;
          font-weight: 900;
          margin-bottom: 16px;
        }
        .plan-card-row {
          display: flex;
          justify-content: space-between;
          gap: 14px;
          padding: 7px 0;
          border-top: 1px solid #F3F4F6;
          color: #374151;
          font-size: 14px;
        }
        .plan-actions-panel {
          padding: 24px;
          background: #ffffff;
          border: 1px solid #E5E7EB;
          border-radius: 18px;
          box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
        }
        .plan-action-summary {
          display: flex;
          align-items: center;
          gap: 12px;
          min-height: 52px;
          margin-top: 18px;
          padding: 12px 14px;
          border: 1px solid #E0E7FF;
          border-radius: 14px;
          background: #F8FAFF;
          color: #334155;
          font-size: 14px;
          line-height: 1.45;
        }
        .plan-action-summary strong {
          color: #0F172A;
        }
        .plan-action-summary .arrow {
          color: #6366F1;
          font-size: 18px;
          font-weight: 800;
        }
        .st-key-update_subscription {
          margin-top: 18px;
        }
        .st-key-update_subscription button {
          min-height: 48px !important;
          border-radius: 13px !important;
          font-size: 15px !important;
          font-weight: 750 !important;
          background: linear-gradient(90deg, #6366F1, #D946A8) !important;
          box-shadow: 0 10px 24px rgba(99, 102, 241, 0.22) !important;
        }
        .st-key-update_subscription button:hover {
          transform: translateY(-1px) !important;
          box-shadow: 0 14px 30px rgba(99, 102, 241, 0.28) !important;
        }
        @media (max-width: 768px) {
          .plan-actions-panel {
            padding: 18px;
          }
          .plan-action-summary {
            align-items: flex-start;
            flex-direction: column;
            gap: 4px;
          }
          .plan-action-summary .arrow {
            transform: rotate(90deg);
          }
        }
        .plans-overview-table {
          width: 100%;
          overflow-x: auto;
          margin-top: 14px;
          background: #ffffff;
          border: 1px solid #E5E7EB;
          border-radius: 14px;
          box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
        }
        .plans-overview-table table {
          width: 100%;
          min-width: 860px;
          border-collapse: collapse;
        }
        .plans-overview-table th {
          padding: 14px 16px;
          background: #F8FAFC;
          color: #374151;
          text-align: left;
          font-size: 13px;
          font-weight: 800;
          border-bottom: 1px solid #E5E7EB;
        }
        .plans-overview-table td {
          padding: 14px 16px;
          color: #111827;
          font-size: 14px;
          border-bottom: 1px solid #F3F4F6;
          vertical-align: top;
        }
        .plans-overview-table tr:last-child td {
          border-bottom: 0;
        }
        .plans-status-pill {
          display: inline-block;
          min-width: 72px;
          padding: 5px 10px;
          border-radius: 999px;
          background: #EEF2FF;
          color: #4338CA;
          font-weight: 800;
          font-size: 12px;
          text-align: center;
        }
        .stSelectbox div[data-baseweb="select"],
        .stSelectbox div[data-baseweb="select"] *,
        div[data-testid="stSelectbox"] div[data-baseweb="select"],
        div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
          color: #111827 !important;
          -webkit-text-fill-color: #111827 !important;
          background-color: #ffffff !important;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] input,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] input::placeholder,
        div[data-testid="stSelectbox"] [data-baseweb="select"] [class*="singleValue"],
        div[data-testid="stSelectbox"] [data-baseweb="select"] [class*="SingleValue"],
        div[data-testid="stSelectbox"] [data-baseweb="select"] [class*="valueContainer"],
        div[data-testid="stSelectbox"] [data-baseweb="select"] [class*="ValueContainer"],
        div[data-testid="stSelectbox"] [data-baseweb="select"] [class*="placeholder"],
        div[data-testid="stSelectbox"] [data-baseweb="select"] [class*="Placeholder"] {
          color: #111827 !important;
          -webkit-text-fill-color: #111827 !important;
          opacity: 1 !important;
          text-shadow: none !important;
        }
        div[data-baseweb="popover"] * {
          color: #111827 !important;
          -webkit-text-fill-color: #111827 !important;
          background-color: #ffffff !important;
        }
        div[data-testid="stSelectbox"] label {
          color: #374151 !important;
          -webkit-text-fill-color: #374151 !important;
          font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_plan_cards(plans: list[dict[str, Any]]) -> None:
    cols = st.columns(4, gap="medium")
    for col, plan in zip(cols, plans):
        with col:
            st.markdown(
                f"""
                <div class="plan-card">
                  <div class="plan-card-title">{html.escape(str(plan["Plan name"]))}</div>
                  <div class="plan-card-price">{html.escape(str(plan["Price"]))}</div>
                  <div class="plan-card-row"><span>Students</span><strong>{html.escape(str(plan["Student limit"]))}</strong></div>
                  <div class="plan-card-row"><span>Teachers</span><strong>{html.escape(str(plan["Teacher limit"]))}</strong></div>
                  <div class="plan-card-row"><span>AI Attendance</span><strong>{html.escape(str(plan["AI attendance"]))}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_overview_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        st.info("No institute plan rows found.")
        return

    headers = [
        "Institute Name",
        "Admin Email",
        "Current Plan",
        "Status",
        "Students Limit",
        "Teachers Limit",
        "AI Enabled",
    ]
    body = []
    for row in rows:
        cells = []
        for header in headers:
            value = html.escape(str(row.get(header, "-")))
            if header == "Status":
                value = f'<span class="plans-status-pill">{value.title()}</span>'
            cells.append(f"<td>{value}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")

    head = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    st.markdown(
        f"""
        <div class="plans-overview-table">
          <table>
            <thead><tr>{head}</tr></thead>
            <tbody>{''.join(body)}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _option_label_institute(institute: dict[str, Any]) -> str:
    return f"{_safe_text(institute.get('name'), 'Unknown')} - {_safe_text(institute.get('admin_email'), 'No admin email')}"


def _option_label_plan(plan: dict[str, Any]) -> str:
    return f"{plan['Plan name']} - {plan['Price']}"


def render_founder_plans() -> None:
    db_status_banner()
    _inject_page_css()
    st.markdown('<div class="plans-page-shell">', unsafe_allow_html=True)
    st.markdown("### Plans & Pricing")
    st.markdown('<p class="plans-subtitle">Manage active SnapClass AI subscriptions and plan limits.</p>', unsafe_allow_html=True)

    plans, plans_error = _load_plans()
    institutes, institutes_error = _load_institutes()
    subscriptions, subscriptions_error = _load_subscriptions()

    _render_plan_cards(plans)

    if plans_error:
        st.warning("Plan table could not be loaded. Showing the standard SnapClass AI plan model.")
    if institutes_error:
        st.error("Institutes could not be loaded.")
    if subscriptions_error:
        st.error("Subscriptions could not be loaded.")

    st.divider()
    st.markdown("### Institute Plans Overview")

    if not institutes:
        st.info("No institutes found yet.")
    else:
        rows = _overview_rows(institutes, subscriptions, plans)
        _render_overview_table(rows)

        missing_count = len(institutes) - len(_latest_subscriptions_by_institute(subscriptions))
        if missing_count > 0:
            st.caption(f"{missing_count} institute(s) do not have subscription rows yet.")
            if st.button("Create Missing Subscription Rows", use_container_width=True):
                try:
                    resp = get_supabase().rpc("create_missing_subscription_rows").execute()

                    if resp.data and resp.data.get("ok"):
                        inserted = resp.data.get("inserted", 0)
                        st.success(f"Created {inserted} missing subscription rows.")
                        st.rerun()
                    else:
                        st.warning("No missing subscription rows were created.")

                except Exception as e:
                    st.error("Could not create subscription rows. Please check database permissions.")
                    with st.expander("Developer Debug"):
                        st.code(str(e))

    st.divider()
    st.markdown("### Plan Actions")

    if not institutes:
        st.info("Create an institute before updating subscriptions.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown('<div class="plan-actions-panel">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.4, 1.1, 0.9], gap="medium")

    institute_options = [_option_label_institute(item) for item in institutes]
    plan_options = [_option_label_plan(item) for item in plans]
    institute_by_label = dict(zip(institute_options, institutes))
    plan_by_label = dict(zip(plan_options, plans))

    with c1:
        selected_institute_label = st.selectbox(
            "Select Institute",
            institute_options,
            index=0,
            key="founder_plan_action_institute",
        )
    with c2:
        selected_plan_label = st.selectbox(
            "Select New Plan",
            plan_options,
            index=0,
            key="founder_plan_action_plan",
        )
    with c3:
        selected_status = st.selectbox(
            "Select Status",
            list(STATUS_OPTIONS),
            index=0,
            key="founder_plan_action_status",
        )

    st.markdown(
        f"""
        <div class="plan-action-summary">
          <span><strong>{html.escape(selected_institute_label)}</strong></span>
          <span class="arrow">&rarr;</span>
          <span>{html.escape(selected_plan_label)}</span>
          <span>&middot;</span>
          <span>Status: <strong>{html.escape(selected_status.replace("_", " ").title())}</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _action_space, action_col = st.columns([2.2, 1], gap="medium")
    with action_col:
        update_clicked = st.button(
            "Update Subscription",
            key="update_subscription",
            type="primary",
            use_container_width=True,
        )

    if update_clicked:
        selected_institute = institute_by_label[selected_institute_label]
        selected_plan = plan_by_label[selected_plan_label]
        ok, error = _update_subscription(selected_institute, selected_plan, selected_status)
        if ok:
            st.success("Subscription updated successfully.")
            st.rerun()
        else:
            st.error(error or "Subscription could not be updated.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
