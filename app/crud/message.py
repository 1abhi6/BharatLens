from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from typing import List
from app.models import Message, RoleEnum


async def create_message(
    db: AsyncSession, session_id, role: RoleEnum, content: str, metadata: dict = None
) -> Message:
    msg = Message(session_id=session_id, role=role, content=content, metadata_=metadata)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg

async def get_messages_by_session(db: AsyncSession, session_id: uuid.UUID) -> List[Message]:
    q = await db.execute(select(Message).where(Message.session_id == session_id).order_by(Message.created_at))
    return q.scalars().all()