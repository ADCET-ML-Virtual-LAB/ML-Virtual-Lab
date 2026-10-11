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
    QuizType,
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
from app.services.progress import (
    missing_assignment_prerequisites,
    quiz_attempt_summary,
    score_is_revealed,
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
    # Locked means locked for viewing too: no questions until the earlier steps are done.
    if quiz.quiz_type == QuizType.assignment:
        missing = missing_assignment_prerequisites(current_user.id, quiz.experiment, db)
        if missing:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Assignment is locked. Complete these first: " + ", ".join(missing),
            )
    out = QuizOut.model_validate(quiz)
    out.my_attempts, out.my_best_score = quiz_attempt_summary(current_user.id, quiz, db)
    return out


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
    Pre/post (self-assessment): unlimited attempts; every score is stored and the response carries
    this attempt's score plus the best score so far. Instructors never receive these scores.
    Assignment (graded): ONE attempt only (a second submit returns 409); its score is revealed
    according to reveal_policy.
    """
    # Only students take quizzes. Instructors and admins view content and results, they do not submit.
    if current_user.role != UserRole.student:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only students can submit quizzes")

    quiz = _get_quiz_or_404(quiz_id, db)

    # The graded assignment stays locked until the earlier steps are done.
    # Enforced here (not only in the UI) so it cannot be bypassed by calling the API directly.
    if quiz.quiz_type == QuizType.assignment:
        missing = missing_assignment_prerequisites(current_user.id, quiz.experiment, db)
        if missing:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Assignment is locked. Complete these first: " + ", ".join(missing),
            )

    # The graded assignment can be submitted exactly once.
    if quiz.quiz_type == QuizType.assignment:
        already = (
            db.query(QuizSubmission)
            .filter(QuizSubmission.student_id == current_user.id, QuizSubmission.quiz_id == quiz_id)
            .first()
        )
        if already is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "You have already submitted this assignment")

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

    # Persist the submission. The score is stored for every quiz type: pre/post so the student can see
    # their best score, the assignment so instructors can. Pre/post scores are never sent to instructors.
    try:
        submission = QuizSubmission(
            student_id=current_user.id,
            quiz_id=quiz_id,
            attempt_number=attempt_number,
            score=score,
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
    except IntegrityError:
        # Two submits at the same moment (e.g. a double click) collide on the unique attempt number.
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This quiz was just submitted from another request. Please refresh the page.",
        )

    # Pre/post scores are always visible to the student; the assignment score follows its reveal_policy.
    if quiz.quiz_type == QuizType.assignment:
        revealed_score = score if score_is_revealed(quiz) else None
        best_score = None
    else:
        revealed_score = score
        _, best_score = quiz_attempt_summary(current_user.id, quiz, db)

    return QuizSubmitResponse(
        attempt_number=attempt_number,
        score=revealed_score,
        best_score=best_score,
        answers=results,
    )
