import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    email: EmailStr
    roll_number: Optional[str] = None
    role: UserRole
    is_active: bool
    must_change_password: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool  # frontend redirects straight to the change-password screen if true


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str  # frontend enforces min length; backend also checks (see router)
