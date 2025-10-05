import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud.attachments import create_attachment
from app.crud.message import create_message
from app.crud.session import create_chat_session, get_chat_session
from app.db.session import get_async_session
from app.models.attachment import MediaType
from app.models.message import RoleEnum
from app.services import (
    UploadToS3,
    extract_text_from_s3_image,
    generate_response,
    transcribe_file,
)

router = APIRouter(prefix="/multimodal", tags=["Multimodal"])


@router.post("/media")
async def upload_media(
    file: UploadFile = File(...),
    session_id: uuid.UUID | None = Form(None),
    prompt: str | None = Form(None),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    """
    Accepts image and audio
    """
    # Accept images and audio formats
    SUPPORTED_TYPES = {
        "image": ["image/jpeg", "image/png", "image/webp"],
        "audio": [
            "audio/mpeg",
            "audio/wav",
            "audio/mp3",
            "audio/webm",
            "audio/x-wav",
            "audio/ogg",
        ],
    }
    all_types = SUPPORTED_TYPES["image"] + SUPPORTED_TYPES["audio"]

    if file.content_type not in all_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # If no session provided, create one
    if not session_id:
        session = await create_chat_session(db, current_user.id, title="Media Session")
    else:
        session = await get_chat_session(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Invalid session")

    # Read file
    file_bytes = await file.read()

    # Upload to S3
    s3_obj = UploadToS3()
    file_url = s3_obj.upload_file_to_s3(file_bytes, file.filename, file.content_type)

    # Determine type and handle processing
    if file.content_type in SUPPORTED_TYPES["image"]:
        media_type = MediaType.image
        text_content = extract_text_from_s3_image(file_url)  # OCR for images
        content_summary = f"User uploaded an image: The content of image is: \n{text_content}. Prompt:\n {prompt}"

    elif file.content_type in SUPPORTED_TYPES["audio"]:
        media_type = MediaType.audio
        # Transcribe the audio file using AWS Transcribe
        job_name = "audio_transcribe"
        text_content = transcribe_file(job_name=job_name, s3_uri=file_url)

        content_summary = f"User uploaded an audio file: The transcribe of audio is: \n{text_content}. In whatever language the transcribe is convert it into english and then reply only in English, Unless user explicitly asks for the specific language. \nPrompt:\n {prompt}"
    else:
        raise HTTPException(status_code=400, detail="Unsupported media type")

    # Save user message with attachment
    user_msg = await create_message(
        db, session.id, RoleEnum.user, prompt or f"Uploaded a {media_type.value}"
    )
    await create_attachment(
        db,
        session.id,
        user_msg.id,
        file_url,
        media_type,
        {"filename": file.filename},
    )

    history = [
        {
            "role": "user",
            "content": content_summary,
        }
    ]

    assistant_content = await generate_response(history)

    assistant_msg = await create_message(
        db, session.id, RoleEnum.assistant, assistant_content
    )

    return {
        "assistant_message": assistant_msg.content,
        "file_url": file_url,
        "session_id": str(session.id),
        "message_id": str(assistant_msg.id),
    }
