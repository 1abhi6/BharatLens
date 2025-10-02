from pydantic import BaseModel
from datetime import datetime
import uuid
from typing import Optional, List
from app.schemas.message import MessageRead # Import MessageRead schema


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


class SessionWithMessages(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead]

    class Config:
        from_attributes = True
