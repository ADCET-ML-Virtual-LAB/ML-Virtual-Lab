"""
Import every model here so `Base.metadata` knows about all tables when
`create_all` (or Alembic autogenerate) runs, and so `from app.models import X`
works from anywhere in the app.
"""
from app.models.user import User, UserRole, RefreshToken
from app.models.batch import Batch, Enrollment, InstructorAssignment, RosterEntry
from app.models.experiment import Experiment, ExperimentEvaluationSpec
from app.models.quiz import (
    Quiz,
    QuizType,
    RevealPolicy,
    Question,
    Option,
    QuizSubmission,
    QuizAnswer,
)
from app.models.code_submission import CodeSubmission, SubmissionStatus

__all__ = [
    "User", "UserRole", "RefreshToken",
    "Batch", "Enrollment", "InstructorAssignment", "RosterEntry",
    "Experiment", "ExperimentEvaluationSpec",
    "Quiz", "QuizType", "RevealPolicy", "Question", "Option", "QuizSubmission", "QuizAnswer",
    "CodeSubmission", "SubmissionStatus",
]
