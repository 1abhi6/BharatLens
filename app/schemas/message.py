from pydantic import BaseModel
from datetime import datetime
import uuid

from app.models import RoleEnum


class MessageCreate(BaseModel):
    content: str


class MessageRead(BaseModel):
    id: uuid.UUID
    role: RoleEnum
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
