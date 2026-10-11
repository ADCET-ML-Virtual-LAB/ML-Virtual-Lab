"""
Instructor console API. Every endpoint is for instructors only (admins and
students get 403) and is scoped to the batch the instructor is assigned to.

  GET /instructor/batches
  GET /instructor/batches/{batch_id}
  GET /instructor/experiments
  GET /instructor/experiments/{experiment_id}
  GET /instructor/experiments/{experiment_id}/assignment
  GET /instructor/batches/{batch_id}/experiments/{experiment_id}/status
  GET /instructor/batches/{batch_id}/experiments/{experiment_id}/status/export
  GET /instructor/batches/{batch_id}/experiments/{experiment_id}/assignment-status
  GET /instructor/batches/{batch_id}/experiments/{experiment_id}/assignment-status/export
  GET /instructor/batches/{batch_id}/experiments/{experiment_id}/assignment-status/{student_id}

Pre-Quiz and Post-Quiz scores are never returned. Saved assignment scores are
shown immediately (no reveal policy), as a percentage.
"""
import csv
import io
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.database import get_db
from app.models import (
    Batch,
    Enrollment,
    Experiment,
    InstructorAssignment,
    Quiz,
    QuizSubmission,
    QuizType,
    User,
    UserRole,
)
from app.schemas.instructor import (
    InstructorAssignmentContent,
    InstructorAssignmentRow,
    InstructorAssignmentTable,
    InstructorBatchDetail,
    InstructorBatchOut,
    InstructorExperimentContent,
    InstructorExperimentItem,
    InstructorQuestionReview,
    InstructorStatusRow,
    InstructorStatusTable,
    InstructorStudentOut,
    InstructorSubmissionOut,
)
from app.schemas.quiz import OptionOutAdmin, QuizOutAdmin
from app.services.progress import derive_experiment_progress

router = APIRouter(prefix="/instructor", tags=["instructor"])

_instructor_only = require_roles(UserRole.instructor)

STATUS_LABEL = {
    "not_started": "Not Attempted",
    "in_progress": "In Progress",
    "completed": "Completed",
}


# ── Shared helpers ────────────────────────────────────────────────────────────

def _own_batch(batch_id: uuid.UUID, user: User, db: Session) -> Batch:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Batch not found")
    assigned = (
        db.query(InstructorAssignment.id)
        .filter(InstructorAssignment.instructor_id == user.id, InstructorAssignment.batch_id == batch_id)
        .first()
    )
    if assigned is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not assigned to this batch")
    return batch


def _published_experiment(experiment_id: uuid.UUID, db: Session) -> Experiment:
    exp = db.get(Experiment, experiment_id)
    if exp is None or not exp.is_published:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiment not found")
    return exp


def _batch_students(batch_id: uuid.UUID, db: Session) -> list[User]:
    students = (
        db.query(User)
        .join(Enrollment, Enrollment.student_id == User.id)
        .filter(Enrollment.batch_id == batch_id)
        .all()
    )
    return sorted(students, key=lambda s: ((s.roll_number or "").lower(), s.full_name.lower()))


def _student_out(s: User) -> InstructorStudentOut:
    return InstructorStudentOut(id=s.id, urn=s.roll_number, full_name=s.full_name)


def _quiz_of(exp: Experiment, quiz_type: QuizType) -> Quiz | None:
    return next((q for q in exp.quizzes if q.quiz_type == quiz_type), None)


def _quiz_with_answers(quiz: Quiz | None) -> QuizOutAdmin | None:
    """Answer-key view of a quiz, questions and options in their configured order."""
    if quiz is None:
        return None
    out = QuizOutAdmin.model_validate(quiz)
    out.questions.sort(key=lambda q: q.order_index)
    for question in out.questions:
        question.options.sort(key=lambda o: o.order_index)
    return out


def _submission(student_id: uuid.UUID, quiz: Quiz, db: Session) -> QuizSubmission | None:
    return (
        db.query(QuizSubmission)
        .filter(QuizSubmission.student_id == student_id, QuizSubmission.quiz_id == quiz.id)
        .order_by(QuizSubmission.attempt_number.desc())
        .first()
    )


def _percent(score: float | None) -> str:
    return "Not Submitted" if score is None else f"{score:g}%"


def _safe_cell(value: str) -> str:
    """Stop spreadsheet apps treating a text cell as a formula."""
    return "'" + value if value[:1] in ("=", "+", "-", "@") else value


