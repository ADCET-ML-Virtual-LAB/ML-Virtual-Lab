"""Tests for the View Progress data and the submitted-assignment review."""
from app.models import Quiz, QuizType
from helpers import (
    add_code_submission,
    get_experiment,
    make_experiment,
    make_user,
    quiz_in,
    submit_quiz,
    unlock_assignment,
)
from app.models import SubmissionStatus

FULL_ORDER = [
    "overview",
    "aim-objectives",
    "pre-quiz",
    "video",
    "theory",
    "guided-lab",
    "code-exercise",
    "post-quiz",
    "assignment",
]


def _row(client, student) -> dict:
    return client.get("/dashboards/student", headers=student.headers).json()[0]


def test_sections_are_listed_in_the_approved_order_and_start_incomplete(client, db):
    make_experiment(db)
    student = make_user(db)
    row = _row(client, student)

    assert [s["key"] for s in row["sections"]] == FULL_ORDER
    assert all(s["completed"] is False for s in row["sections"])
    assert row["has_assignment"] is True


def test_sections_reflect_saved_completion(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    client.post(f"/experiments/{exp.slug}/sections/overview/complete", headers=student.headers)
    submit_quiz(client, student, exp, "pre")
    add_code_submission(db, student, exp, SubmissionStatus.matched)

    done = {s["key"]: s["completed"] for s in _row(client, student)["sections"]}
    assert done["overview"] is True
    assert done["pre-quiz"] is True
    assert done["code-exercise"] is False  # a code submission, even a match, is not a tick
    assert done["assignment"] is False

    client.post(f"/experiments/{exp.slug}/sections/code-exercise/complete", headers=student.headers)
    done = {s["key"]: s["completed"] for s in _row(client, student)["sections"]}
    assert done["code-exercise"] is True  # only Mark Completed ticks it


def test_experiment_without_assignment_has_no_assignment_section(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    quiz = db.query(Quiz).filter_by(experiment_id=exp.id, quiz_type=QuizType.assignment).one()
    db.delete(quiz)
    db.commit()

    row = _row(client, student)
    assert row["has_assignment"] is False
    assert "assignment" not in [s["key"] for s in row["sections"]]
    assert row["assignment"] == "not_started"


def test_review_is_not_available_before_submission(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    unlock_assignment(client, db, student, exp)

    assignment = quiz_in(get_experiment(client, student, exp), "assignment")
    assert assignment["my_review"] is None
    # Options never carry is_correct for a student.
    assert all("is_correct" not in o for q in assignment["questions"] for o in q["options"])


def test_student_sees_own_graded_answers_after_submission(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    unlock_assignment(client, db, student, exp)
    assert submit_quiz(client, student, exp, "assignment", correct=False).status_code == 201

    q = exp.quizzes["assignment"]
    for review in (
        quiz_in(get_experiment(client, student, exp), "assignment")["my_review"],
        client.get(f"/quizzes/{q.quiz_id}", headers=student.headers).json()["my_review"],
    ):
        assert len(review) == 1
        assert review[0]["question_id"] == str(q.question_id)
        assert review[0]["selected_option_id"] == str(q.wrong_id)
        assert review[0]["correct_option_ids"] == [str(q.right_id)]
        assert review[0]["is_correct"] is False


def test_correct_answer_is_marked_correct_in_review(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    unlock_assignment(client, db, student, exp)
    assert submit_quiz(client, student, exp, "assignment", correct=True).status_code == 201

    review = quiz_in(get_experiment(client, student, exp), "assignment")["my_review"]
    assert review[0]["is_correct"] is True


def test_review_is_private_to_the_submitting_student(client, db):
    exp = make_experiment(db)
    student_a = make_user(db)
    student_b = make_user(db)
    unlock_assignment(client, db, student_a, exp)
    assert submit_quiz(client, student_a, exp, "assignment").status_code == 201

    unlock_assignment(client, db, student_b, exp)
    assert quiz_in(get_experiment(client, student_b, exp), "assignment")["my_review"] is None


def test_pre_and_post_quizzes_never_return_a_review(client, db):
    exp = make_experiment(db)
    student = make_user(db)
    submit_quiz(client, student, exp, "pre")
    submit_quiz(client, student, exp, "post")

    data = get_experiment(client, student, exp)
    assert quiz_in(data, "pre")["my_review"] is None
    assert quiz_in(data, "post")["my_review"] is None
