"""Progress derivation and assignment-prerequisite checks.

Manually tracked sections are read from SectionCompletion rows. Pre/post quiz
completion comes from best-score-only StudentQuizProgress rows. Code exercise and
assignment completion are derived from their persisted result/submission records.
"""
import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy.orm import Session

from app.models.code_submission import CodeSubmission, SubmissionStatus
from app.models.experiment import Experiment
from app.models.quiz import Quiz, QuizSubmission, QuizType, RevealPolicy
from app.models.student_quiz_progress import StudentQuizProgress
from app.schemas.dashboard import ExperimentProgress
from app.services.section_tracking import (
    STATIC_SECTION_LABELS,
    get_completed_section_keys,
)

_NS = "not_started"
_IP = "in_progress"
_CO = "completed"


def derive_experiment_progress(
    student_id: uuid.UUID,
    experiments: Sequence[Experiment],
    db: Session,
    *,
    student_view: bool = False,
) -> list[ExperimentProgress]:
    """Return one progress entry per published experiment.

    ``student_view`` makes the assignment score visible immediately to the
    student after submission. Instructor-facing calls retain the configured
    reveal policy; their response schema still excludes pre/post quiz scores.
    """
    results: list[ExperimentProgress] = []

    for exp in experiments:
        if not exp.is_published:
            continue

        quizzes_by_type: dict[str, Quiz] = {q.quiz_type.value: q for q in exp.quizzes}
        completed_static = get_completed_section_keys(student_id, exp.id, db)
        section_statuses = {
            key: (_CO if key in completed_static else _NS)
            for key in STATIC_SECTION_LABELS
        }

        # Pre-quiz: the single best-score record means at least one submission occurred.
        pre_q = quizzes_by_type.get(QuizType.pre.value)
        pre_quiz_status = _NS
        if pre_q:
            has_sub = db.query(StudentQuizProgress.id).filter(
                StudentQuizProgress.student_id == student_id,
                StudentQuizProgress.quiz_id == pre_q.id,
            ).first() is not None
            pre_quiz_status = _CO if has_sub else _NS

        # Code exercise: once any valid matching result is saved, it stays complete.
        code_status = _NS
        if exp.evaluation_spec is not None:
            has_match = db.query(CodeSubmission.id).filter(
                CodeSubmission.student_id == student_id,
                CodeSubmission.experiment_id == exp.id,
                CodeSubmission.status == SubmissionStatus.matched,
            ).first() is not None
            if has_match:
                code_status = _CO
            else:
                has_attempt = db.query(CodeSubmission.id).filter(
                    CodeSubmission.student_id == student_id,
                    CodeSubmission.experiment_id == exp.id,
                ).first() is not None
                code_status = _IP if has_attempt else _NS

        # Post-quiz: the single best-score record means at least one submission occurred.
        post_q = quizzes_by_type.get(QuizType.post.value)
        post_quiz_status = _NS
        if post_q:
            has_sub = db.query(StudentQuizProgress.id).filter(
                StudentQuizProgress.student_id == student_id,
                StudentQuizProgress.quiz_id == post_q.id,
            ).first() is not None
            post_quiz_status = _CO if has_sub else _NS

        # Assignment: any accepted submission makes it complete regardless of score.
        assignment_status = _NS
        assignment_score: float | None = None
        asgn_q = quizzes_by_type.get(QuizType.assignment.value)
        if asgn_q:
            latest_sub = (
                db.query(QuizSubmission)
                .filter(
                    QuizSubmission.student_id == student_id,
                    QuizSubmission.quiz_id == asgn_q.id,
                )
                .order_by(QuizSubmission.attempt_number.desc())
                .first()
            )
            if latest_sub:
                assignment_status = _CO
                if student_view or score_is_revealed(asgn_q):
                    assignment_score = latest_sub.score

        # Every configured static section is required. Activity sections are
        # included only when that activity exists for the experiment.
        trackable = list(section_statuses.values())
        if pre_q:
            trackable.append(pre_quiz_status)
        if exp.evaluation_spec is not None:
            trackable.append(code_status)
        if post_q:
            trackable.append(post_quiz_status)
        if asgn_q:
            trackable.append(assignment_status)

        overall = _CO if trackable and all(s == _CO for s in trackable) else (
            _IP if any(s != _NS for s in trackable) else _NS
        )

        results.append(ExperimentProgress(
            experiment_id=exp.id,
            experiment_title=exp.title,
            pre_quiz=pre_quiz_status,
            code_exercise=code_status,
            post_quiz=post_quiz_status,
            assignment=assignment_status,
            assignment_score=assignment_score,
            overall_status=overall,
            section_statuses=section_statuses,
        ))

    return results


