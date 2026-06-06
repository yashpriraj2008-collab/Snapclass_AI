# Workspace import fixes (Pylance)

## Diagnostics addressed
- `sc_final/src/services/payment_service.py`
  - Pylance: `Import "streamlit" could not be resolved`
  - Pylance: `Import "razorpay" could not be resolved`
  - Pylance: `"os" is not defined`

## Planned fixes
1. Update `sc_final/src/services/payment_service.py`
   - Add missing `import os`
   - Guard optional third-party imports (`streamlit`, `razorpay`) with `TYPE_CHECKING` / local imports so Pylance is not blocked.
2. Update `sc_final/requirements.txt` (if missing)
   - Ensure `streamlit` and `razorpay` are present.
3. Run a quick `python -m compileall` to ensure no syntax errors.

