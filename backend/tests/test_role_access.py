"""Role rules: students-only dashboard and code submissions, and instructors only see their own batches."""
import uuid
from types import SimpleNamespace

from app.core.security import create_access_token, hash_password
from app.models import Batch, InstructorAssignment, User, UserRole


def _make_user(db, role: UserRole) -> SimpleNamespace:
    user = User(
        full_name="Test User",
        email=f"{role.value}-{uuid.uuid4().hex[:8]}@college.edu",
        password_hash=hash_password("Pass12345"),
        role=role,
    )
    db.add(user)
    db.commit()
    user_id = user.id
    token = create_access_token(user_id, role.value)
    return SimpleNamespace(id=user_id, headers={"Authorization": f"Bearer {token}"})


def test_student_dashboard_is_for_students_only(client, db):
    student = _make_user(db, UserRole.student)
    instructor = _make_user(db, UserRole.instructor)
    admin = _make_user(db, UserRole.admin)

    assert client.get("/dashboards/student", headers=student.headers).status_code == 200
    assert client.get("/dashboards/student", headers=instructor.headers).status_code == 403
    assert client.get("/dashboards/student", headers=admin.headers).status_code == 403


def test_instructor_sees_only_assigned_batches(client, db):
    instructor = _make_user(db, UserRole.instructor)
    admin = _make_user(db, UserRole.admin)

    mine = Batch(name=f"A-{uuid.uuid4().hex[:6]}", academic_year="2026-27")
    other = Batch(name=f"B-{uuid.uuid4().hex[:6]}", academic_year="2026-27")
    db.add_all([mine, other])
    db.flush()
    mine_id, other_id = str(mine.id), str(other.id)
    db.add(InstructorAssignment(instructor_id=instructor.id, batch_id=mine.id))
    db.commit()

    instructor_ids = {b["id"] for b in client.get("/batches", headers=instructor.headers).json()}
    assert instructor_ids == {mine_id}

    admin_ids = {b["id"] for b in client.get("/batches", headers=admin.headers).json()}
    assert {mine_id, other_id} <= admin_ids

    assert client.get(f"/batches/{mine_id}", headers=instructor.headers).status_code == 200
    assert client.get(f"/batches/{other_id}", headers=instructor.headers).status_code == 403
    assert client.get(f"/batches/{other_id}", headers=admin.headers).status_code == 200


def test_only_students_can_submit_code(client, db):
    body = {"experiment_id": str(uuid.uuid4()), "submitted_code": "x = 1", "client_output": 1}

    for role in (UserRole.instructor, UserRole.admin):
        user = _make_user(db, role)
        assert client.post("/code_submissions", json=body, headers=user.headers).status_code == 403

    # A student passes the role check; this made-up experiment simply does not exist.
    student = _make_user(db, UserRole.student)
    assert client.post("/code_submissions", json=body, headers=student.headers).status_code == 404
