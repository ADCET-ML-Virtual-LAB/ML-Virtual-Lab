import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TimestampMixin, UUIDPKMixin


class UserRole(str, enum.Enum):
    student = "student"
    instructor = "instructor"
    admin = "admin"


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)  # stored lowercase
    # Only students have a roll number; nullable for instructor/admin accounts.
    roll_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # True while the account still has the emailed default password.
    # Every endpoint except login / me / change-password is blocked until it is False.
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # When the credentials email was successfully sent. NULL = not sent (yet / failed) -> instructor can re-send.
    credentials_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    enrollments = relationship("Enrollment", back_populates="student", foreign_keys="Enrollment.student_id")
    instructor_assignments = relationship(
        "InstructorAssignment", back_populates="instructor", foreign_keys="InstructorAssignment.instructor_id"
    )
    quiz_submissions = relationship("QuizSubmission", back_populates="student")
    code_submissions = relationship("CodeSubmission", back_populates="student")
