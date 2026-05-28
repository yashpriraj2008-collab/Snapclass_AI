"""Face AI service using DeepFace embeddings + cosine similarity.

This file is intentionally standalone so UI pages can depend on it without
pulling in heavy imports at module import time.
"""

from __future__ import annotations

import base64
import importlib
import importlib.util
import io
import json
import os
import tempfile
from datetime import datetime
from typing import Any, Optional


# ----------------------------- availability -----------------------------

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    DEEPFACE_ERROR = None
except Exception as e:
    DeepFace = None
    DEEPFACE_AVAILABLE = False
    DEEPFACE_ERROR = repr(e)


def is_deepface_available() -> bool:
    """Return True if DeepFace and cv2 can be imported successfully."""
    try:
        return DEEPFACE_AVAILABLE and importlib.import_module("cv2") is not None
    except Exception:
        return False


def deepface_error_message() -> Optional[str]:
    """Return the real DeepFace import error message (if any)."""
    if DEEPFACE_AVAILABLE:
        return None
    return DEEPFACE_ERROR or "DeepFace could not load."


def _get_deepface():
    if not is_deepface_available():
        return None
    return DeepFace


def image_bytes_to_temp_file(image_bytes: bytes) -> str:
    """Write bytes to a temp file and return the path."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(image_bytes)
        return f.name


def _bytes_to_pil_np(image_bytes: bytes):
    from PIL import Image
    import numpy as np

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(img)


# ----------------------------- embeddings -----------------------------


def generate_face_embedding(image_bytes: bytes) -> tuple[Optional[list[float]], Optional[str]]:
    """Generate a single face embedding from image bytes.

    Uses DeepFace.represent() with the parameters required by the bugfix:
    - model_name="Facenet"
    - detector_backend="opencv"
    - enforce_detection=False
    """
    if not is_deepface_available():
        return (
            None,
            deepface_error_message()
            or "Real AI attendance requires DeepFace. Activate Python 3.11 venv and run: pip install deepface tf-keras tensorflow opencv-python-headless",
        )

    deepface_cls = _get_deepface()
    if deepface_cls is None:
        return None, "DeepFace could not load."

    temp_path: str | None = None
    try:
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            image.save(temp_file.name)
            temp_path = temp_file.name

        result = deepface_cls.represent(
            img_path=temp_path,
            model_name="Facenet",
            detector_backend="opencv",
            enforce_detection=False,
        )

        if not result or len(result) == 0:
            return None, "No face detected."

        embedding = result[0].get("embedding")
        if not embedding:
            return None, "Face embedding could not be generated."

        return [float(x) for x in embedding], None
    except Exception as e:
        return None, str(e)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass



def get_face_embedding(image_bytes: bytes) -> dict[str, Any]:
    """Generate a single face embedding for the given image."""
    embedding, error = generate_face_embedding(image_bytes)
    return {"ok": embedding is not None, "embedding": embedding, "error": error}


def get_current_student_identity(st) -> dict[str, Any]:
    """Extract the current student identity from Streamlit session_state.

    Returns keys used by the app:
      - student_id, user_id, user_email, user_name, roll_no, name

    This is intentionally defensive because different login flows may store
    different fields.
    """

    user = st.session_state.get("user", {}) or {}

    return {
        "student_id": (
            st.session_state.get("student_id")
            or user.get("student_id")
            or user.get("id")
        ),
        "user_id": (
            st.session_state.get("user_id")
            or user.get("user_id")
            or user.get("id")
        ),
        "user_email": (
            st.session_state.get("student_email")
            or st.session_state.get("user_email")
            or user.get("email")
        ),
        "user_name": (
            st.session_state.get("user_name")
            or user.get("name")
        ),
        "roll_no": (
            st.session_state.get("roll_no")
            or st.session_state.get("user_roll")
            or st.session_state.get("user_roll_no")
            or user.get("roll_no")
        ),
        "name": (
            st.session_state.get("name")
            or st.session_state.get("user_name")
            or user.get("name")
        ),
    }


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Cosine similarity in [-1, 1]."""
    import numpy as np

    a = np.array(vec1, dtype=float)
    b = np.array(vec2, dtype=float)

    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return -1.0
    return float(np.dot(a, b) / denom)


# ----------------------------- supabase persistence -----------------------------


def _get_supabase():
    try:
        from src.database.client import get_supabase

        return get_supabase()
    except Exception:
        return None


def check_face_enrolled(
    supabase,
    student_identity: dict[str, Any],
) -> tuple[bool, Any]:
    """Check if a face is enrolled in Supabase.

    Priority order (as requested):
      1) student_id
      2) user_email
      3) roll_no

    This is defensive against missing columns in some deployments.
    """
    if not supabase:
        return False, None

    student_id = student_identity.get("student_id")
    user_email = student_identity.get("user_email")
    roll_no = student_identity.get("roll_no")

    # Try each key in order. If a column doesn't exist, fall back to next.
    try:
        if student_id:
            try:
                result = (
                    supabase.table("face_embeddings")
                    .select("*")
                    .eq("student_id", student_id)
                    .limit(1)
                    .execute()
                )
                if result.data:
                    return True, result.data[0]
            except Exception:
                pass

        if user_email:
            try:
                result = (
                    supabase.table("face_embeddings")
                    .select("*")
                    .eq("user_email", user_email)
                    .limit(1)
                    .execute()
                )
                if result.data:
                    return True, result.data[0]
            except Exception:
                pass

        if roll_no:
            try:
                result = (
                    supabase.table("face_embeddings")
                    .select("*")
                    .eq("roll_no", roll_no)
                    .limit(1)
                    .execute()
                )
                if result.data:
                    return True, result.data[0]
            except Exception:
                pass

    except Exception as e:
        return False, {"error": repr(e)}

    return False, None


