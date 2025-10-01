from pydantic import BaseModel
from datetime import datetime
import uuid
from typing import Optional


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionRead(BaseModel):
    id: uuid.UUID
    user_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
