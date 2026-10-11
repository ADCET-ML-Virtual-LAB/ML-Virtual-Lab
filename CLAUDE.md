# CLAUDE.md

Context for anyone (human or AI) working on this repo. Read this before
making changes — it explains decisions that aren't obvious from the code
alone.

## What this is
A web-based ML Virtual Lab: ~10 classical ML experiments (no deep
learning), each with theory, a video, notes, a guided/parametric lab, a
free-form code editor, a pre-quiz, a post-quiz, and a graded assignment.
Linked from the university LMS but run as an independent app — its own
accounts, data, and hosting.

Three roles: **student** (self-enrolled by an instructor's upload, never
self-registers), **instructor** (created by Admin, scoped to their
assigned batches only), **admin** (the college dev team, full control).

## Tech stack
- **DB**: PostgreSQL, SQLAlchemy 2.0 (declarative, `Mapped[...]` style)
- **Backend**: FastAPI (Python), Pydantic v2 for schemas
- **Frontend**: React + Vite, Monaco editor, Pyodide (Python-in-WASM)
- **Auth**: JWT bearer tokens (no sessions, no refresh tokens — see below)

## Non-obvious decisions (don't "fix" these without discussing)

**Code execution is 100% client-side.** Student code runs in the browser
via Pyodide, inside a Web Worker. The backend never executes student code
and has no sandbox, no job queue, no Celery/Redis. `POST /code_submissions`
only *compares* the output the browser already computed against a hidden
expected answer (`ExperimentEvaluationSpec`, admin/instructor-only,
never serialized to a student-facing response). This is why the earlier
"Docker sandbox" design was dropped — don't reintroduce server-side
execution.

**No self-registration.** Students never create their own accounts.
An instructor (assigned to a batch) or Admin calls
`POST /batches/{batch_id}/students` with a list of emails/names. Each new
email gets a `User` with a random per-student password (`must_change_password
= True`) and a background email with that password
(`app/core/mailer.py`). Re-uploading the same list is idempotent — existing
emails are just enrolled if not already, never re-created or re-emailed.
`get_current_active_user` (in `app/core/deps.py`) blocks every endpoint
except login/me/change-password until the student has changed that default
password.

**No refresh tokens.** Access tokens are long-lived (`ACCESS_TOKEN_EXPIRE_MINUTES`,
default 8h) instead of the usual short-access + refresh-token pair. This is
a deliberate simplicity trade-off for a college project with modest
security requirements — revisit if that stops being true.

**Progress is derived from persisted activity records.** Manual static-section
completion is stored in `SectionCompletion`; pre/post quiz submitted status and
best score are stored in one `StudentQuizProgress` row per student/quiz; accepted
assignment submissions are stored in `QuizSubmission`; code-exercise results are
stored in `CodeSubmission`. Overall experiment progress is derived on read from
these records in `app/services/progress.py`. Guided Lab is tracked through the
same manual Mark Completed mechanism as other required static sections.

**IDs are UUIDs, not auto-increment ints** — avoids sequential IDs being
guessable/enumerable in a public-ish API.

**Roles are enforced with FastAPI dependencies, not decorators or
middleware**: `require_roles(UserRole.admin, ...)` in
`app/core/deps.py`. An instructor's batch-scoping (only their own assigned
batches) is checked per-endpoint, not just per-role — see
`_assert_can_manage_batch` in `app/routers/batches.py` as the pattern to
copy for any new instructor-facing, batch-scoped endpoint.

## Folder structure
```
backend/
  app/
    core/        # security.py (hashing/JWT), deps.py (auth deps), mailer.py
    models/      # SQLAlchemy ORM — one file per module's tables
    schemas/     # Pydantic request/response models — mirrors models/
    routers/     # one file per module; thin — logic stays in the router
                 # function for now (no service layer yet beyond mailer)
    config.py    # all env vars, one Settings object
    database.py  # engine/session/Base
    main.py      # FastAPI app + router registration
  scripts/       # one-off CLI scripts (create_admin.py, seeders)
  requirements.txt / requirements-dev.txt
frontend/
  src/
    pages/       # one file per route in App.jsx
    api/         # axios calls, one file per backend module
    editor/      # Monaco + Pyodide (client-side execution)
    components/  # shared UI (Layout, etc.)
```

## Conventions
- **Emails are always stored/compared lowercase.** Normalize at the
  boundary (schema or router), not scattered through business logic.
- **Passwords**: bcrypt via `app/core/security.py`'s `hash_password` /
  `verify_password`. Never log or return a plaintext password anywhere
  except the one background email at creation time.
- **Errors**: raise `HTTPException` with a plain-English `detail` string;
  don't leak which specific field/reason failed for auth endpoints (e.g.
  login returns the same 401 for "no such user" and "wrong password").
  Use 409 for uniqueness conflicts, 422 for validation, 403 for
  role/ownership failures, 404 for missing resources.
