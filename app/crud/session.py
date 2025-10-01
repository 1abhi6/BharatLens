from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from typing import Optional

from app.models import ChatSession


async def create_chat_session(
    db: AsyncSession, user_id: int, title: Optional[str] = None
) -> ChatSession:
    session = ChatSession(user_id=user_id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_chat_session(
    db: AsyncSession, session_id: uuid.UUID
) -> Optional[ChatSession]:
    q = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    return q.scalars().first()