def save_face_embedding_to_supabase(
    supabase,
    student_identity: dict[str, Any],
    embedding: list[float],
) -> Any:
    """Save embedding into face_embeddings.

    Stores embedding as json.dumps(embedding) into text column.
    Re-checks Supabase after upsert to confirm the row exists.

    Uses student_id/user_email/roll_no if available, but remains compatible
    with the current schema (roll_no unique) by always storing roll_no.
    """
    if not supabase:
        raise RuntimeError("Supabase client unavailable.")

    student_id = student_identity.get("student_id")
    user_id = student_identity.get("user_id")
    user_email = student_identity.get("user_email")
    user_name = student_identity.get("user_name")
    name = student_identity.get("name")
    roll_no = student_identity.get("roll_no")

    payload: dict[str, Any] = {
        "student_id": student_id,
        "user_id": user_id,
        "user_email": user_email,
        "user_name": user_name,
        "name": user_name or name or "Student",
        "roll_no": roll_no or user_email or str(student_id) or "UNKNOWN",
        "embedding": json.dumps(embedding),
        "updated_at": datetime.utcnow().isoformat(),
    }

    payload = {k: v for k, v in payload.items() if v is not None}

    # Prefer upsert on student_id if available, else fall back to roll_no.
    on_conflict = "student_id" if payload.get("student_id") else "roll_no"

    try:
        db = supabase
        db.table("face_embeddings").upsert(payload, on_conflict=on_conflict).execute()

        # Re-query immediately to verify.
        # The helper already implements priority: student_id -> user_email -> roll_no.
        enrolled, row = check_face_enrolled(db, student_identity)
        if not enrolled:
            raise RuntimeError("Face embedding saved, but verification re-query failed.")

        return row
    except Exception as e:
        return {"error": repr(e)}



def _coerce_embedding(raw: Any) -> Optional[list[float]]:
    if raw is None:
        return None
    if isinstance(raw, list):
        try:
            return [float(x) for x in raw]
        except Exception:
            return None
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [float(x) for x in parsed]
        except Exception:
            return None
    return None


def load_face_embeddings_from_supabase(roll_no: Optional[list[str]] = None) -> list[dict[str, Any]]:
    """Load embeddings from public.face_embeddings.

    Note: this helper is used for cosine-similarity matching.
    It expects `embedding` stored as json text in the DB.
    """

    db = _get_supabase()
    if db is None:
        return []

    try:
        q = db.table("face_embeddings").select("roll_no,embedding,name")
        if roll_no:
            q = q.in_("roll_no", roll_no)
        rows = q.execute().data or []

        out: list[dict[str, Any]] = []
        for r in rows:
            emb = _coerce_embedding(r.get("embedding"))
            if emb is None:
                continue
            out.append({"roll": r.get("roll_no"), "name": r.get("name"), "embedding": emb})
        return out
    except Exception:
        return []



# ----------------------------- identification -----------------------------


def identify_matching_face(image_bytes: bytes, threshold: float = 0.38) -> dict[str, Any]:
    """Identify a matching enrolled face.


    Returns:
      {ok, match: bool, matched_roll: str|None, confidence: float, best_score: float, error}

    threshold is cosine similarity threshold.
    """
    if not is_deepface_available():
        return {
            "ok": False,
            "match": False,
            "matched_roll": None,
            "confidence": 0.0,
            "best_score": -1.0,
            "error": deepface_error_message() or "DeepFace could not load.",
        }

    emb_res = get_face_embedding(image_bytes)
    if not emb_res.get("ok"):
        return {
            "ok": False,
            "match": False,
            "matched_roll": None,
            "confidence": 0.0,
            "best_score": -1.0,
            "error": emb_res.get("error"),
        }

    live_emb = emb_res["embedding"]
    enrolled = load_face_embeddings_from_supabase()
    if not enrolled:
        return {
            "ok": False,
            "match": False,
            "matched_roll": None,
            "confidence": 0.0,
            "best_score": -1.0,
            "error": "No enrolled students found.",
        }

    best_roll: Optional[str] = None
    best_score = -1.0

    for s in enrolled:
        stored_emb = s.get("embedding")
        if stored_emb is None:
            continue
        score = cosine_similarity(live_emb, stored_emb)
        if score > best_score:
            best_score = score
            best_roll = s.get("roll")

    match = best_score >= threshold
    confidence = max(0.0, min(100.0, round((best_score + 1) * 50, 1)))

    return {
        "ok": True,
        "match": match,
        "matched_roll": best_roll,
        "confidence": confidence,
        "best_score": best_score,
        "error": None,
    }


def save_attendance_to_supabase(
    *,
    roll_no: str,
    subject: str,
    attendance_date: str,
    status: str,
    marked_by: Optional[str] = None,
) -> dict[str, Any]:
    """Insert attendance row into public.attendance.

    Status must match DB constraint; we default to lowercase: present/absent.
    """
    db = _get_supabase()
    if db is None:
        return {"ok": False, "error": "Supabase client unavailable."}

    try:
        payload: dict[str, Any] = {
            "roll_no": roll_no,
            "subject": subject,
            "attendance_date": str(attendance_date),
            "status": status,
        }
        if marked_by is not None:
            payload["marked_by"] = marked_by

        db.table("attendance").insert(payload).execute()
        return {"ok": True, "error": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}
