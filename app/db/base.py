# app/db/base.py

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here so Alembic can detect them
from app.models.user import User
from app.models.chat_session import ChatSession
from app.models.message import Message
from app.models.attachment import Attachment
