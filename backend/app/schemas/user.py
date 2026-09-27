import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.user import UserRole


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    roll_number: Optional[str] = None
    role: UserRole


class StudentRegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    roll_number: str  # checked against RosterEntry before account creation
    password: str


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
