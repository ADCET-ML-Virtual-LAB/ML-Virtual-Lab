import enum
import uuid
from typing import Optional

from sqlalchemy import String, Text, Integer, Boolean, Enum, ForeignKey, DateTime, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import UUIDPKMixin, TimestampMixin


class QuizType(str, enum.Enum):
    pre = "pre"           # ungraded, before the lab
    post = "post"         # ungraded, after the lab
    assignment = "assignment"  # graded


class RevealPolicy(str, enum.Enum):
    immediate = "immediate"
    after_deadline = "after_deadline"


class Quiz(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "quizzes"

    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    quiz_type: Mapped[QuizType] = mapped_column(Enum(QuizType, name="quiz_type"), nullable=False)
    # is_scored is redundant with quiz_type (only "assignment" is scored) but kept
    # explicit so grading logic never has to branch on the type string.
    is_scored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    deadline: Mapped[Optional["DateTime"]] = mapped_column(DateTime(timezone=True), nullable=True)
    reveal_policy: Mapped[RevealPolicy] = mapped_column(
        Enum(RevealPolicy, name="reveal_policy"), nullable=False, default=RevealPolicy.immediate
    )

    __table_args__ = (UniqueConstraint("experiment_id", "quiz_type", name="uq_experiment_quiz_type"),)

    experiment = relationship("Experiment", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    submissions = relationship("QuizSubmission", back_populates="quiz", cascade="all, delete-orphan")


class Question(Base, UUIDPKMixin):
    __tablename__ = "questions"

    quiz_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quiz = relationship("Quiz", back_populates="questions")
    options = relationship("Option", back_populates="question", cascade="all, delete-orphan")
    answers = relationship("QuizAnswer", back_populates="question")


class Option(Base, UUIDPKMixin):
    __tablename__ = "options"

    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_text: Mapped[str] = mapped_column(String(500), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    question = relationship("Question", back_populates="options")


class QuizSubmission(Base, UUIDPKMixin):
    """One row per (student, quiz) attempt — holds the overall score for assignments."""
    __tablename__ = "quiz_submissions"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quiz_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # null for ungraded pre/post
    submitted_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "quiz_id", "attempt_number", name="uq_student_quiz_attempt"),
    )

    student = relationship("User", back_populates="quiz_submissions")
    quiz = relationship("Quiz", back_populates="submissions")
    answers = relationship("QuizAnswer", back_populates="submission", cascade="all, delete-orphan")


class QuizAnswer(Base, UUIDPKMixin):
    """One row per question, within a QuizSubmission."""
    __tablename__ = "quiz_answers"

    quiz_submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz_submissions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_option_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("options.id", ondelete="CASCADE"), nullable=False
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)

    submission = relationship("QuizSubmission", back_populates="answers")
    question = relationship("Question", back_populates="answers")
