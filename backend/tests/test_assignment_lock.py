"""The graded assignment stays locked (and hidden) until Pre-Quiz, Post-Quiz and a MATCHING Code Exercise are done.
The lock is for students only; instructors and admins are never locked, and they cannot submit quizzes."""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.core.security import create_access_token, hash_password
from app.models import (
    CodeSubmission,
    Experiment,
    ExperimentEvaluationSpec,
    Option,
    Question,
    Quiz,
    QuizType,
    SubmissionStatus,
    User,
    UserRole,
)


def _make_user(db, role: UserRole = UserRole.student) -> SimpleNamespace:
    user = User(
        full_name="Test User",
        email=f"{role.value}-{uuid.uuid4().hex[:8]}@college.edu",
        password_hash=hash_password("Pass12345"),
        role=role,
    )
    db.add(user)
    db.commit()
    user_id = user.id
    token = create_access_token(user_id, role.value)
    return SimpleNamespace(id=user_id, headers={"Authorization": f"Bearer {token}"})


def _make_experiment(db, with_spec: bool = True) -> SimpleNamespace:
    """Published experiment with pre/post/assignment quizzes (1 question each).
    `quizzes` maps quiz type -> (quiz_id, question_id, correct_option_id)."""
    exp = Experiment(
        title="Linear Regression",
        slug=f"lr-{uuid.uuid4().hex[:8]}",
        aim="aim",
        objective="objective",
        is_published=True,
    )
    db.add(exp)
    db.flush()

    quizzes = {}
    for quiz_type in (QuizType.pre, QuizType.post, QuizType.assignment):
        quiz = Quiz(
            experiment_id=exp.id,
            quiz_type=quiz_type,
            is_scored=quiz_type == QuizType.assignment,
            title=quiz_type.value,
        )
        db.add(quiz)
        db.flush()
        question = Question(quiz_id=quiz.id, question_text="2 + 2 = ?", order_index=0)
        db.add(question)
        db.flush()
        right = Option(question_id=question.id, option_text="4", is_correct=True, order_index=0)
        wrong = Option(question_id=question.id, option_text="5", is_correct=False, order_index=1)
        db.add_all([right, wrong])
        db.flush()
        quizzes[quiz_type.value] = (quiz.id, question.id, right.id)

    if with_spec:
        db.add(ExperimentEvaluationSpec(experiment_id=exp.id, expected_output={"value": 1.0}))
    db.commit()
    return SimpleNamespace(id=exp.id, slug=exp.slug, quizzes=quizzes)


def _submit_quiz(client, user, exp, quiz_type):
    quiz_id, question_id, option_id = exp.quizzes[quiz_type]
    return client.post(
        f"/quizzes/{quiz_id}/submit",
        json={"answers": [{"question_id": str(question_id), "selected_option_id": str(option_id)}]},
        headers=user.headers,
    )


