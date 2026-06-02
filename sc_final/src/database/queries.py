"""
All database queries with automatic demo-data fallback.
Every function is safe: if Supabase fails → returns demo data, never crashes.
"""
from typing import Optional
import pandas as pd
from src.database.client import get_supabase
import src.services.demo_data as demo


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _df(data: list, fallback: pd.DataFrame) -> pd.DataFrame:
    """Convert Supabase result list to DataFrame, or return fallback."""
    if data:
        return pd.DataFrame(data)
    return fallback.copy()

def _safe(fn, fallback):
    """Run fn(); on any exception return fallback."""
    try:
        return fn()
    except Exception:
        return fallback


# ──────────────────────────────────────────────
# INSTITUTES
# ──────────────────────────────────────────────

def get_institutes() -> list:
    db = get_supabase()
    if db is None:
        return demo.INSTITUTES
    return _safe(
        lambda: db.table("institutes").select("*").order("name").execute().data or demo.INSTITUTES,
        demo.INSTITUTES
    )

def add_institute(name: str, city: str) -> dict:
    db = get_supabase()
    if db is None:
        return {"ok": True, "demo": True, "message": f"'{name}' saved locally (demo mode)."}
    try:
        db.table("institutes").insert({"name": name, "city": city}).execute()
        return {"ok": True, "demo": False, "message": f"✅ Institute '{name}' added to Supabase."}
    except Exception as e:
        return {"ok": False, "demo": True, "message": f"Supabase error: {e}"}

def delete_institute(inst_id: str) -> dict:
    db = get_supabase()
    if db is None:
        return {"ok": True, "demo": True, "message": "Deleted (demo mode)."}
    try:
        db.table("institutes").delete().eq("id", inst_id).execute()
        return {"ok": True, "demo": False, "message": "✅ Institute deleted."}
    except Exception as e:
        return {"ok": False, "message": f"Error: {e}"}


# ──────────────────────────────────────────────
# STUDENTS
# ──────────────────────────────────────────────

def get_students(class_name: Optional[str] = None) -> pd.DataFrame:
    """Return students DataFrame with columns used across the app.

    Screens expect: id (optional), roll, name, class_name, attendance, email.
    """
    db = get_supabase()
    if db is None:
        df = pd.DataFrame(demo.STUDENTS.copy())
        if class_name:
            return pd.DataFrame(df.loc[df["class_name"] == class_name])
        return pd.DataFrame(df)

    fallback = demo.STUDENTS
    return pd.DataFrame(_safe(lambda: _fetch_students(db, class_name), fallback))


def _fetch_students(db, class_name: Optional[str]):
    q = db.table("students").select("id,roll_no,name,email,class_name,created_at").order("name")
    if class_name:
        q = q.eq("class_name", class_name)
    data = q.execute().data
    if not data:
        return demo.STUDENTS.copy()

    df = pd.DataFrame(data).rename(columns={"roll_no": "roll"})

    # Ensure required columns exist for consistent UI rendering.
    if "attendance" not in df.columns:
        df["attendance"] = 0.0
    if "email" not in df.columns:
        df["email"] = ""
    if "class_name" not in df.columns:
        df["class_name"] = ""

    # Keep only what the UI uses.
    cols = [c for c in ["id", "roll", "name", "email", "class_name", "attendance"] if c in df.columns]
    return df[cols].copy()

def add_student(name: str, email: str, roll: str, class_name: str) -> dict:
    db = get_supabase()
    if db is None:
        return {"ok": True, "demo": True, "message": f"'{name}' saved (demo mode). Connect Supabase to persist."}
    try:
        db.table("students").insert({
            "name": name, "email": email, "roll_no": roll, "class_name": class_name
        }).execute()
        return {"ok": True, "demo": False, "message": f"✅ Student '{name}' added to Supabase."}
    except Exception as e:
        return {"ok": False, "demo": True, "message": f"Error: {e}"}

def delete_student(student_id: str) -> dict:
    db = get_supabase()
    if db is None:
        return {"ok": True, "demo": True, "message": "Deleted (demo mode)."}
    try:
        db.table("students").delete().eq("id", student_id).execute()
        return {"ok": True, "demo": False, "message": "✅ Student deleted."}
    except Exception as e:
        return {"ok": False, "message": f"Error: {e}"}


# ──────────────────────────────────────────────
# TEACHERS
# ──────────────────────────────────────────────

def get_teachers() -> pd.DataFrame:
    db = get_supabase()
    if db is None:
        return demo.TEACHERS.copy()
    return pd.DataFrame(
        _safe(
            lambda: _df(db.table("teachers").select("*").order("name").execute().data, demo.TEACHERS),
            demo.TEACHERS,
        )
    )

