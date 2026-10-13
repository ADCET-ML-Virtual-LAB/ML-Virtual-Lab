# ML Virtual Lab

A web-based virtual lab for Machine Learning experiments. Students work through experiments (overview,
aim, quizzes, video, theory, guided lab, code exercise, assignment). Instructors follow their batch's
experiment status and assignment results. Admins manage the system.

Linked from the university LMS but run as an independent app with its own accounts and data.

## Roles
| Role | What they can do today |
|---|---|
| **Student** | Home, Experiments, View Progress (with Assignment Scores), Profile. Completes experiments and submits quizzes, code and assignments. |
| **Instructor** | Home, Batches, Profile. For their own batch: student list, read-only experiment content with answer keys, Students Status, Assignment Status, submission review, Excel downloads. |
| **Admin** | The admin panel from the original build (batches, instructors, experiments). The final admin console is still to be designed (see Pending work). |

Students never register themselves. See "Auth and student onboarding" below.

## Stack
- **Database**: PostgreSQL
- **Backend**: FastAPI + SQLAlchemy 2.0 (models in `backend/app/models/`), Pydantic v2, openpyxl for Excel downloads
- **Frontend**: React (Vite), Monaco editor, Pyodide (Python in the browser)

Student code runs fully in the browser (Monaco + Pyodide in a Web Worker). The backend never executes
student code. It stores the output the browser computed and compares it with a hidden expected result
(`ExperimentEvaluationSpec`). See `backend/app/models/code_submission.py`.

