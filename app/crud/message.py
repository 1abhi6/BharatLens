from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message, RoleEnum


async def create_message(
    db: AsyncSession, session_id, role: RoleEnum, content: str, metadata: dict = None
) -> Message:
    msg = Message(session_id=session_id, role=role, content=content, metadata_=metadata)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
