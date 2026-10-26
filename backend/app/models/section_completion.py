"""Persisted completion records for manually tracked experiment sections."""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import UUIDPKMixin, TimestampMixin


class SectionCompletion(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "section_completions"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )
    section_key: Mapped[str] = mapped_column(String(80), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "student_id", "experiment_id", "section_key",
            name="uq_student_experiment_section_completion",
        ),
        Index("ix_section_completion_student_experiment", "student_id", "experiment_id"),
    )

    student = relationship("User", back_populates="section_completions")
    experiment = relationship("Experiment", back_populates="section_completion_records")
