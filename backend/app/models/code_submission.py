import enum
import uuid
from typing import Optional

from sqlalchemy import Text, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import UUIDPKMixin


class SubmissionStatus(str, enum.Enum):
    matched = "matched"        # client output matched expected_output within tolerance
    mismatched = "mismatched"
    error = "error"            # code raised an error in the browser


class CodeSubmission(Base, UUIDPKMixin):
    """
    Execution itself happens entirely client-side (Pyodide/WASM, in a Web
    Worker — no student code ever runs on our servers). The browser posts
    the code it ran plus the output it produced; the backend only does a
    cheap value/shape comparison against ExperimentEvaluationSpec, which
    the client never sees. This keeps the server load near-zero while
    still hiding the expected answer from students.
    """
    __tablename__ = "code_submissions"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    submitted_code: Mapped[str] = mapped_column(Text, nullable=False)
    client_output: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # what the browser computed
    client_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # traceback, if execution failed
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus, name="submission_status"), nullable=False)
    feedback_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User", back_populates="code_submissions")
    experiment = relationship("Experiment", back_populates="code_submissions")
