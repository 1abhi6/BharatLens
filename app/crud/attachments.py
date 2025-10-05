from app.models.attachment import Attachment
from sqlalchemy.ext.asyncio import AsyncSession


async def create_attachment(
    db: AsyncSession,
    session_id,
    message_id,
    url,
    media_type,
    metadata_=None,
    audio_url=None,
):
    attachment = Attachment(
        session_id=session_id,
        message_id=message_id,
        url=url,
        media_type=media_type,
        metadata_=metadata_,
        audio_url=audio_url,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment
