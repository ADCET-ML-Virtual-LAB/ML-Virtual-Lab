"""
Progress derivation service — computes ExperimentProgress from existing DB rows.

Called by both the student dashboard (own progress) and the instructor dashboard
(progress for all students in a batch).  Progress is never stored in a separate
table — it's derived on read from QuizSubmission and CodeSubmission rows.
"""
import uuid
from typing import Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.code_submission import CodeSubmission, SubmissionStatus
from app.models.experiment import Experiment
from app.models.quiz import Quiz, QuizSubmission, QuizType, RevealPolicy
from app.schemas.dashboard import ExperimentProgress
from datetime import datetime, timezone


_NS = "not_started"
_IP = "in_progress"
_CO = "completed"


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
                if score_is_revealed(asgn_q):
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
            code_exercise=code_status,
            post_quiz=post_quiz_status,
            assignment=assignment_status,
            assignment_score=assignment_score,
            overall_status=overall,
        ))

    return results


def missing_assignment_prerequisites(
    student_id: uuid.UUID,
    exp: Experiment,
    db: Session,
) -> list[str]:
    """
    Steps a student must still finish before the graded assignment unlocks.
    An empty list means the assignment is open.

    Strict rule (may be relaxed later): Pre-Quiz and Post-Quiz must be submitted,
    and the Code Exercise result must MATCH the stored expected result.
    "Completed" means exactly what it means in derive_experiment_progress, so the
    lock and the progress screens can never disagree.

    A step the experiment does not have cannot be required:
      - no pre/post quiz defined      -> that quiz is skipped
      - no evaluation spec defined    -> nothing can ever match, so the code step is skipped
    The guided lab is practice only and is never required.
    """
    progress = derive_experiment_progress(student_id, [exp], db)
    # derive_experiment_progress skips unpublished experiments -> nothing is completed.
    p = progress[0] if progress else None
    quiz_types = {q.quiz_type.value for q in exp.quizzes}

    missing: list[str] = []
    if "pre" in quiz_types and (p is None or p.pre_quiz != _CO):
        missing.append("Pre-Quiz")
    if exp.evaluation_spec is not None and (p is None or p.code_exercise != _CO):
        missing.append("Code Exercise")
    if "post" in quiz_types and (p is None or p.post_quiz != _CO):
        missing.append("Post-Quiz")
    return missing


def score_is_revealed(quiz: Quiz) -> bool:
    """May the student see this quiz's score yet? The quiz's reveal_policy decides."""
    if quiz.reveal_policy == RevealPolicy.immediate:
        return True
    if quiz.reveal_policy == RevealPolicy.after_deadline:
        return quiz.deadline is None or datetime.now(timezone.utc) >= quiz.deadline
    return False


def quiz_attempt_summary(student_id: uuid.UUID, quiz: Quiz, db: Session) -> tuple[int, float | None]:
    """
    (attempts so far, best score the student is allowed to see).

    Pre/post quizzes are self-assessment, so their best score is always visible to the student.
    The graded assignment follows its reveal policy. These numbers go to the student only,
    never to instructors (the instructor dashboard and CSV carry the assignment score alone).
    """
    attempts, best = (
        db.query(func.count(QuizSubmission.id), func.max(QuizSubmission.score))
        .filter(QuizSubmission.student_id == student_id, QuizSubmission.quiz_id == quiz.id)
        .one()
    )
    if quiz.quiz_type == QuizType.assignment and not score_is_revealed(quiz):
        best = None
    return attempts, best
