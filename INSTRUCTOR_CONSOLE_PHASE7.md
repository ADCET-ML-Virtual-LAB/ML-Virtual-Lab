# Instructor Console — Phase 7 (backend foundation)

Backend only. No frontend change yet (Phase 8 builds the navbar, Home, Batches and batch workspace).

## What changed
- **One instructor per batch**: `instructor_assignments.batch_id` is now unique. `POST /batches/{id}/instructors`
  returns 409 if the batch already has a different instructor (same instructor again is a no-op).
- **Instructors only**: new `/instructor/*` API (see `openapi.yaml`). Admins and students get 403.
  The legacy `/dashboards/instructor` and `/dashboards/instructor/export` are now instructors-only too.
- **Data rules**: own batch only; published experiments only; saved assignment percentage shown immediately
  (reveal policy ignored); pre/post scores never returned; status uses the student tick rule.
- **CSV**: status CSV and assignment-scores CSV, each for the open experiment only.
- **Submission review**: per question — options with answer key, the student's choice, correct/incorrect.

## Files
New: `backend/app/routers/instructor.py`, `backend/app/schemas/instructor.py`,
`backend/scripts/migrate_one_instructor_per_batch.py`, `backend/tests/test_instructor_console.py`
Changed: `backend/app/models/batch.py`, `backend/app/routers/batches.py`, `backend/app/routers/dashboards.py`,
`backend/app/main.py`, `openapi.yaml`, `CLAUDE.md`

## Apply
```powershell
$repo = "D:\Virtual Lab\ML-Virtual-Lab"
$zip = "$env:USERPROFILE\Downloads\ML-Virtual-Lab-instructor-console-phase7-backend-patch.zip"
Expand-Archive -LiteralPath $zip -DestinationPath $repo -Force
cd "$repo\backend"
.\venv\Scripts\Activate.ps1
python -m scripts.migrate_one_instructor_per_batch
python -m pytest -q
```
The migration stops without changing anything if a batch already has two instructors.