def missing_assignment_prerequisites(
    student_id: uuid.UUID,
    exp: Experiment,
    db: Session,
) -> list[str]:
    """Return unmet prerequisites in the same order as the student workflow.

    All currently defined manual sections are required. Pre/post quizzes and the
    Code Exercise are prerequisites when the corresponding activity is defined.
    This function is shared by experiment details, quiz access and submission.
    """
    completed_static = get_completed_section_keys(student_id, exp.id, db)
    quiz_types = {q.quiz_type.value: q for q in exp.quizzes}
    pre_q = quiz_types.get(QuizType.pre.value)
    post_q = quiz_types.get(QuizType.post.value)

    pre_submitted = bool(pre_q) and db.query(StudentQuizProgress.id).filter(
        StudentQuizProgress.student_id == student_id,
        StudentQuizProgress.quiz_id == pre_q.id,
    ).first() is not None
    post_submitted = bool(post_q) and db.query(StudentQuizProgress.id).filter(
        StudentQuizProgress.student_id == student_id,
        StudentQuizProgress.quiz_id == post_q.id,
    ).first() is not None
    code_matched = False
    if exp.evaluation_spec is not None:
        code_matched = db.query(CodeSubmission.id).filter(
            CodeSubmission.student_id == student_id,
            CodeSubmission.experiment_id == exp.id,
            CodeSubmission.status == SubmissionStatus.matched,
        ).first() is not None

    # The order reflects the existing experiment flow. Change it only together
    # with the approved section ordering in the student workspace.
    ordered_requirements = [
        ("overview", STATIC_SECTION_LABELS["overview"], True),
        ("aim-objectives", STATIC_SECTION_LABELS["aim-objectives"], True),
        ("pre-quiz", "Pre-Quiz", pre_q is not None and not pre_submitted),
        ("video", STATIC_SECTION_LABELS["video"], True),
        ("theory", STATIC_SECTION_LABELS["theory"], True),
        ("guided-lab", STATIC_SECTION_LABELS["guided-lab"], True),
        ("code-exercise", "Code Exercise (output must match the expected result)", exp.evaluation_spec is not None and not code_matched),
        ("post-quiz", "Post-Quiz", post_q is not None and not post_submitted),
    ]

    missing: list[str] = []
    for key, label, required in ordered_requirements:
        if not required:
            continue
        if key in STATIC_SECTION_LABELS:
            if key not in completed_static:
                missing.append(label)
        else:
            # Dynamic activities have already encoded their missing status in
            # the third tuple element above.
            missing.append(label)
    return missing


def score_is_revealed(quiz: Quiz) -> bool:
    """Apply the configured score-release policy for non-student-facing views."""
    if quiz.reveal_policy == RevealPolicy.immediate:
        return True
    if quiz.reveal_policy == RevealPolicy.after_deadline:
        return quiz.deadline is None or datetime.now(timezone.utc) >= quiz.deadline
    return False


def student_quiz_status(
    student_id: uuid.UUID, quiz: Quiz, db: Session
) -> tuple[bool, float | None]:
    """Return submitted status and the student-visible saved score.

    Pre/post quizzes use one best-score row and never store individual attempts.
    Assignments continue using their single accepted QuizSubmission record, and
    student assignment scores are visible immediately after submission.
    """
    if quiz.quiz_type in (QuizType.pre, QuizType.post):
        result = db.query(StudentQuizProgress).filter(
            StudentQuizProgress.student_id == student_id,
            StudentQuizProgress.quiz_id == quiz.id,
        ).first()
        return (result is not None, result.best_score if result is not None else None)

    submission = db.query(QuizSubmission).filter(
        QuizSubmission.student_id == student_id,
        QuizSubmission.quiz_id == quiz.id,
    ).first()
    return (submission is not None, submission.score if submission is not None else None)
