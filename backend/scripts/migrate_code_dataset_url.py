"""Add experiments.code_dataset_url (dataset file for the Code Exercise).

Run from the backend directory with the project's virtualenv active:
    python -m scripts.migrate_code_dataset_url

Safe to rerun. Nothing else is changed.
"""
from sqlalchemy import inspect, text

from app.database import engine


def main() -> None:
    with engine.begin() as connection:
        columns = {c["name"] for c in inspect(connection).get_columns("experiments")}
        if "code_dataset_url" in columns:
            print("experiments.code_dataset_url already exists. Nothing to do.")
            return
        connection.execute(text("ALTER TABLE experiments ADD COLUMN code_dataset_url TEXT"))
        print("Added experiments.code_dataset_url")


if __name__ == "__main__":
    main()
