"""Tests for the decided status rule, the Code Exercise tick and fixed experiment numbers."""
import uuid

from app.models import SubmissionStatus, UserRole
from helpers import (
    add_code_submission,
    get_experiment,
    make_experiment,
    make_user,
    submit_quiz,
    unlock_assignment,
)


def _overall(client, student) -> str:
    rows = client.get("/dashboards/student", headers=student.headers).json()
    return rows[0]["overall_status"]


def test_code_exercise_tick_only_after_matched_result_is_saved(client, db):
    exp = make_experiment(db)
    student = make_user(db)

    assert get_experiment(client, student, exp)["code_exercise_completed"] is False

    add_code_submission(db, student, exp, SubmissionStatus.mismatched)
    assert get_experiment(client, student, exp)["code_exercise_completed"] is False

    add_code_submission(db, student, exp, SubmissionStatus.matched)
    assert get_experiment(client, student, exp)["code_exercise_completed"] is True


def test_code_exercise_tick_not_shown_to_other_students(client, db):
    exp = make_experiment(db)
    student_a = make_user(db)
    student_b = make_user(db)
    add_code_submission(db, student_a, exp, SubmissionStatus.matched)

    assert get_experiment(client, student_a, exp)["code_exercise_completed"] is True
    assert get_experiment(client, student_b, exp)["code_exercise_completed"] is False


def test_status_not_started_when_nothing_is_ticked(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    assert _overall(client, student) == "not_started"

    # A failed or mismatched code attempt is not a tick, so it is not progress.
    add_code_submission(db, student, exp, SubmissionStatus.mismatched)
    add_code_submission(db, student, exp, SubmissionStatus.error)
    assert _overall(client, student) == "not_started"


def test_status_in_progress_with_one_tick_and_completed_only_with_all(client, db):
    exp = make_experiment(db)
    student = make_user(db)

    resp = client.post(
        f"/experiments/{exp.slug}/sections/overview/complete", headers=student.headers
    )
    assert resp.status_code == 200
    assert _overall(client, student) == "in_progress"

    unlock_assignment(client, db, student, exp)
    # Everything except the assignment is ticked: still in progress.
    assert _overall(client, student) == "in_progress"

    assert submit_quiz(client, student, exp, "assignment", correct=False).status_code == 201
    # Assignment submitted with a low score still completes it.
    assert _overall(client, student) == "completed"


def test_experiment_number_must_be_between_1_and_10(client, db):
    admin = make_user(db, UserRole.admin)
    payload = {
        "title": "T",
        "slug": f"t-{uuid.uuid4().hex[:6]}",
        "aim": "a",
        "objective": "o",
        "order_index": 11,
    }
    assert client.post("/experiments", json=payload, headers=admin.headers).status_code == 422
    payload["order_index"] = 0
    assert client.post("/experiments", json=payload, headers=admin.headers).status_code == 422


def test_experiment_number_cannot_be_reused_or_changed(client, db):
    admin = make_user(db, UserRole.admin)
    payload = {
        "title": "T",
        "slug": f"t-{uuid.uuid4().hex[:6]}",
        "aim": "a",
        "objective": "o",
        "order_index": 3,
    }
    created = client.post("/experiments", json=payload, headers=admin.headers)
    assert created.status_code == 201

    duplicate = dict(payload, slug=f"t-{uuid.uuid4().hex[:6]}")
    assert client.post("/experiments", json=duplicate, headers=admin.headers).status_code == 409

    patched = client.patch(
        f"/experiments/{payload['slug']}", json={"order_index": 7, "title": "New"}, headers=admin.headers
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "New"
    assert patched.json()["order_index"] == 3
