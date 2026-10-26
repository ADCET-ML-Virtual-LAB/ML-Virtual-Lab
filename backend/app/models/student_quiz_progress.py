"""Best-score-only records for student Pre-Quiz and Post-Quiz self-assessments.

Unlike QuizSubmission, this table does not keep one row per attempt or store
submitted answer choices. A single row records that the student has submitted
the quiz and the best score achieved so far.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TimestampMixin, UUIDPKMixin


class StudentQuizProgress(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "student_quiz_progress"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False
    )
    best_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # This is the most recent successful submission time, not an attempt history.
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "quiz_id", name="uq_student_quiz_progress"),
    )

    student = relationship("User")
    quiz = relationship("Quiz")
