"""Pydantic schemas for student and instructor dashboard views (Modules 7 & 8)."""
import uuid
from typing import Optional

from pydantic import BaseModel


class StepStatus:
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    not_tracked = "not_tracked"


class ExperimentProgress(BaseModel):
    experiment_id: uuid.UUID
    experiment_title: str
    pre_quiz: str  # StepStatus values
    guided_lab: str  # always "not_tracked" until ping endpoint exists
    code_exercise: str
    post_quiz: str
    assignment: str
    assignment_score: Optional[float] = None
    overall_status: str


class InstructorStudentProgress(BaseModel):
    student_id: uuid.UUID
    student_name: str
    roll_number: Optional[str] = None
    experiments: list[ExperimentProgress]
