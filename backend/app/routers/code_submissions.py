"""
Code submissions router — Module 6 (client-side execution only).

The browser (Pyodide/WASM in a Web Worker) has already executed the student's
code; this endpoint receives the output the client computed, compares it against
the hidden ExperimentEvaluationSpec, records the result and returns feedback.
Student code NEVER runs on this server.

Endpoints:
  POST  /code_submissions           record result of a client-executed submission
  GET   /code_submissions           list own submission history for an experiment
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models import User
from app.models.code_submission import CodeSubmission, SubmissionStatus
from app.models.experiment import Experiment, ExperimentEvaluationSpec
from app.schemas.code_submission import CodeSubmissionCreate, CodeSubmissionOut
from datetime import datetime, timezone

router = APIRouter(prefix="/code_submissions", tags=["code_submissions"])


def _compare_output(client_output, expected_output, tolerance: float | None) -> bool:
    """
    Shallow comparison logic.  The frontend sends whatever Pyodide produced
    (numbers, lists, dicts …).  We do a best-effort comparison:
      • If both are numeric (or both are lists/dicts of numerics), use
        tolerance-based comparison when tolerance is set.
      • Otherwise fall back to equality.
    This is intentionally simple for v1; a dedicated numpy-aware comparator
    can be added later without changing the API contract.
    """
    if client_output is None:
        return False

    if tolerance is not None:
        # Try numeric comparison
        try:
            diff = abs(float(client_output) - float(expected_output))
            return diff <= tolerance
        except (TypeError, ValueError):
            pass

        # Try list comparison element-wise
        if isinstance(client_output, list) and isinstance(expected_output, list):
            if len(client_output) != len(expected_output):
                return False
            try:
                return all(
                    abs(float(a) - float(b)) <= tolerance
                    for a, b in zip(client_output, expected_output)
                )
            except (TypeError, ValueError):
                pass

    return client_output == expected_output


@router.post("", response_model=CodeSubmissionOut, status_code=status.HTTP_201_CREATED)
def create_code_submission(
    payload: CodeSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Record the result of a client-executed code exercise.
    The browser sends what Pyodide computed; we compare and store feedback.
    """
    exp = db.get(Experiment, payload.experiment_id)
    if exp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiment not found")

    spec: ExperimentEvaluationSpec | None = exp.evaluation_spec

    if payload.client_error:
        sub_status = SubmissionStatus.error
        feedback = f"Execution error:\n{payload.client_error}"
    elif spec is None:
        # No spec set yet — record as-is, no comparison possible
        sub_status = SubmissionStatus.mismatched
        feedback = "No evaluation spec configured for this experiment yet."
    else:
        matched = _compare_output(
            payload.client_output,
            spec.expected_output,
            spec.comparison_tolerance,
        )
        sub_status = SubmissionStatus.matched if matched else SubmissionStatus.mismatched
        feedback = (
            "Output matched the expected result. Great work!"
            if matched
            else "Output did not match the expected result. Review your approach and try again."
        )

    submission = CodeSubmission(
        student_id=current_user.id,
        experiment_id=payload.experiment_id,
        submitted_code=payload.submitted_code,
        client_output=payload.client_output,
        client_error=payload.client_error,
        status=sub_status,
        feedback_message=feedback,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("", response_model=list[CodeSubmissionOut])
def list_code_submissions(
    experiment_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return own submission history for one experiment, newest first."""
    return (
        db.query(CodeSubmission)
        .filter(
            CodeSubmission.student_id == current_user.id,
            CodeSubmission.experiment_id == experiment_id,
        )
        .order_by(CodeSubmission.submitted_at.desc())
        .all()
    )
