# TODO — Workspace import/Pylance problems

## Goal
Eliminate Pylance warnings in `sc_final/src/screens/founder_reports.py` for `streamlit` and `pandas` imports.

## Steps
- [ ] Update `founder_reports.py` to use safe/optional imports (so type checking doesn’t fail when deps aren’t installed).
- [ ] Provide a small runtime fallback that shows a clear Streamlit error if the missing dep is required at runtime.
- [ ] Run a quick `python -m py_compile` check on the edited file.

