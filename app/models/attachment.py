import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base
import enum


class MediaType(str, enum.Enum):
    image = "image"
    audio = "audio"


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
    )

    url = Column(String, nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    metadata_ = Column(JSONB, nullable=True)

    # To store generated assistant audio responses
    audio_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSession", back_populates="attachments")
    message = relationship("Message", back_populates="attachments")