def _csv_response(batch: Batch, exp: Experiment, kind: str, header: list[str], rows: list[list[str]]):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for row in rows:
        writer.writerow([_safe_cell(str(cell)) for cell in row])
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", f"{batch.name}_{batch.academic_year}")
    filename = f"batch_{safe}_experiment_{exp.order_index}_{kind}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _status_rows(batch_id: uuid.UUID, exp: Experiment, db: Session) -> list[InstructorStatusRow]:
    rows = []
    for s in _batch_students(batch_id, db):
        progress = derive_experiment_progress(s.id, [exp], db, student_view=True)
        rows.append(InstructorStatusRow(
            student_id=s.id, urn=s.roll_number, full_name=s.full_name,
            status=progress[0].overall_status,
        ))
    return rows


def _assignment_rows(batch_id: uuid.UUID, quiz: Quiz | None, db: Session) -> list[InstructorAssignmentRow]:
    rows = []
    for s in _batch_students(batch_id, db):
        sub = _submission(s.id, quiz, db) if quiz is not None else None
        rows.append(InstructorAssignmentRow(
            student_id=s.id, urn=s.roll_number, full_name=s.full_name,
            submitted=sub is not None,
            score=sub.score if sub is not None else None,
        ))
    return rows


# ── Batches ───────────────────────────────────────────────────────────────────

@router.get("/batches", response_model=list[InstructorBatchOut])
def list_my_batches(db: Session = Depends(get_db), user: User = Depends(_instructor_only)):
    batches = (
        db.query(Batch)
        .join(InstructorAssignment, InstructorAssignment.batch_id == Batch.id)
        .filter(InstructorAssignment.instructor_id == user.id)
        .order_by(Batch.created_at.desc())
        .all()
    )
    return [InstructorBatchOut(id=b.id, name=b.name, academic_year=b.academic_year) for b in batches]


@router.get("/batches/{batch_id}", response_model=InstructorBatchDetail)
def get_my_batch(batch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(_instructor_only)):
    batch = _own_batch(batch_id, user, db)
    return InstructorBatchDetail(
        id=batch.id,
        name=batch.name,
        academic_year=batch.academic_year,
        instructor_name=user.full_name,
        students=[_student_out(s) for s in _batch_students(batch.id, db)],
    )


# ── Experiment content (read-only) ────────────────────────────────────────────

@router.get("/experiments", response_model=list[InstructorExperimentItem])
def list_published_experiments(db: Session = Depends(get_db), _user: User = Depends(_instructor_only)):
    exps = (
        db.query(Experiment).filter(Experiment.is_published == True)  # noqa: E712
        .order_by(Experiment.order_index).all()
    )
    return [InstructorExperimentItem(id=e.id, number=e.order_index, title=e.title, slug=e.slug) for e in exps]


@router.get("/experiments/{experiment_id}", response_model=InstructorExperimentContent)
def get_experiment_content(
    experiment_id: uuid.UUID, db: Session = Depends(get_db), _user: User = Depends(_instructor_only)
):
    exp = _published_experiment(experiment_id, db)
    return InstructorExperimentContent(
        id=exp.id, number=exp.order_index, title=exp.title, slug=exp.slug,
        overview=exp.overview, aim=exp.aim, objective=exp.objective,
        notes=exp.notes, video_url=exp.video_url,
        pre_quiz=_quiz_with_answers(_quiz_of(exp, QuizType.pre)),
        post_quiz=_quiz_with_answers(_quiz_of(exp, QuizType.post)),
        assignment=_quiz_with_answers(_quiz_of(exp, QuizType.assignment)),
    )


@router.get("/experiments/{experiment_id}/assignment", response_model=InstructorAssignmentContent)
def get_assignment_content(
    experiment_id: uuid.UUID, db: Session = Depends(get_db), _user: User = Depends(_instructor_only)
):
    exp = _published_experiment(experiment_id, db)
    return InstructorAssignmentContent(
        experiment_id=exp.id, experiment_number=exp.order_index, experiment_title=exp.title,
        assignment=_quiz_with_answers(_quiz_of(exp, QuizType.assignment)),
    )


# ── Students Status (per experiment) ──────────────────────────────────────────

