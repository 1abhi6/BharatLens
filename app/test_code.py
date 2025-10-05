import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, create_engine
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
import enum

Base = declarative_base()

class MediaType(str, enum.Enum):
    image = "image"
    audio = "audio"

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attachments = relationship("Attachment", back_populates="session", cascade="all, delete")

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=True)
    url = Column(String, nullable=False)
    media_type = Column(Enum(MediaType), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSession", back_populates="attachments")

# SQLite for testing purpose; replace with your DB URL
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
db = Session()

# Test insert
session_obj = ChatSession()
attachment_obj = Attachment(url="http://example.com/image.jpg", media_type=MediaType.image, session=session_obj)

db.add(session_obj)
db.commit()
