"""Quiz attempt rules (pre/post unlimited + best score, assignment one attempt) and what each role sees."""
import csv
import io
import uuid

from helpers import (
    get_experiment,
    make_experiment,
    make_user,
    quiz_in,
    submit_quiz,
    unlock_assignment,
)

from app.models import Batch, Enrollment, InstructorAssignment, UserRole


def test_pre_quiz_allows_unlimited_attempts_and_reports_best_score(client, db):
    exp = make_experiment(db)
    student = make_user(db)

    first = submit_quiz(client, student, exp, "pre", correct=False)
    assert first.status_code == 201
    assert first.json()["score"] == 0.0
    assert first.json()["best_score"] == 0.0

    second = submit_quiz(client, student, exp, "pre", correct=True)
    assert second.json()["attempt_number"] == 2
    assert second.json()["score"] == 100.0
    assert second.json()["best_score"] == 100.0

    third = submit_quiz(client, student, exp, "pre", correct=False)
    assert third.status_code == 201
    assert third.json()["score"] == 0.0
    assert third.json()["best_score"] == 100.0  # the best attempt is kept

    pre = quiz_in(get_experiment(client, student, exp), "pre")
    assert pre["my_attempts"] == 3
    assert pre["my_best_score"] == 100.0


def test_assignment_can_be_submitted_only_once(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    unlock_assignment(client, db, student, exp)

    assert submit_quiz(client, student, exp, "assignment").status_code == 201
    second = submit_quiz(client, student, exp, "assignment")
    assert second.status_code == 409
    assert "already submitted" in second.json()["detail"].lower()

    assignment = quiz_in(get_experiment(client, student, exp), "assignment")
    assert assignment["my_attempts"] == 1
    assert assignment["my_best_score"] == 100.0  # reveal_policy defaults to immediate


def test_instructor_gets_no_attempt_counts(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    instructor = make_user(db, UserRole.instructor)
    assert submit_quiz(client, student, exp, "pre").status_code == 201

    pre = quiz_in(get_experiment(client, instructor, exp), "pre")
    assert pre["my_attempts"] == 0
    assert pre["my_best_score"] is None


def test_student_progress_has_no_guided_lab(client, db):
    make_experiment(db)
    student = make_user(db)

    rows = client.get("/dashboards/student", headers=student.headers).json()
    assert len(rows) == 1
    assert "guided_lab" not in rows[0]
    assert set(rows[0]) == {
        "experiment_id",
        "experiment_title",
        "pre_quiz",
        "code_exercise",
        "post_quiz",
        "assignment",
        "assignment_score",
        "overall_status",
    }


def test_instructor_dashboard_and_csv_show_only_overall_and_assignment(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    instructor = make_user(db, UserRole.instructor)

    batch = Batch(name=f"A-{uuid.uuid4().hex[:6]}", academic_year="2026-27")
    db.add(batch)
    db.flush()
    batch_id = str(batch.id)
    db.add(Enrollment(student_id=student.id, batch_id=batch.id))
    db.add(InstructorAssignment(instructor_id=instructor.id, batch_id=batch.id))
    db.commit()

    # The student did the pre-quiz only: overall is "Ongoing", the assignment is not submitted.
    assert submit_quiz(client, student, exp, "pre").status_code == 201

    data = client.get(f"/dashboards/instructor?batch_id={batch_id}", headers=instructor.headers).json()
    entry = data[0]["experiments"][0]
    assert set(entry) == {
        "experiment_id",
        "experiment_title",
        "overall_status",
        "assignment_status",
        "assignment_score",
    }
    assert entry["overall_status"] == "in_progress"
    assert entry["assignment_status"] == "not_started"

    resp = client.get(f"/dashboards/instructor/export?batch_id={batch_id}", headers=instructor.headers)
    assert resp.status_code == 200
    rows = list(csv.reader(io.StringIO(resp.text)))
    short = exp.slug[:20]
    assert rows[0] == ["student_name", "roll_number", "email", f"{short}_assignment", f"{short}_score"]
    assert rows[1][3:] == ["not_started", ""]


def test_instructor_sees_assignment_score_once_submitted(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    instructor = make_user(db, UserRole.instructor)

    batch = Batch(name=f"B-{uuid.uuid4().hex[:6]}", academic_year="2026-27")
    db.add(batch)
    db.flush()
    batch_id = str(batch.id)
    db.add(Enrollment(student_id=student.id, batch_id=batch.id))
    db.add(InstructorAssignment(instructor_id=instructor.id, batch_id=batch.id))
    db.commit()

    unlock_assignment(client, db, student, exp)
    assert submit_quiz(client, student, exp, "assignment").status_code == 201

    entry = client.get(f"/dashboards/instructor?batch_id={batch_id}", headers=instructor.headers).json()[0][
        "experiments"
    ][0]
    assert entry["assignment_status"] == "completed"
    assert entry["assignment_score"] == 100.0
    assert entry["overall_status"] == "completed"
