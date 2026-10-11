"""
Experiments router — Module 3 (Content Management) + Module 5 (lab_config).

Endpoints:
  GET    /experiments               list published experiments (all logged-in users)
  POST   /experiments               create experiment (admin only)
  GET    /experiments/{slug}        get one experiment by slug
  PATCH  /experiments/{slug}        update experiment (admin only)
  POST   /experiments/{id}/evaluation-spec   set/replace hidden expected output (admin only)
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, require_roles
from app.database import get_db
from app.models import User
from app.models.experiment import Experiment, ExperimentEvaluationSpec
from app.models.section_completion import SectionCompletion
from app.models.quiz import QuizType
from app.models.user import UserRole
from app.schemas.experiment import (
    EvalSpecCreate,
    ExperimentCreate,
    ExperimentDetailOut,
    ExperimentOut,
    ExperimentUpdate,
)
from app.schemas.section_completion import SectionCompletionOut
from app.services.progress import (
    assignment_review,
    is_code_exercise_completed,
    missing_assignment_prerequisites,
    student_quiz_status,
)
from app.services.section_tracking import (
    STATIC_SECTION_LABELS,
    get_section_completion_map,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])


def _get_experiment_or_404(slug: str, db: Session) -> Experiment:
    exp = db.query(Experiment).filter(Experiment.slug == slug).first()
    if exp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiment not found")
    return exp


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ExperimentOut])
def list_experiments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return published experiments ordered by order_index.
    Admin/instructor also see unpublished ones for management purposes."""
    q = db.query(Experiment).order_by(Experiment.order_index)
    if current_user.role == UserRole.student:
        q = q.filter(Experiment.is_published == True)  # noqa: E712
    return q.all()


# ── Create ───────────────────────────────────────────────────────────────────

@router.post("", response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
def create_experiment(
    payload: ExperimentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(UserRole.admin)),
):
    # Experiment numbers are fixed (1-10) and each number can be used once.
    if db.query(Experiment.id).filter(Experiment.order_index == payload.order_index).first():
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Experiment number {payload.order_index} already exists",
        )
    exp = Experiment(**payload.model_dump())
    db.add(exp)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already in use")
    db.refresh(exp)
    return exp


# ── Get one ──────────────────────────────────────────────────────────────────

@router.get("/{slug}", response_model=ExperimentDetailOut)
def get_experiment(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    exp = _get_experiment_or_404(slug, db)
    # Students may only view published experiments
    if current_user.role == UserRole.student and not exp.is_published:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiment not found")

    # Copy into the response model first; the withholding below changes only this copy, never the DB rows.
    detail = ExperimentDetailOut.model_validate(exp)

    # Student-only saved quiz state: best score for pre/post, accepted score for assignment.
    if current_user.role == UserRole.student:
        detail.section_completions = get_section_completion_map(current_user.id, exp.id, db)
        detail.code_exercise_completed = is_code_exercise_completed(current_user.id, exp, db)
        quizzes_by_id = {q.id: q for q in exp.quizzes}
        for quiz_out in detail.quizzes:
            quiz = quizzes_by_id[quiz_out.id]
            quiz_out.my_submitted, saved_score = student_quiz_status(current_user.id, quiz, db)
            if quiz.quiz_type == QuizType.assignment:
                quiz_out.my_assignment_score = saved_score
                quiz_out.my_review = assignment_review(current_user.id, quiz, db)
            else:
                quiz_out.my_best_score = saved_score

    # Assignment lock (students only): until the earlier steps are done the assignment is hidden completely.
    if current_user.role == UserRole.student and any(q.quiz_type == QuizType.assignment for q in exp.quizzes):
        missing = missing_assignment_prerequisites(current_user.id, exp, db)
        if missing:
            detail.assignment_locked = True
            detail.assignment_missing_steps = missing
            for quiz in detail.quizzes:
                if quiz.quiz_type == QuizType.assignment:
                    quiz.questions = []
    return detail


# ── Student section completion ───────────────────────────────────────────────

@router.post(
    "/{slug}/sections/{section_key}/complete",
    response_model=SectionCompletionOut,
    status_code=status.HTTP_200_OK,
)
def mark_section_completed(
    slug: str,
    section_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
):
    """Persist a student's manual completion of a static experiment section.

    This endpoint is idempotent. The frontend must re-fetch experiment progress
    after this returns successfully; it must not add the completion tick itself.
    """
    if section_key not in STATIC_SECTION_LABELS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown manually tracked section")

    exp = _get_experiment_or_404(slug, db)
    if not exp.is_published:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiment not found")

    existing = db.query(SectionCompletion).filter(
        SectionCompletion.student_id == current_user.id,
        SectionCompletion.experiment_id == exp.id,
        SectionCompletion.section_key == section_key,
    ).first()
    if existing is not None:
        return SectionCompletionOut(
            id=existing.id,
            experiment_id=existing.experiment_id,
            section_key=existing.section_key,
            created_at=existing.created_at,
            completed=True,
        )

    completion = SectionCompletion(
        student_id=current_user.id,
        experiment_id=exp.id,
        section_key=section_key,
    )
    db.add(completion)
    try:
        db.commit()
    except IntegrityError:
        # Concurrent/double requests may race on the unique constraint. Treat an
        # existing row as success; never claim success without a persisted row.
        db.rollback()
        existing = db.query(SectionCompletion).filter(
            SectionCompletion.student_id == current_user.id,
            SectionCompletion.experiment_id == exp.id,
            SectionCompletion.section_key == section_key,
        ).first()
        if existing is None:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Could not save section completion. Please retry.",
            )
        completion = existing
    else:
        db.refresh(completion)

    return SectionCompletionOut(
        id=completion.id,
        experiment_id=completion.experiment_id,
        section_key=completion.section_key,
        created_at=completion.created_at,
        completed=True,
    )


# ── Update ───────────────────────────────────────────────────────────────────

@router.patch("/{slug}", response_model=ExperimentOut)
def update_experiment(
    slug: str,
    payload: ExperimentUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(UserRole.admin)),
):
    exp = _get_experiment_or_404(slug, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exp, field, value)
    db.commit()
    db.refresh(exp)
    return exp


# ── Evaluation spec (admin-only, never student-facing) ───────────────────────

@router.post("/{experiment_id}/evaluation-spec", status_code=status.HTTP_201_CREATED)
def set_evaluation_spec(
    experiment_id: uuid.UUID,
    payload: EvalSpecCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(UserRole.admin)),
):
    """Set or replace the hidden expected output for an experiment's code exercise.
    The spec is NEVER returned in any student-facing response."""
    exp = db.get(Experiment, experiment_id)
    if exp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiment not found")

    spec = exp.evaluation_spec
    if spec is None:
        spec = ExperimentEvaluationSpec(experiment_id=experiment_id)
        db.add(spec)

    spec.expected_output = payload.expected_output
    spec.comparison_tolerance = payload.comparison_tolerance
    db.commit()
    return {"detail": "Evaluation spec saved"}
