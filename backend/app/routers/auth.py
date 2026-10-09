from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas.user import ChangePasswordRequest, LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    # Same error for "no such email" and "wrong password" so a caller can't tell which is wrong.
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token, must_change_password=user.must_change_password)


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password", response_model=UserOut)
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "New password must be at least 8 characters")
    if payload.new_password == payload.current_password:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "New password must differ from the current one")
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    return user


# ── Admin-only: create instructor account ────────────────────────────────────

from pydantic import BaseModel as _PydanticBase, EmailStr as _EmailStr
from app.core.deps import require_roles as _require_roles
from app.models.user import UserRole as _UserRole
from sqlalchemy.exc import IntegrityError as _IntegrityError


class _InstructorCreate(_PydanticBase):
    full_name: str
    email: _EmailStr
    password: str


@router.post("/instructors", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_instructor(
    payload: _InstructorCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_roles(_UserRole.admin)),
):
    """Admin-only: create an instructor account with a known password."""
    instructor = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=_UserRole.instructor,
        must_change_password=False,
    )
    db.add(instructor)
    try:
        db.commit()
    except _IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already in use")
    db.refresh(instructor)
    return instructor


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_roles(_UserRole.admin)),
):
    """Admin-only: list all users (for admin panel)."""
    return db.query(User).order_by(User.full_name).all()
