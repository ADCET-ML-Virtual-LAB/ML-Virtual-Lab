"""
Base-commit convenience script: creates every table directly from the ORM
models. Fine for local dev / first setup. Once the team starts changing the
schema, switch to Alembic migrations instead of re-running this (see the
"Add Alembic migrations" issue in README.md).

Usage:
    python init_db.py
"""
from app.database import Base, engine
from app import models  # noqa: F401  (import registers all models on Base.metadata)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("All tables created.")
