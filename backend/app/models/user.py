import enum
import uuid
from typing import Optional

from sqlalchemy import String, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import UUIDPKMixin, TimestampMixin


class UserRole(str, enum.Enum):
    student = "student"
    instructor = "instructor"
    admin = "admin"


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # Only students have a roll number; nullable for instructor/admin accounts.
    roll_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # relationships
    enrollments = relationship("Enrollment", back_populates="student", foreign_keys="Enrollment.student_id")
    instructor_assignments = relationship(
        "InstructorAssignment", back_populates="instructor", foreign_keys="InstructorAssignment.instructor_id"
    )
    quiz_submissions = relationship("QuizSubmission", back_populates="student")
    code_submissions = relationship("CodeSubmission", back_populates="student")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base, UUIDPKMixin):
    """Lets us revoke individual sessions instead of trusting JWTs blindly until they expire."""
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