def _add_code_submission(db, user, exp, status):
    db.add(
        CodeSubmission(
            student_id=user.id,
            experiment_id=exp.id,
            submitted_code="print(1)",
            client_output={"value": 1.0},
            status=status,
            submitted_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def _get_experiment(client, user, exp) -> dict:
    resp = client.get(f"/experiments/{exp.slug}", headers=user.headers)
    assert resp.status_code == 200
    return resp.json()


def _complete_static_sections(client, user, exp):
    for section_key in ("overview", "aim-objectives", "theory", "video", "guided-lab", "code-exercise"):
        response = client.post(
            f"/experiments/{exp.slug}/sections/{section_key}/complete",
            headers=user.headers,
        )
        assert response.status_code == 200, response.text


def _quiz_in(data: dict, quiz_type: str) -> dict:
    return next(q for q in data["quizzes"] if q["quiz_type"] == quiz_type)


def test_locked_assignment_is_hidden_from_a_student_with_no_progress(client, db):
    exp = _make_experiment(db)
    student = _make_user(db)

    data = _get_experiment(client, student, exp)
    assert data["assignment_locked"] is True
    assert data["assignment_missing_steps"] == [
        "Experiment Title / Overview", "Aim / Learning Objectives", "Pre-Quiz", "Video",
        "Theory / Reading Material", "Guided Lab", "Code Exercise", "Post-Quiz"
    ]
    assert _quiz_in(data, "assignment")["questions"] == []  # cannot even be viewed
    assert len(_quiz_in(data, "pre")["questions"]) == 1  # other quizzes stay open

    assignment_id = exp.quizzes["assignment"][0]
    assert client.get(f"/quizzes/{assignment_id}", headers=student.headers).status_code == 403
    resp = _submit_quiz(client, student, exp, "assignment")
    assert resp.status_code == 403
    assert "locked" in resp.json()["detail"].lower()


def test_assignment_stays_locked_until_code_exercise_is_marked_completed(client, db):
    exp = _make_experiment(db)
    student = _make_user(db)

    for section_key in ("overview", "aim-objectives", "theory", "video", "guided-lab"):
        client.post(f"/experiments/{exp.slug}/sections/{section_key}/complete", headers=student.headers)
    assert _submit_quiz(client, student, exp, "pre").status_code == 201
    assert _submit_quiz(client, student, exp, "post").status_code == 201
    # A matched code result alone does not complete the Code Exercise.
    _add_code_submission(db, student, exp, SubmissionStatus.matched)

    data = _get_experiment(client, student, exp)
    assert data["assignment_locked"] is True
    assert data["assignment_missing_steps"] == ["Code Exercise"]
    assert _submit_quiz(client, student, exp, "assignment").status_code == 403


def test_assignment_opens_when_everything_is_done_without_a_code_match(client, db):
    exp = _make_experiment(db)
    student = _make_user(db)

    _complete_static_sections(client, student, exp)  # includes Mark Completed on the Code Exercise
    assert _submit_quiz(client, student, exp, "pre").status_code == 201
    assert _submit_quiz(client, student, exp, "post").status_code == 201
    # No code submission at all: matching is not required.

    data = _get_experiment(client, student, exp)
    assert data["assignment_locked"] is False
    assert data["assignment_missing_steps"] == []
    assert len(_quiz_in(data, "assignment")["questions"]) == 1

    assignment_id = exp.quizzes["assignment"][0]
    assert client.get(f"/quizzes/{assignment_id}", headers=student.headers).status_code == 200
    assert _submit_quiz(client, student, exp, "assignment").status_code == 201


def test_code_exercise_is_required_even_without_an_expected_result(client, db):
    # Like Guided Lab, the Code Exercise counts for every experiment.
    exp = _make_experiment(db, with_spec=False)
    student = _make_user(db)

    for section_key in ("overview", "aim-objectives", "theory", "video", "guided-lab"):
        client.post(f"/experiments/{exp.slug}/sections/{section_key}/complete", headers=student.headers)
    assert _submit_quiz(client, student, exp, "pre").status_code == 201
    assert _submit_quiz(client, student, exp, "post").status_code == 201
    assert _get_experiment(client, student, exp)["assignment_missing_steps"] == ["Code Exercise"]

    client.post(f"/experiments/{exp.slug}/sections/code-exercise/complete", headers=student.headers)
    assert _get_experiment(client, student, exp)["assignment_locked"] is False


def test_instructor_and_admin_are_never_locked_but_cannot_submit(client, db):
    exp = _make_experiment(db)
    for role in (UserRole.instructor, UserRole.admin):
        user = _make_user(db, role)

        data = _get_experiment(client, user, exp)
        assert data["assignment_locked"] is False
        assert data["assignment_missing_steps"] == []
        assert len(_quiz_in(data, "assignment")["questions"]) == 1  # they can view it

        assert _submit_quiz(client, user, exp, "assignment").status_code == 403
        assert _submit_quiz(client, user, exp, "pre").status_code == 403
