"""The Code Exercise problem statement is stored per experiment and shown to students."""
from app.models import Experiment, UserRole
from helpers import make_experiment, make_user


def test_problem_statement_is_returned_to_students(client, db):
    exp = make_experiment(db)
    db.get(Experiment, exp.id).code_problem_statement = "Use random_state=42. Store the answer in `result`."
    db.commit()
    student = make_user(db, UserRole.student)

    body = client.get(f"/experiments/{exp.slug}", headers=student.headers).json()
    assert body["code_problem_statement"] == "Use random_state=42. Store the answer in `result`."


def test_problem_statement_is_optional(client, db):
    exp = make_experiment(db)
    student = make_user(db, UserRole.student)
    body = client.get(f"/experiments/{exp.slug}", headers=student.headers).json()
    assert body["code_problem_statement"] is None
