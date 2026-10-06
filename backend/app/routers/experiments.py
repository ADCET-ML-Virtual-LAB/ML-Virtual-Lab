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
from app.models.user import UserRole
from app.schemas.experiment import (
    EvalSpecCreate,
    ExperimentCreate,
    ExperimentOut,
    ExperimentUpdate,
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

@router.get("/{slug}", response_model=ExperimentOut)
def get_experiment(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    exp = _get_experiment_or_404(slug, db)
    # Students may only view published experiments
    if current_user.role == UserRole.student and not exp.is_published:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiment not found")
    return exp


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
