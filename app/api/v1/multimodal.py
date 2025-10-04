from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import aiofiles

from app.db.session import get_async_session
from app.api.deps import get_current_user
from app.models.message import RoleEnum
from app.models.attachment import MediaType
from app.crud.session import get_chat_session, create_chat_session
from app.crud.message import create_message
from app.crud.attachments import create_attachment
from app.services.storage import upload_file_to_s3
from app.services.llm_client import generate_response

router = APIRouter(prefix="/multimodal", tags=["multimodal"])


@router.post("/images")
async def upload_image(
    file: UploadFile = File(...),
    session_id: uuid.UUID | None = Form(None),
    prompt: str | None = Form(None),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # If no session provided, create one
    if not session_id:
        session = await create_chat_session(db, current_user.id, title="Image Session")
    else:
        session = await get_chat_session(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Invalid session")

    # Read file
    file_bytes = await file.read()

    # Upload to S3
    file_url = upload_file_to_s3(file_bytes, file.filename, file.content_type)

    # Save user message with image metadata
    user_msg = await create_message(
        db, session.id, RoleEnum.user, prompt or "Uploaded an image"
    )
    await create_attachment(
        db,
        session.id,
        user_msg.id,
        file_url,
        MediaType.image,
        {"filename": file.filename},
    )

    # For now: just describe the image
    history = [
        {
            "role": "user",
            "content": f"User uploaded an image: {file.filename}. Prompt: {prompt}",
        }
    ]

    assistant_content = await generate_response(history)

    assistant_msg = await create_message(
        db, session.id, RoleEnum.assistant, assistant_content
    )

    return {
        "assistant_message": assistant_msg.content,
        "image_url": file_url,
        "session_id": str(session.id),
        "message_id": str(assistant_msg.id),
    }
