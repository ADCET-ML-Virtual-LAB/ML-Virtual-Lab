"""
Progress derivation service — computes ExperimentProgress from existing DB rows.

Called by both the student dashboard (own progress) and the instructor dashboard
(progress for all students in a batch).  Progress is never stored in a separate
table — it's derived on read from QuizSubmission and CodeSubmission rows.
"""
import uuid
from typing import Sequence

from sqlalchemy.orm import Session

from app.models.code_submission import CodeSubmission, SubmissionStatus
from app.models.experiment import Experiment
from app.models.quiz import Quiz, QuizSubmission, QuizType, RevealPolicy
from app.schemas.dashboard import ExperimentProgress
from datetime import datetime, timezone


_NS = "not_started"
_IP = "in_progress"
_CO = "completed"
_NT = "not_tracked"


def derive_experiment_progress(
    student_id: uuid.UUID,
    experiments: Sequence[Experiment],
    db: Session,
) -> list[ExperimentProgress]:
    """
    For one student, return an ExperimentProgress entry per published experiment.
    """
    results = []

    for exp in experiments:
        if not exp.is_published:
            continue

        quizzes_by_type: dict[str, Quiz] = {q.quiz_type.value: q for q in exp.quizzes}

        # ── Pre-quiz ──────────────────────────────────────────────────────────
        pre_quiz_status = _NS
        pre_q = quizzes_by_type.get("pre")
        if pre_q:
            has_sub = db.query(QuizSubmission).filter(
                QuizSubmission.student_id == student_id,
                QuizSubmission.quiz_id == pre_q.id,
            ).first()
            pre_quiz_status = _CO if has_sub else _NS

        # ── Guided lab ───────────────────────────────────────────────────────
        guided_lab_status = _NT  # no ping endpoint yet (see CLAUDE.md)

        # ── Code exercise ─────────────────────────────────────────────────────
        code_status = _NS
        code_sub = db.query(CodeSubmission).filter(
            CodeSubmission.student_id == student_id,
            CodeSubmission.experiment_id == exp.id,
        ).order_by(CodeSubmission.submitted_at.desc()).first()
        if code_sub:
            code_status = _CO if code_sub.status == SubmissionStatus.matched else _IP

        # ── Post-quiz ─────────────────────────────────────────────────────────
        post_quiz_status = _NS
        post_q = quizzes_by_type.get("post")
        if post_q:
            has_sub = db.query(QuizSubmission).filter(
                QuizSubmission.student_id == student_id,
                QuizSubmission.quiz_id == post_q.id,
            ).first()
            post_quiz_status = _CO if has_sub else _NS

        # ── Assignment ────────────────────────────────────────────────────────
        assignment_status = _NS
        assignment_score: float | None = None
        asgn_q = quizzes_by_type.get("assignment")
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
                # Reveal score based on policy
                if asgn_q.reveal_policy == RevealPolicy.immediate:
                    assignment_score = latest_sub.score
                elif asgn_q.reveal_policy == RevealPolicy.after_deadline:
                    if asgn_q.deadline is None or datetime.now(timezone.utc) >= asgn_q.deadline:
                        assignment_score = latest_sub.score

        # ── Overall status ────────────────────────────────────────────────────
        trackable = [pre_quiz_status, code_status, post_quiz_status, assignment_status]
        overall = _CO if all(s == _CO for s in trackable) else (
            _IP if any(s != _NS for s in trackable) else _NS
        )

        results.append(ExperimentProgress(
            experiment_id=exp.id,
            experiment_title=exp.title,
            pre_quiz=pre_quiz_status,
            guided_lab=guided_lab_status,
            code_exercise=code_status,
            post_quiz=post_quiz_status,
            assignment=assignment_status,
            assignment_score=assignment_score,
            overall_status=overall,
        ))

    return results
