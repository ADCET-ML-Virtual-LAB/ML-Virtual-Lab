import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.batch import Batch, Enrollment, InstructorAssignment
from app.core.security import hash_password

ADMIN_EMAIL = "admin@college.edu"
ADMIN_PASS = "AdminPass123!"

INSTRUCTOR_BASE_EMAIL = "instructor{}@college.edu"
INSTRUCTOR_PASS = "InstPass123!"

STUDENT_BASE_EMAIL = "student{}@college.edu"
STUDENT_PASS = "StudPass123!"

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Admin
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                full_name="System Administrator",
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASS),
                role=UserRole.admin,
                is_active=True,
                must_change_password=False
            )
            db.add(admin)
            print(f"Created Admin: {ADMIN_EMAIL}")

        # 2. Instructors
        instructors = []
        for i in range(1, 6):
            email = INSTRUCTOR_BASE_EMAIL.format(i)
            instructor = db.query(User).filter(User.email == email).first()
            if not instructor:
                instructor = User(
                    full_name=f"Instructor {i}",
                    email=email,
                    password_hash=hash_password(INSTRUCTOR_PASS),
                    role=UserRole.instructor,
                    is_active=True,
                    must_change_password=False
                )
                db.add(instructor)
                print(f"Created Instructor: {email}")
            instructors.append(instructor)
        
        db.flush()

        # 3. Batches
        batches_data = [
            {"name": "TE-CSE-A", "academic_year": "2026-27"},
            {"name": "TE-CSE-B", "academic_year": "2026-27"},
            {"name": "BE-IT-A", "academic_year": "2026-27"}
        ]
        batches = []
        for bdata in batches_data:
            batch = db.query(Batch).filter(
                Batch.name == bdata["name"],
                Batch.academic_year == bdata["academic_year"]
            ).first()
            if not batch:
                batch = Batch(name=bdata["name"], academic_year=bdata["academic_year"])
                db.add(batch)
                print(f"Created Batch: {bdata['name']}")
            batches.append(batch)
            
        db.flush()

        # 4. Assign Instructors to Batches
        for i, batch in enumerate(batches):
            instructor = instructors[i % len(instructors)]
            assignment = db.query(InstructorAssignment).filter(
                InstructorAssignment.instructor_id == instructor.id,
                InstructorAssignment.batch_id == batch.id
            ).first()
            if not assignment:
                assignment = InstructorAssignment(instructor_id=instructor.id, batch_id=batch.id)
                db.add(assignment)
                print(f"Assigned {instructor.email} to {batch.name}")

        # 5. Students
        students = []
        for i in range(1, 16):
            email = STUDENT_BASE_EMAIL.format(i)
            roll_number = f"CS{i:03d}"
            student = db.query(User).filter(User.email == email).first()
            if not student:
                student = User(
                    full_name=f"Student {i}",
                    email=email,
                    roll_number=roll_number,
                    password_hash=hash_password(STUDENT_PASS),
                    role=UserRole.student,
                    is_active=True,
                    must_change_password=False
                )
                db.add(student)
                print(f"Created Student: {email} (Roll: {roll_number})")
            students.append(student)

        db.flush()

        # 6. Enroll students
        for i, student in enumerate(students):
            batch = batches[i % len(batches)]
            enrollment = db.query(Enrollment).filter(
                Enrollment.student_id == student.id,
                Enrollment.batch_id == batch.id
            ).first()
            if not enrollment:
                enrollment = Enrollment(student_id=student.id, batch_id=batch.id)
                db.add(enrollment)
                print(f"Enrolled {student.email} in {batch.name}")

        db.commit()
        print("Data seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
