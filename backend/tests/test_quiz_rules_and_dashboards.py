"""Best-score-only self-assessment quizzes and one-attempt assignment rules."""
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
from app.models import (
    Batch,
    Enrollment,
    InstructorAssignment,
    QuizAnswer,
    QuizSubmission,
    StudentQuizProgress,
    UserRole,
)


def test_pre_quiz_allows_unlimited_attempts_but_stores_only_best_score(client, db):
    exp = make_experiment(db)
    student = make_user(db)

    first = submit_quiz(client, student, exp, "pre", correct=False)
    assert first.status_code == 201
    assert first.json()["score"] == 0.0  # this attempt's score is returned transiently
    assert first.json()["best_score"] == 0.0
    assert "attempt_number" not in first.json()

    second = submit_quiz(client, student, exp, "pre", correct=True)
    assert second.status_code == 201
    assert second.json()["score"] == 100.0
    assert second.json()["best_score"] == 100.0
    assert "attempt_number" not in second.json()

    third = submit_quiz(client, student, exp, "pre", correct=False)
    assert third.status_code == 201
    assert third.json()["score"] == 0.0
    assert third.json()["best_score"] == 100.0  # the best score never decreases

    pre = quiz_in(get_experiment(client, student, exp), "pre")
    assert pre["my_submitted"] is True
    assert pre["my_best_score"] == 100.0
    assert "my_attempts" not in pre

    # Three submissions produce one best-score row and no per-attempt/answer rows.
    quiz_id = exp.quizzes["pre"].quiz_id
    assert db.query(StudentQuizProgress).filter_by(student_id=student.id, quiz_id=quiz_id).count() == 1
    assert db.query(QuizSubmission).filter_by(student_id=student.id, quiz_id=quiz_id).count() == 0
    assert db.query(QuizAnswer).join(QuizSubmission).filter(
        QuizSubmission.student_id == student.id,
        QuizSubmission.quiz_id == quiz_id,
    ).count() == 0


def test_post_quiz_also_uses_best_score_only_storage(client, db):
    exp = make_experiment(db)
    student = make_user(db)

    low = submit_quiz(client, student, exp, "post", correct=False)
    high = submit_quiz(client, student, exp, "post", correct=True)

    assert low.status_code == 201
    assert low.json()["score"] == 0.0
    assert low.json()["best_score"] == 0.0
    assert high.status_code == 201
    assert high.json()["score"] == 100.0
    assert high.json()["best_score"] == 100.0

    post = quiz_in(get_experiment(client, student, exp), "post")
    assert post["my_submitted"] is True
    assert post["my_best_score"] == 100.0
    quiz_id = exp.quizzes["post"].quiz_id
    assert db.query(StudentQuizProgress).filter_by(student_id=student.id, quiz_id=quiz_id).count() == 1
    assert db.query(QuizSubmission).filter_by(student_id=student.id, quiz_id=quiz_id).count() == 0


def test_assignment_can_be_submitted_only_once_and_remains_separate(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    unlock_assignment(client, db, student, exp)

    first = submit_quiz(client, student, exp, "assignment")
    assert first.status_code == 201
    assert first.json()["score"] == 100.0
    assert first.json()["best_score"] is None
    assert "attempt_number" not in first.json()

    second = submit_quiz(client, student, exp, "assignment")
    assert second.status_code == 409
    assert "already submitted" in second.json()["detail"].lower()

    assignment = quiz_in(get_experiment(client, student, exp), "assignment")
    assert assignment["my_submitted"] is True
    assert assignment["my_assignment_score"] == 100.0
    assert assignment["my_best_score"] is None

    quiz_id = exp.quizzes["assignment"].quiz_id
    assert db.query(QuizSubmission).filter_by(student_id=student.id, quiz_id=quiz_id).count() == 1
    assert db.query(QuizAnswer).join(QuizSubmission).filter(
        QuizSubmission.student_id == student.id,
        QuizSubmission.quiz_id == quiz_id,
    ).count() == 1


def test_instructor_gets_no_student_self_assessment_score(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    instructor = make_user(db, UserRole.instructor)
    assert submit_quiz(client, student, exp, "pre").status_code == 201

    pre = quiz_in(get_experiment(client, instructor, exp), "pre")
    assert pre["my_submitted"] is False
    assert pre["my_best_score"] is None
    assert pre["my_assignment_score"] is None
    assert "my_attempts" not in pre


def test_student_progress_includes_manual_section_statuses(client, db):
    make_experiment(db)
    student = make_user(db)

    rows = client.get("/dashboards/student", headers=student.headers).json()
    assert len(rows) == 1
    assert "section_statuses" in rows[0]
    assert rows[0]["section_statuses"]["guided-lab"] == "not_started"
    assert set(rows[0]) == {
        "experiment_id",
        "experiment_title",
        "experiment_number",
        "has_assignment",
        "pre_quiz",
        "code_exercise",
        "post_quiz",
        "assignment",
        "assignment_score",
        "overall_status",
        "section_statuses",
        "sections",
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

    # The student did the pre-quiz only: overall is ongoing, assignment not submitted.
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
