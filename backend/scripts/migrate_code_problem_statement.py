"""Add experiments.code_problem_statement (the Code Exercise problem statement).

Run from the backend directory with the project's virtualenv active:
    python -m scripts.migrate_code_problem_statement

Safe to rerun. Nothing else is changed.
"""
from sqlalchemy import inspect, text

from app.database import engine


def main() -> None:
    with engine.begin() as connection:
        columns = {c["name"] for c in inspect(connection).get_columns("experiments")}
        if "code_problem_statement" in columns:
            print("experiments.code_problem_statement already exists. Nothing to do.")
            return
        connection.execute(text("ALTER TABLE experiments ADD COLUMN code_problem_statement TEXT"))
        print("Added experiments.code_problem_statement")


if __name__ == "__main__":
    main()
