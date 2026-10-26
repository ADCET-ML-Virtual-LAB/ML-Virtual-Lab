# Student Console Phase 3 — Quiz Start Screen, Attempt Score and Completion Tick

This patch builds on the previously applied Student Console Phase 1 and Phase 2 patches. It does not add a database table and does not require a database migration.

## Behaviour implemented

- Student Pre-Quiz and Post-Quiz tabs open an introduction screen first, not the questions.
- The introduction shows the quiz type, experiment number, experiment title, saved best score (or `Not attempted`) and a `Start Now` button.
- The questions appear only after `Start Now` is clicked.
- A successful submission response returns the score for that specific attempt as transient response data, plus the saved best score. Pre-/post-quiz attempt scores and selected answers are not saved as attempt-history records.
- The result screen shows `This attempt` and `My best score` together.
- `Try Again` returns to the introduction, so starting another attempt requires `Start Now` again.
- Navigating away from a quiz or refreshing the page discards the transient attempt result. Returning to the quiz shows its start screen with only the saved best score.
- After a successful submission, the frontend re-fetches the experiment from the backend. The Pre-Quiz/Post-Quiz tick is rendered from the refreshed `my_submitted` value returned from the saved database state. No tick is added from the submit click alone.
- If submission fails, no new completion tick appears. If submission succeeds but the subsequent refresh fails, the current attempt result is still shown with a warning that saved progress could not be refreshed.
- The same `QuizPanel` behaviour applies to Pre-Quiz and Post-Quiz.
- Assignment submission behaviour remains separate and retains its one-attempt rule.

## Files in this patch

- `backend/app/routers/quizzes.py`
- `backend/app/schemas/quiz.py`
- `backend/tests/test_quiz_rules_and_dashboards.py`
- `frontend/src/components/QuizPanel.jsx`
- `frontend/src/components/QuizPanel.css`
- `frontend/src/pages/ExperimentPage.jsx`

## Apply

1. Extract this ZIP into the repository root `D:\Virtual Lab\ML-Virtual-Lab`, allowing the included paths to merge and replace matching files.
2. No database migration is required for this patch.
3. From `backend` with the project's virtual environment active, run `python -m pytest -q`.
4. From `frontend`, run `npm run build`.
5. In the browser, test a configured Pre-Quiz and Post-Quiz: initial introduction, Start Now, attempt score plus best score after submission, tick after the experiment detail refresh, Retry returning to the introduction, and best score only after navigating away and returning or refreshing.

## Validation note

The backend test suite passed 20 tests in the patch-building environment using temporary compatibility stubs for dependencies unavailable in that environment. Those stubs are not included. A frontend production build could not be run here because npm dependency downloads failed due to unavailable network/DNS access; please run the build in the project's configured development environment.