def add_teacher(name: str, email: str, subject: str, class_name: str = "") -> dict:
    db = get_supabase()
    if db is None:
        return {"ok": True, "demo": True, "message": f"'{name}' saved (demo mode)."}
    try:
        db.table("teachers").insert({
            "name": name, "email": email, "subject": subject, "class_name": class_name
        }).execute()
        return {"ok": True, "demo": False, "message": f"✅ Teacher '{name}' added to Supabase."}
    except Exception as e:
        return {"ok": False, "message": f"Error: {e}"}

def delete_teacher(teacher_id: str) -> dict:
    db = get_supabase()
    if db is None:
        return {"ok": True, "demo": True, "message": "Deleted (demo mode)."}
    try:
        db.table("teachers").delete().eq("id", teacher_id).execute()
        return {"ok": True, "demo": False, "message": "✅ Teacher deleted."}
    except Exception as e:
        return {"ok": False, "message": f"Error: {e}"}


# ──────────────────────────────────────────────
# SUBJECTS
# ──────────────────────────────────────────────

def get_subjects(class_name: Optional[str] = None) -> pd.DataFrame:
    db = get_supabase()
    if db is None:
        df = demo.SUBJECTS.copy()
        if class_name:
            return pd.DataFrame(df.loc[df["class_name"] == class_name])
        return df
    return pd.DataFrame(_safe(lambda: _fetch_subjects(db, class_name), demo.SUBJECTS))

def _fetch_subjects(db, class_name):
    q = db.table("subjects").select("id,name,class_name").order("name")
    if class_name:
        q = q.eq("class_name", class_name)
    data = q.execute().data
    if not data:
        return demo.SUBJECTS.copy()
    df = pd.DataFrame(data).rename(columns={"name": "subject"})
    df["teacher"]    = "—"
    df["total"]      = 40
    df["present"]    = 32
    df["attendance"] = 80.0
    return df

def add_subject(name: str, class_name: str, teacher_name: str = "") -> dict:
    db = get_supabase()
    if db is None:
        return {"ok": True, "demo": True, "message": f"'{name}' saved (demo mode)."}
    try:
        db.table("subjects").insert({"name": name, "class_name": class_name}).execute()
        return {"ok": True, "demo": False, "message": f"✅ Subject '{name}' added to Supabase."}
    except Exception as e:
        return {"ok": False, "message": f"Error: {e}"}


# ──────────────────────────────────────────────
# ATTENDANCE — WRITE
# ──────────────────────────────────────────────

def get_student_id(roll_no: str):
    db = get_supabase()
    if db is None:
        return None
    try:
        data = db.table("students").select("id").eq("roll_no", roll_no).execute().data
        return data[0]["id"] if data else None
    except Exception:
        return None

def get_subject_id(subject_name: str, class_name: Optional[str] = None):
    db = get_supabase()
    if db is None:
        return None
    try:
        q = db.table("subjects").select("id").eq("name", subject_name)
        if class_name:
            q = q.eq("class_name", class_name)
        data = q.execute().data
        return data[0]["id"] if data else None
    except Exception:
        return None

def save_attendance(records: list) -> dict:
    """
    records: list of {roll, subject, date, status, class_name(optional)}
    Tries Supabase first, falls back to session_state.
    """
    import streamlit as st
    db = get_supabase()

    if db is None:
        _save_session(records)
        return {"ok": True, "demo": True,
                "message": f"✅ {len(records)} records saved locally (demo mode). Connect Supabase to persist."}

    saved, errors = 0, []
    for rec in records:
        try:
            student_id = get_student_id(rec["roll"])
            subject_id = get_subject_id(rec["subject"], rec.get("class_name"))
            if not student_id or not subject_id:
                errors.append(f"{rec['roll']}: student or subject not found in DB")
                continue
            db.table("attendance").upsert({
                "student_id":      student_id,
                "subject_id":      subject_id,
                "attendance_date": rec["date"],
                "status":          rec["status"],
                "marked_by":       rec.get("marked_by", "teacher"),
            }, on_conflict="student_id,subject_id,attendance_date").execute()
            saved += 1
        except Exception as e:
            errors.append(str(e))

    if errors:
        _save_session(records)
        return {"ok": True, "demo": True,
                "message": f"⚠️ {saved} saved to Supabase. {len(errors)} error(s) — saved locally as backup."}
    return {"ok": True, "demo": False,
            "message": f"✅ {saved} attendance records saved to Supabase."}

def _save_session(records: list):
    import streamlit as st
    if "attendance_saved" not in st.session_state:
        st.session_state.attendance_saved = {}
    key = f"{records[0].get('subject','?')}_{records[0].get('date','?')}" if records else "batch"
    st.session_state.attendance_saved[key] = records


# ──────────────────────────────────────────────
# ATTENDANCE — READ
# ──────────────────────────────────────────────

