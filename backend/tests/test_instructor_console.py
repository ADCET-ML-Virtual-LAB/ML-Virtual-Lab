"""Instructor console API: instructors only, batch-scoped, no pre/post scores, one instructor per batch."""
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Batch, Enrollment, Experiment, InstructorAssignment, User, UserRole
from helpers import make_experiment, make_user, submit_quiz, unlock_assignment


def _batch(db, instructor=None, name=None):
    batch = Batch(name=name or f"B-{uuid.uuid4().hex[:6]}", academic_year="2026-27")
    db.add(batch)
    db.flush()
    if instructor is not None:
        db.add(InstructorAssignment(instructor_id=instructor.id, batch_id=batch.id))
    db.commit()
    return batch.id


def _enrol(db, batch_id, name="Asha Patil", urn="CS001"):
    student = make_user(db, UserRole.student)
    user = db.get(User, student.id)
    user.full_name, user.roll_number = name, urn
    db.add(Enrollment(student_id=student.id, batch_id=batch_id))
    db.commit()
    return student


def _number(db, exp, number=3):
    db.get(Experiment, exp.id).order_index = number
    db.commit()


def _submitted_assignment(client, db, student, exp, correct):
    unlock_assignment(client, db, student, exp)
    assert submit_quiz(client, student, exp, "assignment", correct=correct).status_code == 201


def _url(batch_id, exp, tail):
    return f"/instructor/batches/{batch_id}/experiments/{exp.id}/{tail}"


# ── Access ────────────────────────────────────────────────────────────────────

def test_instructor_endpoints_are_for_instructors_only(client, db):
    instructor = make_user(db, UserRole.instructor)
    admin = make_user(db, UserRole.admin)
    student = make_user(db, UserRole.student)
    batch_id = _batch(db, instructor)
    exp = make_experiment(db)
    paths = [
        "/instructor/batches",
        f"/instructor/batches/{batch_id}",
        "/instructor/experiments",
        f"/instructor/experiments/{exp.id}",
        f"/instructor/experiments/{exp.id}/assignment",
        _url(batch_id, exp, "status"),
        _url(batch_id, exp, "status/export"),
        _url(batch_id, exp, "assignment-status"),
        _url(batch_id, exp, "assignment-status/export"),
    ]
    for path in paths:
        assert client.get(path, headers=instructor.headers).status_code == 200, path
        assert client.get(path, headers=admin.headers).status_code == 403, path
        assert client.get(path, headers=student.headers).status_code == 403, path
        assert client.get(path).status_code == 401, path


def test_old_instructor_dashboard_endpoints_are_closed_to_admin(client, db):
    admin = make_user(db, UserRole.admin)
    batch_id = _batch(db, make_user(db, UserRole.instructor))
    assert client.get(f"/dashboards/instructor?batch_id={batch_id}", headers=admin.headers).status_code == 403
    assert client.get(f"/dashboards/instructor/export?batch_id={batch_id}", headers=admin.headers).status_code == 403


def test_instructor_only_reaches_own_batch(client, db):
    me = make_user(db, UserRole.instructor)
    other = make_user(db, UserRole.instructor)
    mine, theirs = _batch(db, me), _batch(db, other)
    exp = make_experiment(db)

    ids = {b["id"] for b in client.get("/instructor/batches", headers=me.headers).json()}
    assert ids == {str(mine)}
    assert client.get(f"/instructor/batches/{theirs}", headers=me.headers).status_code == 403
    assert client.get(_url(theirs, exp, "status"), headers=me.headers).status_code == 403
    assert client.get(_url(theirs, exp, "assignment-status"), headers=me.headers).status_code == 403
    assert client.get(_url(theirs, exp, "status/export"), headers=me.headers).status_code == 403
    assert client.get(f"/instructor/batches/{uuid.uuid4()}", headers=me.headers).status_code == 404


# ── Batches ───────────────────────────────────────────────────────────────────

def test_batch_list_is_empty_for_instructor_without_batches(client, db):
    me = make_user(db, UserRole.instructor)
    assert client.get("/instructor/batches", headers=me.headers).json() == []


def test_batch_detail_lists_students_with_urn_and_name_only(client, db):
    me = make_user(db, UserRole.instructor)
    db.get(User, me.id).full_name = "Prof. Rao"
    batch_id = _batch(db, me)
    _enrol(db, batch_id, "Asha Patil", "CS001")
    other_batch = _batch(db, make_user(db, UserRole.instructor))
    _enrol(db, other_batch, "Someone Else", "CS999")

    body = client.get(f"/instructor/batches/{batch_id}", headers=me.headers).json()
    assert body["instructor_name"] == "Prof. Rao"
    assert [(s["urn"], s["full_name"]) for s in body["students"]] == [("CS001", "Asha Patil")]
    assert set(body["students"][0]) == {"id", "urn", "full_name"}  # no email, no extra data
    assert "student_count" not in body


# ── Experiment content ────────────────────────────────────────────────────────

