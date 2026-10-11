"""Pydantic schemas for experiments and evaluation specs (Module 3 + 6)."""
import uuid
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.quiz import QuizOut


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
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
    assignment_missing_steps: list[str] = []  # e.g. ["Pre-Quiz", "Code Exercise"]


class ExperimentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    aim: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    notes: Optional[str] = None
    video_url: Optional[str] = None
    lab_config: Optional[Any] = None
    starter_code: Optional[str] = None
    allowed_imports: Optional[list[str]] = None
    order_index: int = 0
    is_published: bool = False


class ExperimentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    aim: Optional[str] = None
    objective: Optional[str] = None
    notes: Optional[str] = None
    video_url: Optional[str] = None
    lab_config: Optional[Any] = None
    starter_code: Optional[str] = None
    allowed_imports: Optional[list[str]] = None
    order_index: Optional[int] = None
    is_published: Optional[bool] = None


class EvalSpecCreate(BaseModel):
    """Admin-only: set/replace the hidden expected output for an experiment's code exercise."""
    expected_output: Any  # any JSON-serialisable value
    comparison_tolerance: Optional[float] = None  # for float comparisons
