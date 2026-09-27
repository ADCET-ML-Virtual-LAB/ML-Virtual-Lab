# ML Virtual Lab — Base Commit

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
uvicorn app.main:app --reload

# 3. Frontend
cd ../frontend
npm install
npm run dev
```
Backend: http://localhost:8000/docs · Frontend: http://localhost:5173

## Pre-commit (run once per clone, from the repo root)
```bash
pip install -r backend/requirements-dev.txt
pre-commit install

# Install frontend dependencies so the frontend build hook can run.
cd frontend && npm install && cd ..

# Optional: check every tracked file immediately.
pre-commit run --all-files
```
After installation, every `git commit` runs whitespace, YAML/JSON/TOML,
merge-conflict, private-key, and large-file checks; Ruff checks and formats
Python; Prettier formats supported frontend/config/document files; and frontend
source/config changes trigger a Vite production build. A failing check blocks
the commit. If a formatter changes files, stage the changes and commit again.

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