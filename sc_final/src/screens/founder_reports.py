from __future__ import annotations

from collections import Counter
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from src.components.ui import db_status_banner


def _rows(response: Any) -> list[dict[str, Any]]:
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    return data or []


def _safe_fetch(db: Any, table_name: str, select: str = "*", *, order_by: str = "", desc: bool = False) -> list[dict[str, Any]]:
    if not db:
        return []
    try:
        query = db.table(table_name).select(select)
        if order_by:
            query = query.order(order_by, desc=desc)
        return _rows(query.execute())
    except Exception:
        return []


def _count_rows(db: Any, table_names: list[str]) -> int:
    for table_name in table_names:
        rows = _safe_fetch(db, table_name, "id")
        if rows:
            return len(rows)
    return 0


def _text(value: Any, default: str = "-") -> str:
    text = str(value or "").strip()
    return text or default


def _status_label(value: Any) -> str:
    return _text(value, "active").replace("_", " ").title()


def _render_report_css() -> None:
    st.markdown(
        """
        <style>
        .founder-report-table {
            width: 100%;
            border-collapse: collapse;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
            margin: 12px 0 18px;
        }
        .founder-report-table th,
        .founder-report-table td {
            padding: 14px 16px;
            border-bottom: 1px solid #eef2f7;
            color: #111827;
            text-align: left;
            vertical-align: top;
            font-size: 14px;
        }
        .founder-report-table th {
            background: #f8fafc;
            color: #475569;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: .04em;
            font-weight: 800;
        }
        .founder-report-table tr:last-child td {
            border-bottom: none;
        }
        .report-summary-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
            margin: 18px 0;
        }
        .report-summary-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        }
        .report-summary-card h4 {
            margin: 0 0 12px;
            color: #111827;
            font-size: 16px;
        }
        .report-pill-row {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            padding: 8px 0;
            border-top: 1px solid #f1f5f9;
            color: #334155;
            font-size: 14px;
        }
        .report-empty-state {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1e3a8a;
            padding: 18px 20px;
            border-radius: 16px;
            margin: 16px 0;
            font-weight: 600;
        }
        @media (max-width: 820px) {
            .report-summary-grid {
                grid-template-columns: 1fr;
            }
            .founder-report-table {
                display: block;
                overflow-x: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_summary_card(title: str, counts: Counter[str]) -> None:
    if not counts:
        body = '<div class="report-pill-row"><span>No data</span><strong>0</strong></div>'
    else:
        body = "".join(
            f'<div class="report-pill-row"><span>{escape(label)}</span><strong>{count}</strong></div>'
            for label, count in counts.most_common()
        )
    st.markdown(
        f"""
        <div class="report-summary-card">
            <h4>{escape(title)}</h4>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_institute_table(df: pd.DataFrame) -> None:
    headers = "".join(f"<th>{escape(str(column))}</th>" for column in df.columns)
    body = ""
    for row in df.to_dict(orient="records"):
        cells = "".join(f"<td>{escape(str(row.get(column, '-')))}</td>" for column in df.columns)
        body += f"<tr>{cells}</tr>"
    st.markdown(
        f"""
        <table class="founder-report-table">
            <thead><tr>{headers}</tr></thead>
            <tbody>{body}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_founder_reports() -> None:
    db_status_banner()
    _render_report_css()

    st.markdown("## Platform Reports")
    st.caption("Overview of institutes, teachers, students, subscriptions, and attendance.")

    from src.services.institute_service import _db

    db = _db()
    if not db:
        st.info("Connect Supabase to generate reports.")
        return

    institutes = _safe_fetch(
        db,
        "institutes",
        "id,name,city,state,admin_name,admin_email,plan,status,subscription_status,created_at",
        order_by="created_at",
        desc=True,
    )
    teachers_count = _count_rows(db, ["teachers"])
    students_count = _count_rows(db, ["students"])
    attendance_count = _count_rows(db, ["attendance_records", "attendance_sessions", "attendance"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Institutes", len(institutes))
    c2.metric("Teachers", teachers_count)
    c3.metric("Students", students_count)
    c4.metric("Attendance Records", attendance_count)

    if not institutes:
        st.markdown('<div class="report-empty-state">No institutes found yet. Reports will appear after institutes are created.</div>', unsafe_allow_html=True)
        return

    rows: list[dict[str, str]] = []
    for inst in institutes:
        rows.append(
            {
                "Institute": _text(inst.get("name")),
                "City": _text(inst.get("city")),
                "State": _text(inst.get("state")),
                "Admin": _text(inst.get("admin_name")),
                "Admin Email": _text(inst.get("admin_email")),
                "Plan": _text(inst.get("plan"), "Demo"),
                "Institute Status": _status_label(inst.get("status")),
                "Subscription": _status_label(inst.get("subscription_status")),
                "Created": _text(str(inst.get("created_at") or "")[:10]),
            }
        )

    df = pd.DataFrame(rows)
    plan_counts = Counter(row["Plan"] for row in rows)
    subscription_counts = Counter(row["Subscription"] for row in rows)

    st.markdown("### Summary")
    left, right = st.columns(2)
    with left:
        _render_summary_card("Institutes by Plan", plan_counts)
    with right:
        _render_summary_card("Institutes by Subscription", subscription_counts)

    st.markdown("### All Institutes")
    _render_institute_table(df)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv_bytes,
        file_name="snapclass_platform_report.csv",
        mime="text/csv",
    )
