"""
Quizzes router — Module 4 (MCQ Engine).

Endpoints:
  POST   /experiments/{experiment_id}/quizzes    create quiz + questions (admin only)
  GET    /quizzes/{quiz_id}                      get quiz questions (students get no is_correct)
  POST   /quizzes/{quiz_id}/submit               submit answers, get results
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, require_roles
from app.database import get_db
from app.models import User
from app.models.experiment import Experiment
from app.models.quiz import (
    Option,
    Question,
    Quiz,
    QuizAnswer,
    QuizSubmission,
    RevealPolicy,
)
from app.models.user import UserRole
from app.schemas.quiz import (
    QuizCreate,
    QuizOut,
    QuizOutAdmin,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizAnswerResult,
)

router = APIRouter(tags=["quizzes"])


def _get_quiz_or_404(quiz_id: uuid.UUID, db: Session) -> Quiz:
    q = db.get(Quiz, quiz_id)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quiz not found")
    return q


# ── Create quiz ──────────────────────────────────────────────────────────────

@router.post(
    "/experiments/{experiment_id}/quizzes",
    response_model=QuizOutAdmin,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(
    experiment_id: uuid.UUID,
    payload: QuizCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(UserRole.admin)),
):
    exp = db.get(Experiment, experiment_id)
    if exp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiment not found")

    is_scored = payload.quiz_type.value == "assignment"
    quiz = Quiz(
        experiment_id=experiment_id,
        quiz_type=payload.quiz_type,
        is_scored=is_scored,
        title=payload.title,
        deadline=payload.deadline,
        reveal_policy=payload.reveal_policy,
    )
    db.add(quiz)
    try:
        db.flush()  # get quiz.id before adding questions
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This experiment already has a quiz of this type",
        )

    for q_data in payload.questions:
        question = Question(
            quiz_id=quiz.id,
            question_text=q_data.question_text,
            order_index=q_data.order_index,
        )
        db.add(question)
        db.flush()
        for o_data in q_data.options:
            db.add(Option(
                question_id=question.id,
                option_text=o_data.option_text,
                is_correct=o_data.is_correct,
                order_index=o_data.order_index,
            ))

    db.commit()
    db.refresh(quiz)
    return quiz


# ── Get quiz ──────────────────────────────────────────────────────────────────

@router.get("/quizzes/{quiz_id}")
def get_quiz(
    quiz_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    quiz = _get_quiz_or_404(quiz_id, db)
    # Admin/instructor see is_correct; students don't
    if current_user.role in (UserRole.admin, UserRole.instructor):
        return QuizOutAdmin.model_validate(quiz)
    return QuizOut.model_validate(quiz)


# ── Submit quiz ───────────────────────────────────────────────────────────────

@router.post(
    "/quizzes/{quiz_id}/submit",
    response_model=QuizSubmitResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_quiz(
    quiz_id: uuid.UUID,
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Accept quiz answers and return per-question correctness.
    For pre/post (ungraded): no score stored.
    For assignment (graded): stores score; reveals it based on reveal_policy.
    Re-submission is always allowed — each call creates a new attempt.
    """
    quiz = _get_quiz_or_404(quiz_id, db)

    # Build a lookup of valid question_id → {option_id → is_correct}
    question_map: dict[uuid.UUID, dict[uuid.UUID, bool]] = {}
    for question in quiz.questions:
        question_map[question.id] = {opt.id: opt.is_correct for opt in question.options}

    # Validate submitted answers
    results: list[QuizAnswerResult] = []
    correct_count = 0
    for answer in payload.answers:
        if answer.question_id not in question_map:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"question_id {answer.question_id} is not in this quiz",
            )
        opts = question_map[answer.question_id]
        if answer.selected_option_id not in opts:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"option_id {answer.selected_option_id} does not belong to question {answer.question_id}",
            )
        is_correct = opts[answer.selected_option_id]
        if is_correct:
            correct_count += 1
        results.append(QuizAnswerResult(question_id=answer.question_id, is_correct=is_correct))

    # Calculate score (0–100)
    score = round(correct_count / len(quiz.questions) * 100, 2) if quiz.questions else 0.0

    # Determine next attempt number
    prev_attempts = (
        db.query(QuizSubmission)
        .filter(
            QuizSubmission.student_id == current_user.id,
            QuizSubmission.quiz_id == quiz_id,
        )
        .count()
    )
    attempt_number = prev_attempts + 1

    # Persist submission
    submission = QuizSubmission(
        student_id=current_user.id,
        quiz_id=quiz_id,
        attempt_number=attempt_number,
        score=score if quiz.is_scored else None,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.flush()

    for answer in payload.answers:
        opts = question_map[answer.question_id]
        db.add(QuizAnswer(
            quiz_submission_id=submission.id,
            question_id=answer.question_id,
            selected_option_id=answer.selected_option_id,
            is_correct=opts[answer.selected_option_id],
        ))

    db.commit()

    # Decide whether to reveal score (assignment only, based on reveal_policy)
    revealed_score: float | None = None
    if quiz.is_scored:
        if quiz.reveal_policy == RevealPolicy.immediate:
            revealed_score = score
        elif quiz.reveal_policy == RevealPolicy.after_deadline:
            if quiz.deadline is None or datetime.now(timezone.utc) >= quiz.deadline:
                revealed_score = score

    return QuizSubmitResponse(
        attempt_number=attempt_number,
        score=revealed_score,
        answers=results,
    )
