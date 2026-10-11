"""Pydantic schemas for experiments and evaluation specs (Module 3 + 6)."""
import uuid
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.quiz import QuizOut


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    overview: Optional[str] = None
    slug: str
    aim: str
    objective: str
    notes: Optional[str] = None
    video_url: Optional[str] = None
    lab_config: Optional[Any] = None
    starter_code: Optional[str] = None
    allowed_imports: Optional[list[str]] = None
    order_index: int
    is_published: bool


class ExperimentDetailOut(ExperimentOut):
    """
    Single-experiment view: the experiment plus its quizzes.

    For a student whose assignment is still locked, the assignment quiz comes back
    with an EMPTY `questions` list and `assignment_locked` is true, so the assignment
    cannot even be viewed until the earlier steps are completed.
    """
    quizzes: list[QuizOut] = []
    assignment_locked: bool = False
    assignment_missing_steps: list[str] = Field(default_factory=list)
    # Student-only status map sourced from saved SectionCompletion rows.
    section_completions: dict[str, bool] = Field(default_factory=dict)
    # Student-only: true once a matching Code Exercise result has been saved.
    code_exercise_completed: bool = False


class ExperimentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    overview: Optional[str] = None
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    aim: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    notes: Optional[str] = None
    video_url: Optional[str] = None
    lab_config: Optional[Any] = None
    starter_code: Optional[str] = None
    allowed_imports: Optional[list[str]] = None
    # Experiments are fixed (1-10); the number is chosen once at creation.
    order_index: int = Field(ge=1, le=10)
    is_published: bool = False


class ExperimentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    overview: Optional[str] = None
    aim: Optional[str] = None
    objective: Optional[str] = None
    notes: Optional[str] = None
    video_url: Optional[str] = None
    lab_config: Optional[Any] = None
    starter_code: Optional[str] = None
    allowed_imports: Optional[list[str]] = None
    is_published: Optional[bool] = None


class EvalSpecCreate(BaseModel):
    """Admin-only: set/replace the hidden expected output for an experiment's code exercise."""
    expected_output: Any  # any JSON-serialisable value
    comparison_tolerance: Optional[float] = None  # for float comparisons
