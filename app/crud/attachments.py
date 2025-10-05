from sqlalchemy.ext.asyncio import AsyncSession
from app.models.attachment import Attachment, MediaType

async def create_attachment(db: AsyncSession, session_id, message_id, url: str, media_type: MediaType, metadata: dict = None) -> Attachment:
    attach = Attachment(session_id=session_id, message_id=message_id, url=url, media_type=media_type, metadata=metadata)
    db.add(attach)
    await db.commit()
    await db.refresh(attach)
    return attach
