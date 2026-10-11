"""
Dashboards router — Module 7 (Instructor) + Module 8 (Student).

Endpoints:
  GET  /dashboards/student              own progress across experiments (students only)
  GET  /dashboards/instructor           batch students' progress (admin/instructor)
  GET  /dashboards/instructor/export    same data as CSV (admin/instructor)
"""
import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.database import get_db
from app.models import User
from app.models.batch import Batch, Enrollment, InstructorAssignment
from app.models.experiment import Experiment
from app.models.user import UserRole
from app.schemas.dashboard import ExperimentProgress, InstructorExperimentProgress, InstructorStudentProgress
from app.services.progress import derive_experiment_progress

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


def _get_published_experiments(db: Session) -> list[Experiment]:
    return db.query(Experiment).filter(Experiment.is_published == True).order_by(Experiment.order_index).all()  # noqa: E712


def _assert_batch_access(batch_id: uuid.UUID, user: User, db: Session) -> Batch:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Batch not found")
    if user.role == UserRole.admin:
        return batch
    assigned = (
        db.query(InstructorAssignment)
        .filter(
            InstructorAssignment.instructor_id == user.id,
            InstructorAssignment.batch_id == batch_id,
        )
        .first()
    )
    if assigned is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not assigned to this batch")
    return batch


def _for_instructor(progress: list[ExperimentProgress]) -> list[InstructorExperimentProgress]:
    """Instructors get the overall status and the assignment only; pre/post quiz detail stays private to the student."""
    return [
        InstructorExperimentProgress(
            experiment_id=p.experiment_id,
            experiment_title=p.experiment_title,
            overall_status=p.overall_status,
            assignment_status=p.assignment,
            assignment_score=p.assignment_score,
        )
        for p in progress
    ]


# ── Student dashboard ─────────────────────────────────────────────────────────

@router.get("/student", response_model=list[ExperimentProgress])
def student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
):
    """Own progress and assignment scores across all published experiments. Students only."""
    experiments = _get_published_experiments(db)
    return derive_experiment_progress(current_user.id, experiments, db, student_view=True)


# ── Instructor dashboard ──────────────────────────────────────────────────────

@router.get("/instructor", response_model=list[InstructorStudentProgress])
def instructor_dashboard(
    batch_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.instructor)),
):
    """Per-student overall status and assignment status/score for all students in a batch."""
    _assert_batch_access(batch_id, user, db)

    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.batch_id == batch_id)
        .all()
    )
    experiments = _get_published_experiments(db)

    result = []
    for enrollment in enrollments:
        student = enrollment.student
        progress = derive_experiment_progress(student.id, experiments, db)
        result.append(InstructorStudentProgress(
            student_id=student.id,
            student_name=student.full_name,
            roll_number=student.roll_number,
            experiments=_for_instructor(progress),
        ))
    return result


# ── CSV export ────────────────────────────────────────────────────────────────

@router.get("/instructor/export")
def export_instructor_dashboard(
    batch_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.instructor)),
):
    """Assignment status and score per experiment, as a downloadable CSV."""
    batch = _assert_batch_access(batch_id, user, db)

    enrollments = (
        db.query(Enrollment).filter(Enrollment.batch_id == batch_id).all()
    )
    experiments = _get_published_experiments(db)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    exp_cols = []
    for exp in experiments:
        short = exp.slug[:20]
        exp_cols += [f"{short}_assignment", f"{short}_score"]
    writer.writerow(["student_name", "roll_number", "email"] + exp_cols)

    for enrollment in enrollments:
        student = enrollment.student
        progress_list = derive_experiment_progress(student.id, experiments, db)
        row = [student.full_name, student.roll_number or "", student.email]
        for p in progress_list:
            row += [p.assignment, p.assignment_score if p.assignment_score is not None else ""]
        writer.writerow(row)

    output.seek(0)
    filename = f"batch_{batch.name}_{batch.academic_year}_progress.csv".replace(" ", "_")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
