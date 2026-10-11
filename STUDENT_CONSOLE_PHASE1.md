# Student Console implementation — Phase 1

This patch implements the first backend-led increment of the approved Student Console requirements: persistent completion for static sections, database-driven ticks, inclusion of static sections in assignment prerequisites and progress calculation, the Title/Overview content field, and the click-triggered locked-assignment explanation in the current experiment UI.

It does **not** yet implement the final horizontal navbar/profile dropdown, the contextual left experiment sidebar, the final expandable View Progress page, the separate Assignment Scores page, or the revised single-record best-score-only quiz persistence. Those are follow-on increments; this patch deliberately keeps the existing route/layout structure while establishing the saved completion foundation.

## Apply the patch

1. Back up your working tree and database first. From PowerShell:

   ```powershell
   cd "D:\Virtual Lab\ML-Virtual-Lab"
   git status
   ```

   Commit or stash current edits if appropriate. Back up the database used by `backend/.env` before running the migration.

2. Extract the patch ZIP into the repository root:

   `D:\Virtual Lab\ML-Virtual-Lab`

   Allow files to merge into the existing `backend` and `frontend` folders and allow the included files to replace matching files. The ZIP paths are relative to the repository root.

3. Run the schema migration using the same Python environment and `.env` configuration as the backend:

   ```powershell
   cd "D:\Virtual Lab\ML-Virtual-Lab\backend"
   python -m scripts.migrate_student_section_tracking
   ```

   The script is safe to re-run. It adds `experiments.overview` when missing, creates `section_completions`, and fills empty overview fields with editable starter text. It uses the `DATABASE_URL` loaded by the backend; verify `.env` points to the intended development database before running it.

4. Start/restart the backend as you normally do. The frontend will read the new `section_completions` map from `GET /experiments/{slug}` and save via `POST /experiments/{slug}/sections/{section_key}/complete`.

5. Restart the frontend. No new frontend package is required for this patch.

## Included behaviour

- Static keys supported in this phase: `overview`, `aim-objectives`, `theory`, `video`, `guided-lab`.
- Completion records are unique per student, experiment and section; repeat clicks are idempotent.
- The frontend does not optimistically tick a section. It first saves through the API and then re-fetches the experiment; the tick comes only from the saved state returned by the backend.
- Save failure leaves the section unticked and displays an error.
- The assignment remains locked until all five static sections and all configured preceding assessment/code prerequisites are complete.
- The outstanding prerequisite list is shown only after the student clicks the locked Assignment entry.
- The Code Exercise remains complete if the database contains a matched submission, even if a later submission mismatches.
- The student progress API now includes `section_statuses`; instructor-facing response fields remain separately shaped and do not expose pre/post quiz scores.

## Validation notes

The updated backend suite passed in this environment (19 tests) using temporary test-only stubs for missing authentication libraries because package installation was unavailable. The stubs are not included in the patch and do not replace your project's real dependencies. Run the tests in your own project environment with the actual dependencies installed. A Vite build was not run because `frontend/node_modules` was not present and network package installation was unavailable here.
