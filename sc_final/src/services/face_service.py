"""
Face Recognition Service — Phase 3
Uses DeepFace for embedding + matching.
SAFE: If any import or model fails, all functions return graceful error dicts.
Never crashes the app.
"""


from __future__ import annotations
import io
import base64
import importlib.util
import numpy as np
from typing import Optional


# ── Lazy availability guard ───────────────────────────────────────────────
# Use find_spec so Pylance doesn't require the packages to be installed.
_deepface_available = False
_cv2_available = False

def _check_imports():
    global _deepface_available, _cv2_available
    _deepface_available = importlib.util.find_spec("deepface") is not None
    _cv2_available = importlib.util.find_spec("cv2") is not None


def _get_deepface():
    """
    Returns DeepFace class if available, otherwise None.
    Uses importlib to avoid static imports that Pylance can't resolve.
    """
    if not _deepface_available:
        return None
    try:
        module = importlib.import_module("deepface")
        return getattr(module, "DeepFace", None)
    except Exception:
        return None

_check_imports()


# ── Helpers ────────────────────────────────────────────────────────────────

def _pil_to_np(pil_img) -> np.ndarray:
    import numpy as np
    return np.array(pil_img.convert("RGB"))

def _bytes_to_np(raw: bytes) -> np.ndarray:
    from PIL import Image
    img = Image.open(io.BytesIO(raw))
    return _pil_to_np(img)

def _np_to_b64(arr: np.ndarray) -> str:
    from PIL import Image
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()

def is_face_ai_available() -> bool:
    return _deepface_available and _cv2_available


# ── Image quality & liveness (Phase 3 helpers) ──

def check_image_quality(image_bytes: bytes) -> dict:
    """Check if image is good enough for face detection.

    Returns: {ok: bool, message: str}

    Note: best-effort only. If PIL is unavailable/unreadable, returns ok=True.
    """
    try:
        from PIL import Image, ImageStat
        import io

        img = Image.open(io.BytesIO(image_bytes)).convert("L")  # grayscale
        stat = ImageStat.Stat(img)
        brightness = float(stat.mean[0])

        if brightness < 40:
            return {"ok": False, "message": "Image too dark. Move to better lighting."}
        if brightness > 230:
            return {"ok": False, "message": "Image too bright. Reduce glare."}
        return {"ok": True, "message": "Image quality good"}
    except Exception:
        return {"ok": True, "message": "Could not check quality"}


