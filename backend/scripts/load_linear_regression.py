"""Load the Linear Regression experiment as experiment number 8.

Run from the backend directory with the project's virtualenv active:
    python -m scripts.load_linear_regression

What it does:
  * removes the demo experiment currently numbered 8 (with its quizzes, completions,
    code submissions and expected result) and any earlier copy of this experiment
  * creates the Linear Regression experiment as number 8 with its content, a
    Pre-Quiz, Post-Quiz and Assignment (no deadline, score shown immediately),
    the Code Exercise (problem statement, starter code, dataset file, allowed libraries)
    and the hidden expected result
Other experiments are not touched. Safe to re-run.
"""
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.code_submission import CodeSubmission
from app.models.experiment import Experiment, ExperimentEvaluationSpec
from app.models.quiz import Option, Question, Quiz, QuizType, RevealPolicy
from scripts import linear_regression_content as c


def _remove_existing(db: Session) -> None:
    targets = (
        db.query(Experiment)
        .filter((Experiment.order_index == c.ORDER_INDEX) | (Experiment.slug == c.SLUG))
        .all()
    )
    for exp in targets:
        print(f"Replacing experiment {exp.order_index}: {exp.title} ({exp.slug})")
        # Code submissions are not cascaded by the ORM relationship, so remove them first.
        db.query(CodeSubmission).filter(CodeSubmission.experiment_id == exp.id).delete(synchronize_session=False)
        db.flush()
        db.delete(exp)
    db.flush()


def _add_quiz(db: Session, exp: Experiment, quiz_type: QuizType, title: str, questions: list) -> None:
    quiz = Quiz(
        experiment_id=exp.id,
        quiz_type=quiz_type,
        is_scored=quiz_type == QuizType.assignment,
        title=title,
        deadline=None,
        reveal_policy=RevealPolicy.immediate,
    )
    db.add(quiz)
    db.flush()
    for q_index, (text, options, correct) in enumerate(questions, start=1):
        question = Question(quiz_id=quiz.id, question_text=text, order_index=q_index)
        db.add(question)
        db.flush()
        for o_index, option_text in enumerate(options, start=1):
            db.add(Option(
                question_id=question.id,
                option_text=option_text,
                is_correct=(o_index - 1 == correct),
                order_index=o_index,
            ))
    db.flush()


def load(db: Session) -> Experiment:
    _remove_existing(db)

    exp = Experiment(
        title=c.TITLE,
        slug=c.SLUG,
        order_index=c.ORDER_INDEX,
        overview=c.OVERVIEW,
        aim=c.AIM,
        objective=c.OBJECTIVE,
        notes=c.NOTES,
        video_url=c.VIDEO_URL,
        starter_code=c.STARTER_CODE,
        allowed_imports=c.ALLOWED_IMPORTS,
        code_dataset_url=c.DATASET_URL,
        code_problem_statement=c.CODE_PROBLEM_STATEMENT,
        is_published=True,
    )
    db.add(exp)
    db.flush()

    _add_quiz(db, exp, QuizType.pre, "Pre-Quiz", c.PRE_QUIZ)
    _add_quiz(db, exp, QuizType.post, "Post-Quiz", c.POST_QUIZ)
    _add_quiz(db, exp, QuizType.assignment, "Assignment", c.ASSIGNMENT)

    db.add(ExperimentEvaluationSpec(
        experiment_id=exp.id,
        expected_output=c.EXPECTED_RESULT,
        comparison_tolerance=None,  # exact match for now
    ))
    db.commit()
    return exp


def main() -> None:
    db = SessionLocal()
    try:
        exp = load(db)
        print(f"Loaded experiment {exp.order_index}: {exp.title} ({exp.slug})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
