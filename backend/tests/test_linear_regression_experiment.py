"""The Linear Regression experiment loader (experiment number 8) and its Code Exercise answer."""
from pathlib import Path

import pytest

from app.models import Experiment, ExperimentEvaluationSpec, Quiz, QuizType, RevealPolicy, SubmissionStatus, UserRole
from helpers import add_code_submission, make_experiment, make_user
from scripts import linear_regression_content as c
from scripts.load_linear_regression import load


DATASET_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public" / "datasets"


def _demo(db, number):
    exp = make_experiment(db)
    db.get(Experiment, exp.id).order_index = number
    db.commit()
    return exp


def test_loader_replaces_only_experiment_8(db):
    demo3, demo8 = _demo(db, 3), _demo(db, 8)
    student = make_user(db, UserRole.student)
    add_code_submission(db, student, demo8, SubmissionStatus.matched)  # must not block the replacement
    db.commit()

    loaded = load(db)

    assert db.get(Experiment, demo8.id) is None
    assert db.get(Experiment, demo3.id) is not None  # other experiments untouched
    assert (loaded.order_index, loaded.slug, loaded.title) == (8, c.SLUG, "Linear Regression")
    assert db.query(Experiment).filter_by(order_index=8).count() == 1


def test_loader_is_safe_to_rerun(db):
    load(db)
    load(db)
    assert db.query(Experiment).filter_by(slug=c.SLUG).count() == 1
    assert db.query(Experiment).filter_by(order_index=8).count() == 1


def test_loaded_content_and_quizzes(db):
    exp = load(db)
    assert exp.is_published
    assert exp.video_url.startswith("https://www.youtube.com/")
    assert "## References" in exp.notes
    assert exp.allowed_imports == ["numpy", "pandas", "sklearn"]
    # The editor starts with a minimal snippet: `result` already exists, no data or solution code.
    assert exp.starter_code.startswith("result = None") and "print(" not in exp.starter_code
    assert "LinearRegression" not in exp.starter_code and "read_csv" not in exp.starter_code
    assert exp.code_dataset_url == "/datasets/Salary_dataset.csv"
    assert "random_state=42" in exp.code_problem_statement and "`result`" in exp.code_problem_statement
    assert "Salary_dataset.csv" in exp.code_problem_statement and "Mark Completed" in exp.code_problem_statement

    quizzes = {q.quiz_type: q for q in db.query(Quiz).filter_by(experiment_id=exp.id)}
    assert set(quizzes) == {QuizType.pre, QuizType.post, QuizType.assignment}
    for quiz_type, quiz in quizzes.items():
        assert len(quiz.questions) == 10
        for question in quiz.questions:
            assert sum(o.is_correct for o in question.options) == 1  # exactly one correct option
        assert quiz.deadline is None and quiz.reveal_policy == RevealPolicy.immediate
        assert quiz.is_scored == (quiz_type == QuizType.assignment)


@pytest.mark.skipif(not DATASET_DIR.exists(), reason="frontend dataset folder not available")
def test_dataset_file_is_in_the_frontend_public_folder():
    lines = (DATASET_DIR / "Salary_dataset.csv").read_text().splitlines()
    assert lines[0] == "YearsExperience,Salary"
    assert len(lines) == 31  # header + 30 records


@pytest.mark.skipif(not DATASET_DIR.exists(), reason="frontend dataset folder not available")
def test_expected_result_is_what_the_demo_solution_produces(monkeypatch):
    pytest.importorskip("sklearn")
    pytest.importorskip("pandas")
    monkeypatch.chdir(DATASET_DIR)  # the solution reads Salary_dataset.csv from the working directory
    namespace = {}
    exec(c.SOLUTION_CODE, namespace)
    assert namespace["result"] == c.EXPECTED_RESULT


def test_student_submission_is_checked_against_the_saved_result(client, db):
    exp = load(db)
    student = make_user(db, UserRole.student)
    assert db.query(ExperimentEvaluationSpec).filter_by(experiment_id=exp.id).one().expected_output == c.EXPECTED_RESULT

    def submit(output):
        return client.post(
            "/code_submissions",
            json={"experiment_id": str(exp.id), "submitted_code": "result = ...", "client_output": output},
            headers=student.headers,
        ).json()["status"]

    assert submit([round(v + 1, 2) for v in c.EXPECTED_RESULT]) == "mismatched"
    assert submit(list(reversed(c.EXPECTED_RESULT))) == "mismatched"  # order matters
    assert submit(c.EXPECTED_RESULT) == "matched"
