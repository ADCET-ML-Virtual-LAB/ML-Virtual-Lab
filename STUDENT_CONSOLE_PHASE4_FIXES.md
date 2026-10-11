# Student Console Phase 4 — Fixes before the navigation phase

No database migration is needed.

## What changed
- Code Exercise now shows its tick (and a saved "Completed" banner) after a matched result is saved; the state is restored on return/refresh/login.
- Clicking the Assignment always re-fetches the lock state from the backend first.
- Experiment status uses ticks only: Not started (no ticks), In progress (some ticks), Completed (all ticks incl. assignment). A failed/mismatched code attempt is no longer progress.
- Experiment numbers are fixed 1-10: required on create, unique (409 if reused), and ignored on update.
- CLAUDE.md, README.md and openapi.yaml brought up to date.

## Files
backend/app/services/progress.py, backend/app/schemas/experiment.py, backend/app/routers/experiments.py,
backend/tests/test_status_rules_and_code_tick.py (new), frontend/src/pages/ExperimentPage.jsx,
CLAUDE.md, README.md, openapi.yaml, STUDENT_CONSOLE_PHASE4_FIXES.md

## Apply
Extract into the repository root, replace matching files, then from `backend` run `python -m pytest -q` and from `frontend` run `npm run build`.
