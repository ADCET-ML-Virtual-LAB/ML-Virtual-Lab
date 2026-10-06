# ML Virtual Lab — Base Commit

## What changed from the original design doc
Code execution is now **fully client-side**: student code runs in the
browser (Monaco editor + Pyodide, a Python-in-WASM runtime, inside a Web
Worker). The backend never executes student code, so **Celery, Redis, and
the Docker sandbox are removed from the stack** — the server only stores
submissions and does a cheap comparison of the *output the browser already
computed* against a hidden expected result (`ExperimentEvaluationSpec`).
This keeps the "answer key" secret without the server bearing any execution
load. See `backend/app/models/code_submission.py` for the reasoning.

Everything else from the design doc (auth, batches, content, quizzes,
guided lab, dashboards) is unchanged in scope.

## Stack
- **DB**: PostgreSQL
- **Backend**: FastAPI + SQLAlchemy 2.0 (models in `backend/app/models/`)
- **Frontend**: React (Vite) + Monaco + Pyodide

## Local setup
```bash
# 1. Postgres
docker compose up -d postgres

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # edit DATABASE_URL / JWT_SECRET_KEY if needed
python init_db.py           # creates all tables
python -m scripts.create_admin --email admin@college.edu --name "Admin" --password "Admin@123"
uvicorn app.main:app --reload

# 3. Frontend
cd ../frontend
npm install
npm run dev
```
Backend: http://localhost:8000/docs · Frontend: http://localhost:5173

## Pre-commit (run once per clone, in repo root)
```bash
pip install -r backend/requirements-dev.txt
pre-commit install
```
From then on, every `git commit` auto-runs formatting/lint (ruff for Python,
Prettier for JS) and basic hygiene checks (no committed secrets, no giant
files, valid YAML/JSON). To run it manually against everything: `pre-commit run --all-files`.

## Auth & student onboarding
There is no self-registration. An instructor (assigned to a batch) or Admin
calls `POST /batches/{batch_id}/students` with a list of
`{email, full_name, roll_number}`. For each new email this:
- creates a `User` (role=student, `must_change_password=True`) with a
  random per-student password,
- enrolls them in the batch,
- emails them that password in the background (`app/core/mailer.py`).

With `EMAIL_ENABLED=false` (the `.env.example` default) nothing is actually
sent — the password is written to the backend console instead, so you can
log in locally without setting up SMTP.

Every student's first login returns `must_change_password: true`; the
frontend should route them straight to `POST /auth/change-password` and
block everything else until it's `false` (`get_current_active_user` in
`app/core/deps.py` enforces this server-side).

## Database schema
14 tables, grouped by module — see `backend/app/models/`:
- **Auth**: `users`, `refresh_tokens`
- **Batches**: `batches`, `enrollments`, `instructor_assignments`, `roster_entries`
- **Content**: `experiments`, `experiment_evaluation_specs`
- **Quiz engine**: `quizzes`, `questions`, `options`, `quiz_submissions`, `quiz_answers`
- **Code exercises**: `code_submissions`

All tables use UUID primary keys and `created_at`/`updated_at` timestamps
(via `models/common.py` mixins). Verified importable with SQLAlchemy — run
`python init_db.py` against a real Postgres to create them.

## Suggested issues (one per teammate to start)
See `ISSUES.md` for the four starter issues, written ready to paste into
GitHub (title + body each).

## Open decisions (unchanged from design doc, still TBD)
- Assignment result reveal timing — `Quiz.reveal_policy` field exists
  (`immediate` / `after_deadline`), default is `immediate`.
- Hosting platform for Postgres + backend in production.

## Follow-up (not in this base commit)
- Alembic migrations (currently using `init_db.py`'s `create_all`, fine
  until the schema needs to evolve without dropping data).
- CI (lint/test) pipeline.
