# Instructor console: downloads are now Excel (.xlsx)

Both instructor downloads (Students Status and Assignment Status) are Excel files instead of CSV.

- Top of the sheet, each in a merged row across the table width: Batch, Academic Year, Experiment No.,
  Experiment Name.
- Below a blank row, a bold header row and one row per student: URN, Student Name, Status
  (or Marks (%) for assignments; the marks are numbers, "Not Submitted" is text).
- Column widths: URN 16, Student Name 40, Status / Marks 22. Header row is frozen.
- Text cells are always stored as text, so a name starting with `=` is never treated as a formula.
- File names: `batch_<name>_<year>_experiment_<n>_status.xlsx` and `..._assignment_scores.xlsx`.
- Still limited to the open experiment or assignment, for the instructor's own batch only.

New dependency: `openpyxl==3.1.5` (in `backend/requirements.txt`).

## Files
New: `backend/app/services/exports.py`
Changed: `backend/app/routers/instructor.py`, `backend/requirements.txt`, `backend/tests/test_instructor_console.py`,
`frontend/src/utils/download.js`, `frontend/src/pages/InstructorExperimentStatus.jsx`, `openapi.yaml`, `CLAUDE.md`
