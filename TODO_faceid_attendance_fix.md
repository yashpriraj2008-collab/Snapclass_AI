# TODO - FaceID attendance save error visibility fix

- [ ] Inspect student FaceID screen and identify Verify & Mark handler.
- [ ] Implement try/except around verification + attendance session creation + attendance_records upsert/insert.
- [ ] Add collapsed **Developer Debug** expander showing required fields + exact exception.
- [ ] Ensure user-facing error is exactly: "Attendance could not be saved. Please ask your teacher to mark manual attendance." (no internal details).
- [ ] Ensure success message: "Attendance marked successfully."
- [ ] Enforce face enrollment check + face could not be verified message.
- [ ] Run: `python -m compileall app.py src sc_final/src`.
- [ ] Run: `pip check`.
- [ ] Validate against checklist: no embedding → enroll message, enrolled student → can mark, duplicate prevention works, history/teacher dashboard reflect row.

