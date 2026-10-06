import uuid
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import UUIDPKMixin, TimestampMixin


class Batch(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "batches"

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "TE-CSE-A"
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2026-27"

    __table_args__ = (UniqueConstraint("name", "academic_year", name="uq_batch_name_year"),)

    enrollments = relationship("Enrollment", back_populates="batch")
    instructor_assignments = relationship("InstructorAssignment", back_populates="batch")


class Enrollment(Base, UUIDPKMixin):
    """Student <-> Batch."""
    __tablename__ = "enrollments"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    enrolled_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("student_id", "batch_id", name="uq_student_batch"),)

    student = relationship("User", back_populates="enrollments", foreign_keys=[student_id])
    batch = relationship("Batch", back_populates="enrollments")


class InstructorAssignment(Base, UUIDPKMixin):
    """Instructor <-> Batch. An instructor's dashboard is scoped to these batches only."""
    __tablename__ = "instructor_assignments"

    instructor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("instructor_id", "batch_id", name="uq_instructor_batch"),)

    instructor = relationship("User", back_populates="instructor_assignments", foreign_keys=[instructor_id])
    batch = relationship("Batch", back_populates="instructor_assignments")
