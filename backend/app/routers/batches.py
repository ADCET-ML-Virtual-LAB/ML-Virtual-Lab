import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import require_roles
from app.core.mailer import send_credentials_emails
from app.core.security import generate_default_password, hash_password
from app.database import get_db
from app.models import Batch, Enrollment, InstructorAssignment, User, UserRole
from app.schemas.batch import (
    BatchCreate,
    BatchOut,
    StudentUploadRequest,
    StudentUploadResponse,
    StudentUploadRowResult,
)

router = APIRouter(prefix="/batches", tags=["batches"])


def _get_batch_or_404(batch_id: uuid.UUID, db: Session) -> Batch:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Batch not found")
    return batch


def _assert_can_manage_batch(batch_id: uuid.UUID, user: User, db: Session) -> None:
    """Admin can manage any batch; an instructor only their own assigned batch(es)."""
    if user.role == UserRole.admin:
        return
    assigned = (
        db.query(InstructorAssignment)
        .filter(InstructorAssignment.instructor_id == user.id, InstructorAssignment.batch_id == batch_id)
        .first()
    )
    if assigned is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not assigned to this batch")


@router.post("", response_model=BatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: BatchCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(UserRole.admin)),
):
    batch = Batch(name=payload.name, academic_year=payload.academic_year)
    db.add(batch)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This batch (name + academic year) already exists")
    db.refresh(batch)
    return batch


@router.get("", response_model=list[BatchOut])
def list_batches(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin, UserRole.instructor)),
):
    return db.query(Batch).order_by(Batch.created_at.desc()).all()


@router.get("/{batch_id}", response_model=BatchOut)
def get_batch(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin, UserRole.instructor)),
):
    return _get_batch_or_404(batch_id, db)


@router.post("/{batch_id}/students", response_model=StudentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_students(
    batch_id: uuid.UUID,
    payload: StudentUploadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.instructor)),
):
    """
    Creates one User (role=student, must_change_password=True) per row not
    already registered, enrolls them in this batch, and queues a
    background email with a generated default password for each new
    account. Rows for an email that already has a User are reported as
    "already_exists" / "already_in_batch" and are never emailed again here
    -- use a future "resend credentials" endpoint for that.
    """
    batch = _get_batch_or_404(batch_id, db)
    _assert_can_manage_batch(batch.id, user, db)

    if len(payload.students) > settings.MAX_UPLOAD_ROWS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Too many rows in one upload (max {settings.MAX_UPLOAD_ROWS}); split the file",
        )

    rows: list[StudentUploadRowResult] = []
    to_email: list[dict] = []
    created = 0

    for student in payload.students:
        email = student.email.lower()
        existing = db.query(User).filter(User.email == email).first()

        if existing is not None:
            already_enrolled = (
                db.query(Enrollment)
                .filter(Enrollment.student_id == existing.id, Enrollment.batch_id == batch.id)
                .first()
            )
            if already_enrolled is None:
                db.add(Enrollment(student_id=existing.id, batch_id=batch.id))
                rows.append(StudentUploadRowResult(email=email, status="already_exists"))
            else:
                rows.append(StudentUploadRowResult(email=email, status="already_in_batch"))
            continue

        plain_password = generate_default_password()
        new_user = User(
            full_name=student.full_name.strip(),
            email=email,
            roll_number=student.roll_number,
            password_hash=hash_password(plain_password),
            role=UserRole.student,
            must_change_password=True,
        )
        db.add(new_user)
        db.flush()  # get new_user.id without committing yet
        db.add(Enrollment(student_id=new_user.id, batch_id=batch.id))

        to_email.append(
            {"user_id": new_user.id, "email": email, "full_name": new_user.full_name, "password": plain_password}
        )
        rows.append(StudentUploadRowResult(email=email, status="created"))
        created += 1

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "One of these emails or roll numbers was just registered by someone else — re-check the file and retry",
        )

    background_tasks.add_task(send_credentials_emails, to_email)

    return StudentUploadResponse(created=created, skipped=len(rows) - created, rows=rows)
