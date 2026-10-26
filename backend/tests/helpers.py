"""Shared test helpers (not a test module). Import with `from helpers import ...`."""
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


def make_user(db, role: UserRole = UserRole.student) -> SimpleNamespace:
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


def make_experiment(db, with_spec: bool = True) -> SimpleNamespace:
    """Published experiment with pre/post/assignment quizzes (1 question, 1 right + 1 wrong option each).
    `quizzes[type]` has quiz_id, question_id, right_id, wrong_id."""
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
        quizzes[quiz_type.value] = SimpleNamespace(
            quiz_id=quiz.id, question_id=question.id, right_id=right.id, wrong_id=wrong.id
        )

    if with_spec:
        db.add(ExperimentEvaluationSpec(experiment_id=exp.id, expected_output={"value": 1.0}))
    db.commit()
    return SimpleNamespace(id=exp.id, slug=exp.slug, quizzes=quizzes)


def submit_quiz(client, user, exp, quiz_type, correct: bool = True):
    q = exp.quizzes[quiz_type]
    option_id = q.right_id if correct else q.wrong_id
    return client.post(
        f"/quizzes/{q.quiz_id}/submit",
        json={"answers": [{"question_id": str(q.question_id), "selected_option_id": str(option_id)}]},
        headers=user.headers,
    )


def add_code_submission(db, user, exp, status: SubmissionStatus):
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


STATIC_SECTION_KEYS = ("overview", "aim-objectives", "theory", "video", "guided-lab", "code-exercise")


def complete_static_sections(client, user, exp):
    """Use the public API to complete every required manually tracked section."""
    for section_key in STATIC_SECTION_KEYS:
        response = client.post(
            f"/experiments/{exp.slug}/sections/{section_key}/complete",
            headers=user.headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["completed"] is True


def unlock_assignment(client, db, user, exp):
    """Mark every manual section (including the Code Exercise) and submit both quizzes."""
    complete_static_sections(client, user, exp)
    assert submit_quiz(client, user, exp, "pre").status_code == 201
    assert submit_quiz(client, user, exp, "post").status_code == 201


def get_experiment(client, user, exp) -> dict:
    resp = client.get(f"/experiments/{exp.slug}", headers=user.headers)
    assert resp.status_code == 200
    return resp.json()


def quiz_in(data: dict, quiz_type: str) -> dict:
    return next(q for q in data["quizzes"] if q["quiz_type"] == quiz_type)
