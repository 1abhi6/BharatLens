from pydantic import BaseModel
from datetime import datetime
import uuid
from typing import Optional, List

from app.models import RoleEnum
from app.schemas.attachment import AttachmentRead


class MessageCreate(BaseModel):
    content: str


class MessageRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: RoleEnum
    content: str
    created_at: datetime
    attachments: Optional[List[AttachmentRead]] = []

    class Config:
        from_attributes = True
