"""Pydantic schemas for quizzes, questions, options and submissions (Module 4)."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.quiz import QuizType, RevealPolicy


# ── Option ──────────────────────────────────────────────────────────────────

class OptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    option_text: str
    order_index: int
    # is_correct intentionally omitted — stripped for students in the router


class OptionOutAdmin(OptionOut):
    """Admin/Instructor view — includes is_correct."""
    is_correct: bool


class OptionCreate(BaseModel):
    option_text: str = Field(min_length=1)
    is_correct: bool = False
    order_index: int = 0


# ── Question ─────────────────────────────────────────────────────────────────

class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    question_text: str
    order_index: int
    options: list[OptionOut]


class QuestionOutAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    question_text: str
    order_index: int
    options: list[OptionOutAdmin]


class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=1)
    order_index: int = 0
    options: list[OptionCreate] = Field(min_length=2)


# ── Quiz ──────────────────────────────────────────────────────────────────────

class QuizOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    experiment_id: uuid.UUID
    quiz_type: QuizType
    is_scored: bool
    title: str
    deadline: Optional[datetime] = None
    reveal_policy: RevealPolicy
    questions: list[QuestionOut]


class QuizOutAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    experiment_id: uuid.UUID
    quiz_type: QuizType
    is_scored: bool
    title: str
    deadline: Optional[datetime] = None
    reveal_policy: RevealPolicy
    questions: list[QuestionOutAdmin]


class QuizCreate(BaseModel):
    quiz_type: QuizType
    title: str = Field(min_length=1, max_length=200)
    deadline: Optional[datetime] = None
    reveal_policy: RevealPolicy = RevealPolicy.immediate
    questions: list[QuestionCreate] = Field(min_length=1)


# ── Submission ────────────────────────────────────────────────────────────────

class QuizAnswerInput(BaseModel):
    question_id: uuid.UUID
    selected_option_id: uuid.UUID


class QuizSubmitRequest(BaseModel):
    answers: list[QuizAnswerInput] = Field(min_length=1)


class QuizAnswerResult(BaseModel):
    question_id: uuid.UUID
    is_correct: bool


class QuizSubmitResponse(BaseModel):
    attempt_number: int
    score: Optional[float] = None  # None for ungraded pre/post
    answers: list[QuizAnswerResult]
