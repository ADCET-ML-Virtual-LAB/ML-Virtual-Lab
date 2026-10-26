"""Enforce one instructor per batch at the database level.

Run from the backend directory after activating the project's virtualenv:
    python -m scripts.migrate_one_instructor_per_batch

If any batch currently has more than one instructor, the script lists them and
stops WITHOUT changing anything: decide which instructor to keep, delete the
other instructor_assignments rows, then run it again.
"""
from sqlalchemy import inspect, text

from app.database import engine

CONSTRAINT = "uq_instructor_assignment_batch"


def main() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "instructor_assignments" not in inspector.get_table_names():
            raise RuntimeError("instructor_assignments table not found; check the database in backend/.env.")

        existing = {c["name"] for c in inspector.get_unique_constraints("instructor_assignments")}
        if CONSTRAINT in existing:
            print("One-instructor-per-batch constraint already exists. Nothing to do.")
            return

        duplicates = connection.execute(text(
            "SELECT b.name, b.academic_year, COUNT(*) AS n "
            "FROM instructor_assignments ia JOIN batches b ON b.id = ia.batch_id "
            "GROUP BY b.name, b.academic_year, ia.batch_id HAVING COUNT(*) > 1"
        )).all()
        if duplicates:
            for name, year, n in duplicates:
                print(f"Batch {name} ({year}) has {n} instructors.")
            raise RuntimeError(
                "Some batches have more than one instructor. Remove the extra "
                "instructor_assignments rows first, then re-run this script. Nothing was changed."
            )

        connection.execute(text(
            f"ALTER TABLE instructor_assignments ADD CONSTRAINT {CONSTRAINT} UNIQUE (batch_id)"
        ))
        print("Added the one-instructor-per-batch constraint.")


if __name__ == "__main__":
    main()
