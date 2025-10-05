from pydantic import BaseModel
from typing import Optional
import datetime
import uuid
from app.models.attachment import MediaType


class AttachmentRead(BaseModel):
    id: uuid.UUID
    url: Optional[str] = None
    media_type: Optional[MediaType] = None
    metadata_: Optional[dict] = None
    audio_url: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
