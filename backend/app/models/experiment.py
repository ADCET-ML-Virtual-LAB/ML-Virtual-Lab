import uuid
from typing import Optional

from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import UUIDPKMixin, TimestampMixin


class Experiment(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "experiments"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    aim: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # markdown
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Module 5 — Guided/Parametric Lab: sliders/inputs shown to the student
    # and how they map to a client-side computation (e.g. which algorithm,
    # parameter ranges, chart type).
    lab_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Module 6 — Free-form Code Editor. Since execution now happens fully in
    # the student's browser (Pyodide), the backend never runs student code.
    # starter_code seeds the editor; allowed_imports is the whitelist the
    # frontend enforces before running a cell.
    starter_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allowed_imports: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)  # e.g. ["numpy","pandas"]

    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    quizzes = relationship("Quiz", back_populates="experiment", cascade="all, delete-orphan")
    code_submissions = relationship("CodeSubmission", back_populates="experiment")
    evaluation_spec = relationship(
        "ExperimentEvaluationSpec", back_populates="experiment", uselist=False, cascade="all, delete-orphan"
    )


class ExperimentEvaluationSpec(Base, UUIDPKMixin):
    """
    The "answer key" for an experiment's code exercise, kept in its own
    table (and its own, admin-only Pydantic schema) so it is never
    accidentally serialised into a student-facing API response — even
    though execution is client-side, the expected result must stay hidden
    or the ungraded feedback becomes trivially gameable.
    """
    __tablename__ = "experiment_evaluation_specs"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    expected_output: Mapped[dict] = mapped_column(JSONB, nullable=False)  # precomputed offline by the team
    comparison_tolerance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # for value comparisons

    experiment = relationship("Experiment", back_populates="evaluation_spec")
