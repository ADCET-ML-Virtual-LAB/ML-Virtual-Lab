"""Create the best-score-only table for Pre-Quiz and Post-Quiz results.

Run from the backend directory after activating the project's virtualenv:
    python -m scripts.migrate_quiz_best_score_only

This migration only creates student_quiz_progress if it is missing. It does not
delete or alter users, experiments, assignment submissions, or other tables.
"""
from sqlalchemy import inspect

from app.database import Base, engine
# Import all models so StudentQuizProgress is registered with Base.metadata.
from app.models import StudentQuizProgress  # noqa: F401,E402


def main() -> None:
    with engine.begin() as connection:
        existing_tables = set(inspect(connection).get_table_names())
        if "users" not in existing_tables or "quizzes" not in existing_tables:
            raise RuntimeError(
                "The application tables are missing. Initialise the existing database first; "
                "this migration should be run against your development database."
            )
        Base.metadata.create_all(bind=connection, tables=[StudentQuizProgress.__table__])
        print("Ensured student_quiz_progress table exists.")
    print("Best-score-only quiz migration completed. Existing assignment data was not modified.")


if __name__ == "__main__":
    main()