def basic_liveness_check(image_bytes: bytes) -> dict:
    """Basic liveness placeholder.

    Current behavior (best-effort): ensure a face is detected and the embedding
    can be extracted with confident detection.

    Returns: {ok: bool, message: str}
    """
    try:
        if not _deepface_available:
            return {"ok": False, "message": "DeepFace not installed."}

        deepface_cls = _get_deepface()
        if deepface_cls is None:
            return {"ok": False, "message": "DeepFace not installed."}

        # Use strict detection to reduce false positives.
        _ = deepface_cls.represent(
            img_path=_bytes_to_np(image_bytes),
            model_name="Facenet",
            enforce_detection=True,
            detector_backend="opencv",
        )

        return {"ok": True, "message": "Liveness check passed"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


# ── Embedding ──


def get_embedding(image_bytes: bytes) -> dict:
    """
    Extract face embedding from image bytes.
    Returns: {ok, embedding (list[float]), error}
    """
    if not _deepface_available:
        return {"ok": False, "embedding": None,
                "error": "DeepFace not installed. Run: pip install deepface tf-keras"}

    deepface_cls = _get_deepface()
    if deepface_cls is None:
        return {"ok": False, "embedding": None,
                "error": "DeepFace not installed."}
    try:
        img = _bytes_to_np(image_bytes)
        result = deepface_cls.represent(
            img_path=img,
            model_name="Facenet",
            enforce_detection=True,
            detector_backend="opencv",
        )
        embedding = result[0]["embedding"]
        return {"ok": True, "embedding": embedding, "error": None}
    except Exception as e:
        return {"ok": False, "embedding": None,
                "error": f"Face not detected or model error: {e}"}


def get_embedding_relaxed(image_bytes: bytes) -> dict:
    """Same but with enforce_detection=False — better for selfies/uploads."""
    if not _deepface_available:
        return {"ok": False, "embedding": None,
                "error": "DeepFace not installed."}

    deepface_cls = _get_deepface()
    if deepface_cls is None:
        return {"ok": False, "embedding": None,
                "error": "DeepFace not installed."}
    try:
        img = _bytes_to_np(image_bytes)
        result = deepface_cls.represent(
            img_path=img,
            model_name="Facenet",
            enforce_detection=False,
            detector_backend="opencv",
        )
        embedding = result[0]["embedding"]
        return {"ok": True, "embedding": embedding, "error": None}
    except Exception as e:
        return {"ok": False, "embedding": None, "error": str(e)}


# ── Verification (1:1) ─────────────────────────────────────────────────────

def verify_faces(img1_bytes: bytes, img2_bytes: bytes,
                 threshold: float = 0.6) -> dict:
    """
    Compare two face images.
    Returns: {ok, match (bool), distance (float), confidence_pct, error}
    """
    if not _deepface_available:
        return {"ok": False, "match": False, "distance": 1.0,
                "confidence_pct": 0, "error": "DeepFace not installed."}

    deepface_cls = _get_deepface()
    if deepface_cls is None:
        return {"ok": False, "match": False, "distance": 1.0,
                "confidence_pct": 0, "error": "DeepFace not installed."}
    try:
        img1 = _bytes_to_np(img1_bytes)
        img2 = _bytes_to_np(img2_bytes)
        result = deepface_cls.verify(
            img1_path=img1,
            img2_path=img2,
            model_name="Facenet",
            enforce_detection=False,
        )
        distance = result["distance"]
        match = result["verified"]
        confidence_pct = round(max(0, (1 - distance) * 100), 1)
        return {
            "ok": True,
            "match": match,
            "distance": round(distance, 4),
            "confidence_pct": confidence_pct,
            "error": None,
        }
    except Exception as e:
        return {"ok": False, "match": False, "distance": 1.0,
                "confidence_pct": 0, "error": str(e)}


def compare_embedding(embedding: list[float],
                      stored_embedding: list[float],
                      threshold: float = 0.6) -> dict:
    """
    Compare a live embedding against a stored one using cosine similarity.
    Returns: {match, distance, confidence_pct}
    """
    try:
        a = np.array(embedding)
        b = np.array(stored_embedding)
        cosine   = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
        distance = round(1 - cosine, 4)
        match    = distance < threshold
        conf     = round(max(0, cosine * 100), 1)
        return {"match": match, "distance": distance, "confidence_pct": conf}
    except Exception as e:
        return {"match": False, "distance": 1.0, "confidence_pct": 0, "error": str(e)}


# ── Multi-face detection (class photo) ────────────────────────────────────

def detect_faces_in_class_photo(image_bytes: bytes) -> dict:
    """
    Detect and extract all faces from a class group photo.
    Returns: {ok, faces: list[{face_img_b64, bbox}], count, error}
    """
    if not _deepface_available or not _cv2_available:
        return {"ok": False, "faces": [], "count": 0,
                "error": "DeepFace / OpenCV not installed."}

    deepface_cls = _get_deepface()
    if deepface_cls is None:
        return {"ok": False, "faces": [], "count": 0,
                "error": "DeepFace not installed."}
    try:
        img_np = _bytes_to_np(image_bytes)

        face_objs = deepface_cls.extract_faces(
            img_path=img_np,
            detector_backend="opencv",
            enforce_detection=False,
        )

        faces = []
        for fo in face_objs:
            face_arr = fo["face"]                       # already cropped numpy array
            face_arr = (face_arr * 255).astype(np.uint8) if face_arr.max() <= 1 else face_arr
            bbox     = fo.get("facial_area", {})
            b64      = _np_to_b64(face_arr)
            faces.append({"face_img_b64": b64, "bbox": bbox})

        return {"ok": True, "faces": faces, "count": len(faces), "error": None}
    except Exception as e:
        return {"ok": False, "faces": [], "count": 0, "error": str(e)}


def match_faces_to_students(class_photo_bytes: bytes,
                             student_embeddings: list[dict],
                             threshold: float = 0.55) -> dict:
    """
    Match detected faces in class photo against stored student embeddings.
    student_embeddings: [{roll, name, embedding}]
    Returns: {ok, matched: [{roll,name,confidence_pct,matched}], unmatched_count, error}
    """
    if not _deepface_available:
        return {"ok": False, "matched": [], "unmatched_count": 0,
                "error": "DeepFace not installed."}

    deepface_cls = _get_deepface()
    if deepface_cls is None:
        return {"ok": False, "matched": [], "unmatched_count": 0,
                "error": "DeepFace not installed."}
    try:
        img_np = _bytes_to_np(class_photo_bytes)

        face_objs = deepface_cls.extract_faces(
            img_path=img_np,
            detector_backend="opencv",
            enforce_detection=False,
        )

        results    = {s["roll"]: {"roll": s["roll"], "name": s["name"],
                                   "confidence_pct": 0, "matched": False}
                      for s in student_embeddings}
        unmatched  = 0

        for fo in face_objs:
            face_arr = fo["face"]
            face_arr = (face_arr * 255).astype(np.uint8) if face_arr.max() <= 1 else face_arr
            try:
                rep = deepface_cls.represent(
                    img_path=face_arr,
                    model_name="Facenet",
                    enforce_detection=False,
                )
                live_emb = rep[0]["embedding"]
            except Exception:
                unmatched += 1
                continue

            best_roll, best_conf = None, 0
            for s in student_embeddings:
                if s.get("embedding") is None:
                    continue
                cmp = compare_embedding(live_emb, s["embedding"], threshold)
                if cmp["match"] and cmp["confidence_pct"] > best_conf:
                    best_conf = cmp["confidence_pct"]
                    best_roll = s["roll"]

            if best_roll:
                results[best_roll]["matched"]        = True
                results[best_roll]["confidence_pct"] = best_conf
            else:
                unmatched += 1

        return {"ok": True, "matched": list(results.values()),
                "unmatched_count": unmatched, "error": None}
    except Exception as e:
        return {"ok": False, "matched": [], "unmatched_count": 0, "error": str(e)}


# ── Embedding security helpers (Phase 3) ──


def encrypt_embedding(embedding: list[float]) -> str:
    """Best-effort encoding of embeddings for storage.

    This is NOT strong encryption; it only base64-wraps the JSON payload.
    Production should replace with real encryption (e.g., AES-GCM via KMS).
    """
    import json

    data = json.dumps(embedding, separators=(",", ":"))
    return base64.b64encode(data.encode("utf-8")).decode("utf-8")


def decrypt_embedding(encoded: str) -> list[float]:
    import json

    data = base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
    return json.loads(data)


# ── Supabase embedding store helpers ──


def save_face_embedding_db(roll: str, embedding: list[float], name: str | None = None) -> dict:
    """Store embedding in Supabase face_embeddings table.

    If `name` is provided, we also store it (optional). This keeps
    load_face_embeddings_db() resilient across deployments.
    """
    try:
        from src.database.client import get_supabase
        import json
        db = get_supabase()
        payload = {
            "roll_no": roll,
            # Store encrypted/encoded embedding payload.
            "embedding": encrypt_embedding(embedding),
        }

        if name is not None:
            payload["name"] = name

        if db is None:
            _save_embedding_session(roll, embedding)
            return {"ok": True, "demo": True,
                    "message": "Embedding saved locally (demo mode)."}

        db.table("face_embeddings").upsert(
            payload,
            on_conflict="roll_no"
        ).execute()
        return {"ok": True, "demo": False, "message": "✅ Face embedding saved to Supabase."}
    except Exception as e:
        _save_embedding_session(roll, embedding)
        return {"ok": True, "demo": True, "message": f"Saved locally. DB error: {e}"}


def _save_embedding_session(roll: str, embedding: list[float]):
    import streamlit as st
    if "face_embeddings" not in st.session_state:
        st.session_state.face_embeddings = {}
    st.session_state.face_embeddings[roll] = embedding

def load_face_embeddings_db(rolls: Optional[list[str]] = None) -> list[dict]:
    """Load embeddings from Supabase or session_state."""
    try:
        from src.database.client import get_supabase
        import json, streamlit as st
        db = get_supabase()
        if db is None:
            stored = st.session_state.get("face_embeddings", {})
            if rolls:
                return [{"roll": r, "embedding": stored[r]}
                        for r in rolls if r in stored]
            return [{"roll": r, "embedding": e} for r, e in stored.items()]
        q = db.table("face_embeddings").select("roll_no,embedding,name")

        if rolls:
            q = q.in_("roll_no", rolls)
        data = q.execute().data or []
        result = []
        for row in data:
            try:
                emb_raw = row.get("embedding")
                if isinstance(emb_raw, str):
                    # Backward compatible: try decrypt first; if that fails, treat as plain JSON.
                    try:
                        emb = decrypt_embedding(emb_raw)
                    except Exception:
                        emb = json.loads(emb_raw)
                else:
                    emb = emb_raw

                result.append({"roll": row["roll_no"], "name": row.get("name",""), "embedding": emb})
            except Exception:
                pass
        return result
    except Exception:
        return []