@router.get("/batches/{batch_id}/experiments/{experiment_id}/status", response_model=InstructorStatusTable)
def experiment_status_table(
    batch_id: uuid.UUID, experiment_id: uuid.UUID,
    db: Session = Depends(get_db), user: User = Depends(_instructor_only),
):
    batch = _own_batch(batch_id, user, db)
    exp = _published_experiment(experiment_id, db)
    return InstructorStatusTable(
        experiment_number=exp.order_index, experiment_title=exp.title,
        rows=_status_rows(batch.id, exp, db),
    )


@router.get("/batches/{batch_id}/experiments/{experiment_id}/status/export")
def export_experiment_status(
    batch_id: uuid.UUID, experiment_id: uuid.UUID,
    db: Session = Depends(get_db), user: User = Depends(_instructor_only),
):
    batch = _own_batch(batch_id, user, db)
    exp = _published_experiment(experiment_id, db)
    rows = [
        [batch.name, batch.academic_year, exp.order_index, exp.title,
         r.urn or "", r.full_name, STATUS_LABEL[r.status]]
        for r in _status_rows(batch.id, exp, db)
    ]
    header = ["Batch", "Academic Year", "Experiment No.", "Experiment Title", "URN", "Student Name", "Status"]
    return _csv_response(batch, exp, "status", header, rows)


# ── Assignment Status (per experiment's assignment) ───────────────────────────

@router.get(
    "/batches/{batch_id}/experiments/{experiment_id}/assignment-status",
    response_model=InstructorAssignmentTable,
)
def assignment_status_table(
    batch_id: uuid.UUID, experiment_id: uuid.UUID,
    db: Session = Depends(get_db), user: User = Depends(_instructor_only),
):
    batch = _own_batch(batch_id, user, db)
    exp = _published_experiment(experiment_id, db)
    quiz = _quiz_of(exp, QuizType.assignment)
    return InstructorAssignmentTable(
        experiment_number=exp.order_index, experiment_title=exp.title,
        has_assignment=quiz is not None,
        rows=_assignment_rows(batch.id, quiz, db) if quiz is not None else [],
    )


@router.get("/batches/{batch_id}/experiments/{experiment_id}/assignment-status/export")
def export_assignment_status(
    batch_id: uuid.UUID, experiment_id: uuid.UUID,
    db: Session = Depends(get_db), user: User = Depends(_instructor_only),
):
    batch = _own_batch(batch_id, user, db)
    exp = _published_experiment(experiment_id, db)
    quiz = _quiz_of(exp, QuizType.assignment)
    if quiz is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This experiment has no assignment")
    rows = [
        [batch.name, batch.academic_year, exp.order_index, exp.title,
         r.urn or "", r.full_name, _percent(r.score)]
        for r in _assignment_rows(batch.id, quiz, db)
    ]
    header = ["Batch", "Academic Year", "Experiment No.", "Experiment Title", "URN", "Student Name", "Marks (%)"]
    return _csv_response(batch, exp, "assignment_scores", header, rows)


@router.get(
    "/batches/{batch_id}/experiments/{experiment_id}/assignment-status/{student_id}",
    response_model=InstructorSubmissionOut,
)
def view_submission(
    batch_id: uuid.UUID, experiment_id: uuid.UUID, student_id: uuid.UUID,
    db: Session = Depends(get_db), user: User = Depends(_instructor_only),
):
    """One student's saved assignment submission: answers, answer key and correctness."""
    batch = _own_batch(batch_id, user, db)
    exp = _published_experiment(experiment_id, db)
    quiz = _quiz_of(exp, QuizType.assignment)
    if quiz is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This experiment has no assignment")

    enrolled = next((s for s in _batch_students(batch.id, db) if s.id == student_id), None)
    if enrolled is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found in this batch")

    submission = _submission(student_id, quiz, db)
    if submission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This assignment has not been submitted")

    answers = {a.question_id: a for a in submission.answers}
    questions = []
    for question in sorted(quiz.questions, key=lambda q: q.order_index):
        answer = answers.get(question.id)
        questions.append(InstructorQuestionReview(
            question_id=question.id,
            question_text=question.question_text,
            options=[OptionOutAdmin.model_validate(o) for o in sorted(question.options, key=lambda o: o.order_index)],
            selected_option_id=answer.selected_option_id if answer else None,
            is_correct=bool(answer and answer.is_correct),
        ))
    return InstructorSubmissionOut(
        experiment_number=exp.order_index, experiment_title=exp.title,
        student=_student_out(enrolled), score=submission.score, questions=questions,
    )
