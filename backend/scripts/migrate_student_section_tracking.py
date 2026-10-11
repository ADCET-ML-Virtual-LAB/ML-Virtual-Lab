"""Apply the small schema migration for Student Console section tracking.

Run from the backend directory:
    python -m scripts.migrate_student_section_tracking

This migration is safe to rerun. It adds experiments.overview when missing and
creates section_completions. Existing experiments receive a generic editable
overview if they do not have one yet.
"""

from sqlalchemy import inspect, text

from app.database import Base, engine
# Import all models so their tables are registered in Base.metadata.
from app.models import SectionCompletion  # noqa: F401,E402


def main() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        if "experiments" not in tables:
            # A fresh database may not have been initialised yet. create_all is
            # safe here and is also safe to run against an existing database.
            Base.metadata.create_all(bind=connection)
            inspector = inspect(connection)
            tables = set(inspector.get_table_names())

        experiment_columns = {c["name"] for c in inspector.get_columns("experiments")}
        if "overview" not in experiment_columns:
            connection.execute(text("ALTER TABLE experiments ADD COLUMN overview TEXT"))
            print("Added experiments.overview")
        else:
            print("experiments.overview already exists")

        # create_all only creates missing tables; it does not alter existing tables.
        Base.metadata.create_all(bind=connection, tables=[SectionCompletion.__table__])
        print("Ensured section_completions table exists")

        connection.execute(text(
            "UPDATE experiments "
            "SET overview = 'Explore the main concepts and practical workflow of ' || title || '.' "
            "WHERE overview IS NULL OR trim(overview) = ''"
        ))
        print("Backfilled empty overviews with editable starter text")

    print("Student section-tracking migration completed.")


if __name__ == "__main__":
    main()