def test_only_published_experiments_are_listed_and_openable(client, db):
    me = make_user(db, UserRole.instructor)
    live, hidden = make_experiment(db), make_experiment(db)
    _number(db, live, 2)
    db.get(Experiment, hidden.id).is_published = False
    db.commit()

    items = client.get("/instructor/experiments", headers=me.headers).json()
    assert [i["id"] for i in items] == [str(live.id)]
    assert items[0]["number"] == 2
    assert client.get(f"/instructor/experiments/{hidden.id}", headers=me.headers).status_code == 404
    assert client.get(f"/instructor/experiments/{hidden.id}/assignment", headers=me.headers).status_code == 404


def test_experiment_content_has_answer_keys_and_no_guided_lab_or_code(client, db):
    me = make_user(db, UserRole.instructor)
    exp = make_experiment(db)
    body = client.get(f"/instructor/experiments/{exp.id}", headers=me.headers).json()

    for key in ("pre_quiz", "post_quiz", "assignment"):
        options = body[key]["questions"][0]["options"]
        assert sorted(o["is_correct"] for o in options) == [False, True]
    for forbidden in ("lab_config", "starter_code", "allowed_imports", "expected_output"):
        assert forbidden not in body
    assert {"overview", "aim", "objective", "notes", "video_url"} <= set(body)


def test_assignment_content_page(client, db):
    me = make_user(db, UserRole.instructor)
    exp = make_experiment(db)
    _number(db, exp, 4)
    body = client.get(f"/instructor/experiments/{exp.id}/assignment", headers=me.headers).json()
    assert body["experiment_number"] == 4
    assert body["experiment_title"] == "Linear Regression"
    assert body["assignment"]["quiz_type"] == "assignment"
    assert "aim" not in body and "overview" not in body


# ── Students Status ───────────────────────────────────────────────────────────

def test_students_status_follows_the_student_tick_rule(client, db):
    me = make_user(db, UserRole.instructor)
    batch_id = _batch(db, me)
    exp = make_experiment(db)
    untouched = _enrol(db, batch_id, "Untouched", "CS001")
    partial = _enrol(db, batch_id, "Partial", "CS002")
    finished = _enrol(db, batch_id, "Finished", "CS003")

    assert client.post(
        f"/experiments/{exp.slug}/sections/overview/complete", headers=partial.headers
    ).status_code == 200
    _submitted_assignment(client, db, finished, exp, correct=True)

    rows = client.get(_url(batch_id, exp, "status"), headers=me.headers).json()["rows"]
    status = {r["full_name"]: r["status"] for r in rows}
    assert status == {"Untouched": "not_started", "Partial": "in_progress", "Finished": "completed"}


def test_status_table_never_exposes_quiz_scores(client, db):
    me = make_user(db, UserRole.instructor)
    batch_id = _batch(db, me)
    exp = make_experiment(db)
    student = _enrol(db, batch_id)
    assert submit_quiz(client, student, exp, "pre").status_code == 201

    for tail in ("status", "assignment-status"):
        text = client.get(_url(batch_id, exp, tail), headers=me.headers).text
        assert "best_score" not in text and "pre_quiz" not in text and "post_quiz" not in text


