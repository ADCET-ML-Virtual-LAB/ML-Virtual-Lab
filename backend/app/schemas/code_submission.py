"""Pydantic schemas for code submissions (Module 6 — client-side execution)."""
import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.code_submission import SubmissionStatus


class CodeSubmissionCreate(BaseModel):
    experiment_id: uuid.UUID
    submitted_code: str
    # What Pyodide computed in the browser. Mutually exclusive with client_error.
    client_output: Optional[Any] = None
    # Traceback text, if the browser execution raised.
    client_error: Optional[str] = None


class CodeSubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    experiment_id: uuid.UUID
    status: SubmissionStatus
    feedback_message: Optional[str] = None
    submitted_at: datetime