## Local setup
```bash
# 1. Postgres
docker compose up -d postgres

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate      # Windows: .\venv\Scripts\Activate.ps1
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

## Seed data (development)
```bash
cd backend
source venv/bin/activate
export PYTHONPATH=.
python scripts/seed_experiments.py     # 10 experiments with demo content
python scripts/seed_data.py            # admin, instructors, students, batches
python -m scripts.load_linear_regression   # real content for experiment 8 (see below)
```
Seed credentials created by `seed_data.py`:
- Admin: `admin@college.edu` / `AdminPass123!`
- Instructors: `instructor1@college.edu` to `instructor5@college.edu` / `InstPass123!`
- Students: `student1@college.edu` to `student15@college.edu` / `StudPass123!`

Seeded students have `must_change_password=False` so you can log in immediately.

### Experiment content
- `seed_experiments.py` creates the ten experiments with demo content.
- `scripts/load_linear_regression.py` replaces the demo experiment numbered 8 with the Linear Regression
  experiment (overview, aim, objectives, video, theory with references, Pre-Quiz, Post-Quiz and Assignment
  of 10 questions each, and the Code Exercise with its hidden expected result). The text is in
  `scripts/linear_regression_content.py`; edit it and re-run the loader. Other experiments are not touched.
- The Code Exercise dataset file lives in `frontend/public/datasets/` (`Salary_dataset.csv`) and is served by the app.
  The code runner copies it into the browser's Python environment, so students read it with
  `pd.read_csv("Salary_dataset.csv")`.

## Upgrading an existing database
`init_db.py` creates all tables for a new database. For a database created earlier, run the one-off
scripts that apply (each is safe to re-run), from `backend/` with the virtualenv active:
```bash
python -m scripts.migrate_student_section_tracking   # section_completions table, experiments.overview
python -m scripts.migrate_quiz_best_score_only       # student_quiz_progress table
python -m scripts.migrate_one_instructor_per_batch   # one instructor per batch (stops if a batch has two)
python -m scripts.migrate_code_problem_statement     # experiments.code_problem_statement
python -m scripts.migrate_code_dataset_url           # experiments.code_dataset_url
```
There is no automated migration tool; schema changes are applied with these scripts.

## Tests and checks
```bash
cd backend && python -m pytest -q       # backend test suite (SQLite test database)
cd frontend && npm run build            # frontend build check (there are no frontend tests yet)
```

## Pre-commit (run once per clone, in repo root)
```bash
pip install -r backend/requirements-dev.txt
pre-commit install
```
Every `git commit` then runs formatting/lint (ruff for Python, Prettier for JS) and basic hygiene checks.
Run it manually with `pre-commit run --all-files`.

## Auth and student onboarding
There is no self-registration. An instructor assigned to a batch, or an admin, calls
`POST /batches/{batch_id}/students` with a list of `{email, full_name, roll_number}`. For each new email this
creates a student (`must_change_password=True`) with a random password, enrolls them in the batch and emails
the password in the background (`app/core/mailer.py`). With `EMAIL_ENABLED=false` (the `.env.example`
default) the password is printed to the backend console instead.

A student's first login goes to the change-password page; the server blocks every other endpoint until the
password is changed (`get_current_active_user` in `app/core/deps.py`).

Login tokens are long-lived JWTs stored in the browser; there are no refresh tokens or server-side sessions.

## What is built
**Student console** (details: `docs/STUDENT_CONSOLE.md`)
- Navbar: Home, Experiments, View Progress, profile menu (My Profile, Log out)
- Experiments page and an experiment page with a left sidebar of sections, each marked with an empty or filled circle
- Section completion saved in the database (Mark Completed, including the Code Exercise), Pre-Quiz / Post-Quiz with
  best score only, a Code Exercise editor with Submit feedback, Assignment with prerequisite locking and a one-time
  submission, review of the submitted assignment
- View Progress (overall percentage, expandable experiment list) and Assignment Scores
- Profile (read-only)

**Instructor console** (details: `docs/INSTRUCTOR_CONSOLE.md`)
- Navbar: Home, Batches, profile menu
- Batch cards, batch information and student list (URN, Name) with search, sorting and pagination
- Experiments: read-only content with answer keys and a Students Status table
- Assignment: questions with answers, an Assignment Status table, and a page for each student's submission
- Excel (.xlsx) downloads for the open experiment or assignment
- One instructor per batch, enforced in the database; instructor pages are for instructors only

## Database schema
Tables by module (`backend/app/models/` is the source of truth):
- **Users**: `users`
- **Batches**: `batches`, `enrollments`, `instructor_assignments`
- **Content**: `experiments`, `experiment_evaluation_specs`
- **Quiz engine**: `quizzes`, `questions`, `options`
- **Assignment submissions (one per student)**: `quiz_submissions`, `quiz_answers`
- **Pre/Post quiz best score only**: `student_quiz_progress`
- **Manual section completion**: `section_completions`
- **Code exercises**: `code_submissions`

All tables use UUID primary keys.

## Pending work
These items are not finished yet:
1. **Student Home text**: the Home page text in `frontend/src/content/homeContent.js` is a draft; the final general
   Machine Learning content is still to be provided.
2. **Profile fields for all users** (student, instructor, admin): the page currently shows name, email, roll number
   (students only) and role as read-only text. The final fields, which can be edited, and the account actions are to be decided.
3. **Instructor Home text**: the Virtual Lab text in `frontend/src/content/instructorHomeContent.js` is placeholder text
   to be replaced.
4. **Admin console**: design and implementation. This includes deciding what admins may see of quiz answer keys,
   because `GET /quizzes/{quiz_id}` still returns answer keys to any instructor or admin without a batch or
   published check. Students never receive answer keys from it, the student UI does not call it and the instructor
   console does not use it.
5. **Code Exercise matching**: the stored result is currently compared exactly. The final matching rules are to be decided.
6. **Experiment content**: only experiment 8 (Linear Regression) has real content. The other experiments still have the
   demo content from `seed_experiments.py`, and no Guided Lab content has been added yet.

## Documentation
- `docs/STUDENT_CONSOLE.md` — how the student console works
- `docs/INSTRUCTOR_CONSOLE.md` — how the instructor console works
- `docs/DEVELOPMENT_HISTORY.md` — what was built, in order
- `CLAUDE.md` — developer notes and the rules the code follows
- `openapi.yaml` — API reference
- `CONTRIBUTING.md` — branch, pull request and commit rules
