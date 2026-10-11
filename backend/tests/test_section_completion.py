"""Tests for database-backed static section completion."""

from helpers import get_experiment, make_experiment, make_user
from app.models import UserRole


def test_student_can_complete_section_and_status_is_returned_from_db(client, db):
    exp = make_experiment(db)
    student = make_user(db)

    initial = get_experiment(client, student, exp)
    assert initial["section_completions"]["theory"] is False

    response = client.post(
        f"/experiments/{exp.slug}/sections/theory/complete",
        headers=student.headers,
    )
    assert response.status_code == 200
    assert response.json()["completed"] is True

    refreshed = get_experiment(client, student, exp)
    assert refreshed["section_completions"]["theory"] is True


def test_section_completion_is_idempotent(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    url = f"/experiments/{exp.slug}/sections/guided-lab/complete"

    first = client.post(url, headers=student.headers)
    second = client.post(url, headers=student.headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_unknown_section_key_cannot_be_marked_complete(client, db):
    exp = make_experiment(db)
    student = make_user(db)

    response = client.post(
        f"/experiments/{exp.slug}/sections/assignment/complete",
        headers=student.headers,
    )
    assert response.status_code == 404

def test_non_student_cannot_mark_section_complete(client, db):
    exp = make_experiment(db)
    instructor = make_user(db, UserRole.instructor)

    response = client.post(
        f"/experiments/{exp.slug}/sections/theory/complete",
        headers=instructor.headers,
    )
    assert response.status_code == 403