def get_attendance_for_student(roll_no: str) -> pd.DataFrame:
    db = get_supabase()
    if db is None:
        return pd.DataFrame()
    try:
        sid = get_student_id(roll_no)
        if not sid:
            return pd.DataFrame()
        data = (
            db.table("attendance")
            .select("attendance_date,created_at,status,subjects(name)")
            .eq("student_id", sid)
            .order("attendance_date", desc=True)
            .limit(60)
            .execute().data
        )
        if not data:
            return pd.DataFrame()
        rows = []
        for r in data:
            subj = r.get("subjects") or {}
            attendance_date = r.get("attendance_date")
            if not attendance_date and r.get("created_at"):
                attendance_date = str(r.get("created_at"))[:10]
            rows.append(
                {
                    "Date": attendance_date,
                    "Subject": subj.get("name", "—"),
                    "Status": str(r.get("status", "")).capitalize(),
                }
            )
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

def get_attendance_for_class(class_name: Optional[str], subject_name: str, att_date: str) -> pd.DataFrame:
    """Get already-saved attendance for a class/subject/date."""
    if not class_name:
        return pd.DataFrame()
    db = get_supabase()
    if db is None:
        return pd.DataFrame()
    try:
        sid = get_subject_id(subject_name, class_name)
        if not sid:
            return pd.DataFrame()
        data = (
            db.table("attendance")
            .select("student_id,status,attendance_date,created_at,students(roll_no,name)")
            .eq("subject_id", sid)
            .execute().data
        )
        if not data:
            return pd.DataFrame()
        rows = []
        for r in data:
            row_date = r.get("attendance_date") or (str(r.get("created_at"))[:10] if r.get("created_at") else None)
            if att_date and row_date and str(row_date) != str(att_date):
                continue
            students = r.get("students") or {}
            if not students:
                continue
            rows.append(
                {
                    "roll": students.get("roll_no"),
                    "name": students.get("name"),
                    "status": r.get("status"),
                    "Date": row_date,
                }
            )
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

def get_attendance_stats_for_student(roll_no: str) -> dict:
    """Returns {total, present, absent, pct} from Supabase or demo."""
    db = get_supabase()
    if db is None:
        return {"total": 0, "present": 0, "absent": 0, "pct": 0}
    try:
        sid = get_student_id(roll_no)
        if not sid:
            return {"total": 0, "present": 0, "absent": 0, "pct": 0}
        data = db.table("attendance").select("status").eq("student_id", sid).execute().data or []
        total   = len(data)
        present = sum(1 for r in data if r["status"] == "present")
        absent  = total - present
        pct     = round(present / total * 100, 1) if total else 0
        return {"total": total, "present": present, "absent": absent, "pct": pct}
    except Exception:
        return {"total": 0, "present": 0, "absent": 0, "pct": 0}

def get_class_attendance_summary(class_name: Optional[str]) -> list:
    """Returns list of {name, roll, pct} for a class."""
    if not class_name:
        return []
    db = get_supabase()
    if db is None:
        return []
    try:
        data = (db.table("students")
                  .select("id,name,roll_no")
                  .eq("class_name", class_name)
                  .execute().data or [])
        results = []
        for s in data:
            att = db.table("attendance").select("status").eq("student_id", s["id"]).execute().data or []
            total   = len(att)
            present = sum(1 for r in att if r["status"] == "present")
            pct     = round(present / total * 100, 1) if total else 0
            results.append({"name": s["name"], "roll": s["roll_no"], "pct": pct})
        return results
    except Exception:
        return []

def _demo_attendance_history() -> pd.DataFrame:
    import random
    random.seed(42)
    dates    = pd.date_range("2025-01-06", periods=20, freq="B")
    subjects = ["Mathematics","Physics","Chemistry","English","Biology"]
    return pd.DataFrame({
        "Date":    [d.strftime("%d %b %Y") for d in dates],
        "Subject": [random.choice(subjects) for _ in dates],
        "Status":  ["Present" if random.random() > .2 else "Absent" for _ in dates],
    })


# ──────────────────────────────────────────────
# PLATFORM STATS (Admin dashboard)
# ──────────────────────────────────────────────

def get_platform_stats() -> dict:
    db = get_supabase()
    if db is None:
        return {"institutes": 3, "teachers": 4, "students": 8,
                "avg_attendance": 78.0, "demo": True}
    try:
        inst     = len(db.table("institutes").select("id").execute().data or [])
        teach    = len(db.table("teachers").select("id").execute().data   or [])
        stud     = len(db.table("students").select("id").execute().data   or [])
        att_data = db.table("attendance").select("status").execute().data or []
        total    = len(att_data)
        present  = sum(1 for r in att_data if r["status"] == "present")
        avg_att  = round(present / total * 100, 1) if total else 0.0
        return {"institutes": inst, "teachers": teach, "students": stud,
                "avg_attendance": avg_att, "demo": False}
    except Exception:
        return {"institutes": 0, "teachers": 0, "students": 0,
                "avg_attendance": 0.0, "demo": True}
