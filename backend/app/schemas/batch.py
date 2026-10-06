import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class BatchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    academic_year: str = Field(min_length=1, max_length=20)

    @field_validator("name", "academic_year")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    academic_year: str
    created_at: datetime


class StudentRow(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=150)
    roll_number: Optional[str] = None


class StudentUploadRequest(BaseModel):
    students: list[StudentRow] = Field(min_length=1)


class StudentUploadRowResult(BaseModel):
    email: str
    status: str  # "created" | "already_exists" | "already_in_batch"


class StudentUploadResponse(BaseModel):
    created: int
    skipped: int
    rows: list[StudentUploadRowResult]
