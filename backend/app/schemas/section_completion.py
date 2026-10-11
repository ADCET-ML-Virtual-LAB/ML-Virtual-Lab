"""Schemas for manually tracked section completion."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SectionCompletionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    experiment_id: uuid.UUID
    section_key: str
    created_at: datetime
    completed: bool = True