- **New tables** need: `UUIDPKMixin` + (usually) `TimestampMixin` from
  `app/models/common.py`, an entry in `app/models/__init__.py`'s
  `__all__`, and — until Alembic is added — a re-run of `init_db.py`
  against a *fresh* DB (it only does `create_all`, no migrations yet).
- **New endpoints**: add the Pydantic schema in `schemas/`, the route in
  the matching `routers/` file, and update `openapi.yaml` in the same PR
  — the spec is meant to stay accurate, not aspirational.
- **Background work** (anything that shouldn't block the response, like
  sending email) goes through FastAPI's `BackgroundTasks`, following the
  pattern in `routers/batches.py`'s `upload_students`.

## Running locally
```bash
docker compose up -d postgres
cd backend && pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
python init_db.py
python -m scripts.create_admin --email admin@college.edu --name "Admin" --password "ChangeMe123"
uvicorn app.main:app --reload
```
`EMAIL_ENABLED=false` (the `.env.example` default) prints generated
passwords to the console instead of sending mail — no SMTP needed for
local dev.

```bash
cd frontend && npm install && npm run dev
```

## Testing status
A pytest suite lives in `backend/tests` (SQLite test DB via `conftest.py`).
Run it from `backend` with the virtual environment active: `python -m pytest -q`.
It covers section completion, quiz best-score rules, assignment locking, status
rules, role access and the instructor dashboard. New endpoints should add tests
there and also be checked manually via `/docs`. The frontend has no automated
tests yet; `npm run build` is the minimum check.

## What's implemented vs. stub (keep this section updated)
- **Done**: auth (login/me/change-password), batches (create/list/get,
  student upload + onboarding email, instructor assignment), experiments
  (including their quizzes), quizzes (submit + assignment lock),
  code_submissions, dashboards (student, instructor, instructor CSV).
- `openapi.yaml` documents the intended design; its `x-status` markers can lag
  behind the code, so check the router file itself for what's actually live.

## Role and quiz rules (keep in sync with the code)
- **Roles**: student, instructor, admin. Students take quizzes, submit code and
  see their own progress. Instructors and admins only *view*: they cannot submit
  quizzes or code, and `/dashboards/student` is students-only (the frontend
  hides "My Progress" and redirects them to `/instructor`).
- **Instructor scope**: an instructor sees only their assigned batches
  (`GET /batches`, `GET /batches/{id}`, dashboard, CSV). Admins see all.
- **What instructors see**: per student and experiment, an overall badge (Not
  started / Ongoing / Completed) plus the assignment status and score. The CSV
  has only the assignment status and score. Pre/post quiz results never go to
  instructors, though completing them still counts toward the overall status.
- **Pre/post quizzes**: self-assessment, unlimited attempts. Persist one best-score
  record per student/quiz; do not store individual attempt or answer history. The
  student sees only the best score. Current-submission correctness may be returned
  transiently for immediate feedback.
- **Assignment**: one accepted submission only (409 on a second). Its score is
  visible to the submitting student immediately. It is locked, and its
  questions are hidden, until all required manual sections are marked complete,
  the pre-quiz and post-quiz are submitted, and the code exercise output *matches*
  the stored result (see
  `missing_assignment_prerequisites` in `app/services/progress.py`). The
  server enforces this; the UI only mirrors it. A step the experiment does not
  have (no quiz, or no expected result) is skipped.
- **Experiments are fixed (1-10)**: `order_index` is the experiment number. It must be
  1-10, unique, and cannot be changed after creation (the update schema ignores it).
- **Experiment status (ticks only)**: Not started = no section ticked in the database;
  In progress = at least one ticked but not all; Completed = every configured section
  ticked, including the assignment. A section is ticked when: manual sections have a
  saved `SectionCompletion`; a quiz is submitted at least once; the Code Exercise has a
  saved *matched* result (failed/mismatched attempts are not progress); the assignment
  has an accepted submission.
- **Assignment lock check**: the student UI re-fetches the experiment from the backend
  every time the Assignment is clicked; the server also re-checks on view and submit.
- **Overall progress (View Progress)**: completed sections / all configured sections across
  the published experiments, as a whole-number percentage (100% only when every section is
  complete). Per experiment only the status is shown (Not Attempted / In Progress /
  Completed), plus the list of sections with an empty/filled circle.
- **Assignment Scores page**: exactly three columns (Experiment No., Experiment Name,
  Assignment Score). Cell = score %, "Not Submitted", or "Assignment not Available" when
  the experiment has no assignment.
- **Submitted assignment review**: after submitting, the student can reopen the assignment
  and see each question with the correct answer, their own answer and Correct/Incorrect.
  `my_review` is returned only to the submitting student and only after submission.