def test_status_csv_covers_only_the_open_experiment(client, db):
    me = make_user(db, UserRole.instructor)
    batch_id = _batch(db, me)
    exp, other_exp = make_experiment(db), make_experiment(db)
    _number(db, exp, 1)
    _number(db, other_exp, 2)
    _enrol(db, batch_id, "Asha Patil", "CS001")

    resp = client.get(_url(batch_id, exp, "status/export"), headers=me.headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    lines = resp.text.strip().splitlines()
    assert lines[0] == "Batch,Academic Year,Experiment No.,Experiment Title,URN,Student Name,Status"
    assert len(lines) == 2
    assert "CS001,Asha Patil,Not Attempted" in lines[1]
    assert ",1,Linear Regression," in lines[1]


# ── Assignment Status and submission ──────────────────────────────────────────

def test_assignment_status_shows_percentage_or_not_submitted(client, db):
    me = make_user(db, UserRole.instructor)
    batch_id = _batch(db, me)
    exp = make_experiment(db)
    done = _enrol(db, batch_id, "Done", "CS001")
    waiting = _enrol(db, batch_id, "Waiting", "CS002")
    _submitted_assignment(client, db, done, exp, correct=True)

    table = client.get(_url(batch_id, exp, "assignment-status"), headers=me.headers).json()
    assert table["has_assignment"] is True
    rows = {r["full_name"]: r for r in table["rows"]}
    assert rows["Done"]["submitted"] is True and rows["Done"]["score"] == 100.0
    assert rows["Waiting"]["submitted"] is False and rows["Waiting"]["score"] is None

    csv_lines = client.get(_url(batch_id, exp, "assignment-status/export"), headers=me.headers).text.splitlines()
    assert csv_lines[0].endswith("Student Name,Marks (%)")
    assert any(line.endswith("Done,100%") for line in csv_lines)
    assert any(line.endswith("Waiting,Not Submitted") for line in csv_lines)


def test_instructor_sees_score_even_with_after_deadline_reveal_policy(client, db):
    from datetime import datetime, timedelta, timezone

    from app.models import Quiz, QuizType, RevealPolicy

    me = make_user(db, UserRole.instructor)
    batch_id = _batch(db, me)
    exp = make_experiment(db)
    student = _enrol(db, batch_id)
    quiz = db.get(Quiz, exp.quizzes["assignment"].quiz_id)
    quiz.reveal_policy = RevealPolicy.after_deadline
    quiz.deadline = datetime.now(timezone.utc) + timedelta(days=7)
    db.commit()
    _submitted_assignment(client, db, student, exp, correct=True)

    row = client.get(_url(batch_id, exp, "assignment-status"), headers=me.headers).json()["rows"][0]
    assert row["score"] == 100.0


def test_experiment_without_assignment_reports_it(client, db):
    from app.models import Quiz, QuizType

    me = make_user(db, UserRole.instructor)
    batch_id = _batch(db, me)
    exp = make_experiment(db)
    db.delete(db.get(Quiz, exp.quizzes["assignment"].quiz_id))
    db.commit()

    table = client.get(_url(batch_id, exp, "assignment-status"), headers=me.headers).json()
    assert table["has_assignment"] is False and table["rows"] == []
    assert client.get(_url(batch_id, exp, "assignment-status/export"), headers=me.headers).status_code == 404


@pytest.mark.parametrize("correct", [True, False])
def test_view_submission_shows_answer_key_student_answer_and_correctness(client, db, correct):
    me = make_user(db, UserRole.instructor)
    batch_id = _batch(db, me)
    exp = make_experiment(db)
    _number(db, exp, 5)
    student = _enrol(db, batch_id, "Asha Patil", "CS001")
    _submitted_assignment(client, db, student, exp, correct=correct)

    body = client.get(
        _url(batch_id, exp, f"assignment-status/{student.id}"), headers=me.headers
    ).json()
    q = exp.quizzes["assignment"]
    assert body["experiment_number"] == 5 and body["experiment_title"] == "Linear Regression"
    assert body["student"]["urn"] == "CS001"
    assert body["score"] == (100.0 if correct else 0.0)
    review = body["questions"][0]
    assert review["is_correct"] is correct
    assert review["selected_option_id"] == str(q.right_id if correct else q.wrong_id)
    assert {o["id"] for o in review["options"] if o["is_correct"]} == {str(q.right_id)}


def test_view_submission_rejects_unsubmitted_and_foreign_students(client, db):
    me = make_user(db, UserRole.instructor)
    batch_id = _batch(db, me)
    exp = make_experiment(db)
    waiting = _enrol(db, batch_id)
    outsider = _enrol(db, _batch(db, make_user(db, UserRole.instructor)), "Outsider", "CS777")
    _submitted_assignment(client, db, outsider, exp, correct=True)

    assert client.get(_url(batch_id, exp, f"assignment-status/{waiting.id}"), headers=me.headers).status_code == 404
    assert client.get(_url(batch_id, exp, f"assignment-status/{outsider.id}"), headers=me.headers).status_code == 404


def test_student_assignment_apis_still_hide_answers_before_submission(client, db):
    exp = make_experiment(db)
    student = make_user(db, UserRole.student)
    unlock_assignment(client, db, student, exp)
    body = client.get(f"/experiments/{exp.slug}", headers=student.headers).json()
    assignment = next(q for q in body["quizzes"] if q["quiz_type"] == "assignment")
    assert "is_correct" not in str(assignment["questions"])
    assert client.get("/instructor/batches", headers=student.headers).status_code == 403


# ── One instructor per batch ──────────────────────────────────────────────────

def test_admin_cannot_give_a_batch_a_second_instructor(client, db):
    admin = make_user(db, UserRole.admin)
    first, second = make_user(db, UserRole.instructor), make_user(db, UserRole.instructor)
    batch_id = _batch(db)

    url = f"/batches/{batch_id}/instructors"
    assert client.post(url, json={"instructor_id": str(first.id)}, headers=admin.headers).status_code == 201
    assert client.post(url, json={"instructor_id": str(first.id)}, headers=admin.headers).status_code == 201  # idempotent
    resp = client.post(url, json={"instructor_id": str(second.id)}, headers=admin.headers)
    assert resp.status_code == 409
    assert db.query(InstructorAssignment).filter_by(batch_id=batch_id).count() == 1


def test_one_instructor_can_still_have_several_batches(client, db):
    admin = make_user(db, UserRole.admin)
    instructor = make_user(db, UserRole.instructor)
    for _ in range(2):
        batch_id = _batch(db)
        resp = client.post(
            f"/batches/{batch_id}/instructors", json={"instructor_id": str(instructor.id)}, headers=admin.headers
        )
        assert resp.status_code == 201
    assert len(client.get("/instructor/batches", headers=instructor.headers).json()) == 2


def test_database_itself_rejects_two_instructors_on_one_batch(db):
    batch_id = _batch(db, make_user(db, UserRole.instructor))
    db.add(InstructorAssignment(instructor_id=make_user(db, UserRole.instructor).id, batch_id=batch_id))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
