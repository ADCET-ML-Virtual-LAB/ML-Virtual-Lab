# Student Console Phase 2 — Pre-Quiz/Post-Quiz Best-Score-Only Storage

This patch is intended to be applied **on top of the Student Console Phase 1 patch** already applied to the repository.

## Changes included

- Adds `StudentQuizProgress`, storing one row per student and Pre-Quiz/Post-Quiz with:
  - `best_score`
  - a single `submitted_at` timestamp
  - no per-attempt rows and no saved answer history
- Updates quiz submission handling:
  - Pre-Quiz/Post-Quiz allow unlimited submissions.
  - Each submission can improve the saved best score but can never lower it.
  - The response returns the saved best score, not the score for the individual current attempt.
  - Per-question correctness is returned transiently for current-attempt feedback and is not saved for self-assessment quizzes.
  - Assignment submissions and answer records continue to be saved separately; the assignment remains one accepted submission only.
- Removes attempt counts and attempt-number text from student quiz responses/UI.
- Keeps assignment score visible immediately to the student after submission and when reopening the assignment.
- Updates student progress and assignment prerequisite checks to use the saved Pre-Quiz/Post-Quiz submitted state.
- Adds/updates tests for best-score-only storage, unlimited attempts, assignment one-attempt behaviour, student/instructor visibility, and progress/lock integration.

## Files included

- `backend/app/models/student_quiz_progress.py` — new database model
- `backend/app/models/__init__.py` — registers the new model
- `backend/app/models/quiz.py` — clarifies assignment-only use of `QuizSubmission`
- `backend/app/routers/quizzes.py` — saves best score only for pre/post, keeps assignment submission logic separate
- `backend/app/routers/experiments.py` — returns submitted/best-score/assignment-score state without attempt counts
- `backend/app/services/progress.py` — pre/post completion and locking read the new saved status
- `backend/app/schemas/quiz.py` — removes attempt-history fields from API schemas
- `frontend/src/components/QuizPanel.jsx` — removes attempt-number/attempt-score display and shows best score only
- `backend/scripts/migrate_quiz_best_score_only.py` — creates the new table if missing
- `backend/tests/test_quiz_rules_and_dashboards.py` — updates automated tests
- `CLAUDE.md` — aligns the project notes with the implemented rules

## Apply the patch

From PowerShell, use the repository root:

```powershell
cd "D:\Virtual Lab\ML-Virtual-Lab"
git status
```

Keep any existing Phase 1 changes. Download `ML-Virtual-Lab-student-console-phase2-quiz-best-score-patch.zip`, extract it directly into the repository root, and allow the matching files to merge/overwrite.

## Database migration

Make sure `backend\.env` points to your intended development database, then run from the backend directory with the project virtual environment activated:

```powershell
cd "D:\Virtual Lab\ML-Virtual-Lab\backend"
.\venv\Scripts\Activate.ps1
python -m scripts.migrate_quiz_best_score_only
```

The migration only creates `student_quiz_progress` if it does not exist. It does not drop tables or remove users, experiments, assignment submissions, or other application data. Since you confirmed there is no pre/post attempt history that needs preserving, there is no data-conversion step.

## Verification

Run backend tests:

```powershell
cd "D:\Virtual Lab\ML-Virtual-Lab\backend"
python -m pytest -q
```

Build the frontend:

```powershell
cd "D:\Virtual Lab\ML-Virtual-Lab\frontend"
npm run build
```

Then test manually:

1. Submit a Pre-Quiz with a low score. The saved best score should appear; no attempt number or per-attempt score should appear.
2. Retry and earn a higher score. The best score should update.
3. Retry and earn a lower score. The displayed best score should not decrease.
4. Refresh/reopen the experiment. The best score and submitted state should remain.
5. Repeat for Post-Quiz.
6. Confirm that these submissions create one `student_quiz_progress` row per student/quiz and no `quiz_submissions`/`quiz_answers` rows for Pre-Quiz/Post-Quiz.
7. Confirm Assignment remains one accepted submission with immediate student score visibility.
8. Confirm pre/post scores remain absent from instructor-facing responses.

## Notes

- The `attempt_number` database field still exists on `QuizSubmission` for the assignment submission table's existing schema; the application only writes an assignment row with `attempt_number=1`. It is no longer part of student quiz API responses or display, and it is not used to save Pre-Quiz/Post-Quiz attempts.
- The current-submission correctness data is returned only in the submission response for immediate visual feedback; it is not persisted as Pre-Quiz/Post-Quiz attempt history.
- The patch does not rebuild the navbar/sidebar/progress UI discussed for later phases.
