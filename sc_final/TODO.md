# TODO - Dropdown + SnapClass UI Audit (Blackbox AI)

## Phase 1: Class Management UI (confirmed)
- [x] Inspect `src/screens/institute_classes.py`
- [x] Add class dropdown conversion (class/section/academic year)

- [ ] Replace **Add Class** text inputs with dropdowns:
  - [ ] Class Name dropdown: 6-12 + JEE/NEET + Foundation/Dropper
  - [ ] Section dropdown: A-F
  - [x] Academic Year dropdown: 2025-26..2028-29 with default `2026-27`
- [ ] Update Add Class validations to use controlled values
- [ ] Replace Add Class button styling with SnapClass gradient
- [ ] Update Setup Progress Cards colors:
  - [ ] Done → Green
  - [ ] Pending → Orange
  - [ ] Incomplete → Red (derive based on missing setup items)

## Phase 2: Teacher Assignment UI
- [ ] Ensure Assign Teacher button uses SnapClass gradient
- [ ] Verify dropdown flow (Select Teacher/Class/Subject) correctness
- [ ] Add validation messages where needed

## Phase 3: Student Registration
- [ ] Add **Gender** dropdown
- [ ] Add **Section** dropdown (or confirm derived-from-class approach)
- [ ] Wire gender/section into `add_student` service call (if supported)
- [ ] Replace Add Student button styling with SnapClass gradient

## Phase 4: Attendance
- [ ] Add Date Range controls: Today / This Week / This Month / Custom
- [ ] Ensure Class + Section + Subject are controlled dropdowns

## Phase 5: Reports
- [ ] Add Date Range controls and filter attendance records
- [ ] Ensure export respects filters

## Phase 6: Global UI Consistency Audit
- [ ] Replace remaining red buttons with SnapClass gradient
- [ ] Standardize border radius (16px), input height (52px), dropdown height (52px)
- [ ] Focus/hover animations
- [ ] Modern searchable dropdowns where options > 10 (if applicable)

## Phase 7: Final report
- [ ] Produce audit report listing:
  - Current field
  - Recommended dropdown
  - Reason

