"""Response schemas for the instructor console (instructors only).

Pre-Quiz and Post-Quiz scores are deliberately absent from every schema here.
Answer keys (is_correct) appear only because these endpoints are instructor-only.
"""
import uuid
from typing import Optional

from pydantic import BaseModel

from app.schemas.quiz import OptionOutAdmin, QuizOutAdmin


class InstructorBatchOut(BaseModel):
    id: uuid.UUID
    name: str
    academic_year: str


class InstructorStudentOut(BaseModel):
    id: uuid.UUID
    urn: Optional[str] = None  # the student's roll number / URN
    full_name: str


class InstructorBatchDetail(BaseModel):
    id: uuid.UUID
    name: str
    academic_year: str
    instructor_name: str
    students: list[InstructorStudentOut]


class InstructorExperimentItem(BaseModel):
    id: uuid.UUID
    number: int
    title: str
    slug: str


class InstructorExperimentContent(InstructorExperimentItem):
    """Read-only experiment content: the student sections minus Guided Lab and Code Exercise."""
    overview: Optional[str] = None
    aim: str
    objective: str
    notes: Optional[str] = None  # Theory / Reading Material
    video_url: Optional[str] = None
    pre_quiz: Optional[QuizOutAdmin] = None
    post_quiz: Optional[QuizOutAdmin] = None
    assignment: Optional[QuizOutAdmin] = None


class InstructorAssignmentContent(BaseModel):
    experiment_id: uuid.UUID
    experiment_number: int
    experiment_title: str
    assignment: Optional[QuizOutAdmin] = None  # None when the experiment has no assignment


class InstructorStatusRow(BaseModel):
    student_id: uuid.UUID
    urn: Optional[str] = None
    full_name: str
    status: str  # not_started | in_progress | completed


class InstructorStatusTable(BaseModel):
    experiment_number: int
    experiment_title: str
    rows: list[InstructorStatusRow]


class InstructorAssignmentRow(BaseModel):
    student_id: uuid.UUID
    urn: Optional[str] = None
    full_name: str
    submitted: bool
    score: Optional[float] = None  # percentage 0-100; None when not submitted


class InstructorAssignmentTable(BaseModel):
    experiment_number: int
    experiment_title: str
    has_assignment: bool
    rows: list[InstructorAssignmentRow]


class InstructorQuestionReview(BaseModel):
    question_id: uuid.UUID
    question_text: str
    options: list[OptionOutAdmin]
    selected_option_id: Optional[uuid.UUID] = None
    is_correct: bool


class InstructorSubmissionOut(BaseModel):
    experiment_number: int
    experiment_title: str
    student: InstructorStudentOut
    score: Optional[float] = None
    questions: list[InstructorQuestionReview]
