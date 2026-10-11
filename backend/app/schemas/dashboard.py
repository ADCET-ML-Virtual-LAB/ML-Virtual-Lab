"""Pydantic schemas for student and instructor dashboard views (Modules 7 & 8)."""
import uuid
from typing import Optional

from pydantic import BaseModel, Field


class StepStatus:
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class SectionProgress(BaseModel):
    """One configured section of an experiment and whether its completion is saved."""
    key: str
    completed: bool


class ExperimentProgress(BaseModel):
    """A student's own progress, including manually tracked static sections."""
    experiment_id: uuid.UUID
    experiment_title: str
    experiment_number: int = 0  # fixed experiment number (1-10)
    has_assignment: bool = False
    pre_quiz: str  # StepStatus values
    code_exercise: str
    post_quiz: str
    assignment: str
    assignment_score: Optional[float] = None
    overall_status: str
    section_statuses: dict[str, str] = Field(default_factory=dict)
    # Every configured section in the approved order, for the View Progress page.
    sections: list[SectionProgress] = Field(default_factory=list)


class InstructorExperimentProgress(BaseModel):
    """
    What an instructor sees per student per experiment: the overall status and the graded assignment.
    Pre/post quiz results are the student's own self-assessment and are not sent to instructors.
    """
    experiment_id: uuid.UUID
    experiment_title: str
    overall_status: str  # not_started | in_progress ("Ongoing") | completed
    assignment_status: str  # not_started | completed
    assignment_score: Optional[float] = None


class InstructorStudentProgress(BaseModel):
    student_id: uuid.UUID
    student_name: str
    roll_number: Optional[str] = None
    experiments: list[InstructorExperimentProgress]
