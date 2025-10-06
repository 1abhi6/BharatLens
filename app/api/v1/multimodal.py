import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud.attachments import create_attachment
from app.crud.message import create_message
from app.crud.session import create_chat_session, get_chat_session
from app.db.session import get_async_session
from app.models import VoiceStyle
from app.models.attachment import MediaType
from app.models.message import RoleEnum
from app.services import (
    AudioOutput,
    UploadToS3,
    extract_text_from_s3_image,
    generate_response,
    transcribe_file,
)


router = APIRouter(prefix="/multimodal", tags=["Multimodal"])


@router.post("/chat")
async def multimodal_chat(
    file: Optional[UploadFile] = File(None, description="Optional File Upload"),
    session_id: Optional[uuid.UUID] = Form(None),
    prompt: Optional[str] = Form(None, description="User text input or question."),
    audio_output: bool = Form(False, description="Return response as audio if True."),
    voice_style: VoiceStyle = Form(
        VoiceStyle.alloy,
        description="""
        Choose the output voice style:\n
        - alloy: Versatile and neutral-sounding voice.\n
        - echo: Warm and resonant voice.\n
        - fable: Clear and articulate voice.\n
        - onyx: Deep and commanding voice.\n
        - nova: Bright and energetic voice.\n
        - shimmer: Smooth and calming voice.\n
        """,
    ),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    """
    Handles multimodal chat:
    - Accepts optional text (`prompt`) or media file (image/audio)
    - Supports text or audio output response
    - Returns assistant response and optional audio file URL
    """
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

    # Check if both file and prompt are empty
    if not file and not prompt:
        raise HTTPException(status_code=400, detail="Either file or prompt is required")

    # Session handling
    if not session_id:
        session = await create_chat_session(db, current_user.id, title="Media Session")
    else:
        session = await get_chat_session(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Invalid session")

    # Step 1: Determine content
    content_summary = ""
    file_url = None
    media_type = None

    if file:
        if file.content_type not in all_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        file_bytes = await file.read()
        s3_obj = UploadToS3()
        file_url = s3_obj.upload_file_to_s3(
            file_bytes, file.filename, file.content_type
        )

        # Image Processing
        if file.content_type in SUPPORTED_TYPES["image"]:
            media_type = MediaType.image
            ocr_text = extract_text_from_s3_image(file_url)
            content_summary = (
                f"User uploaded an image. Extracted text: {ocr_text}. Prompt: {prompt}"
            )

        # Audio Processing
        elif file.content_type in SUPPORTED_TYPES["audio"]:
            media_type = MediaType.audio
            text_content = transcribe_file(job_name="audio_transcribe", s3_uri=file_url)
            content_summary = (
                f"User uploaded an audio file. Transcription: {text_content}. "
                f"Convert it to English unless explicitly asked otherwise. Prompt: {prompt}"
            )

        # Save attachment
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
    else:
        # Text-only chat
        content_summary = f"User says: {prompt}"

    # Step 2: Generate Assistant Response
    history = [{"role": "user", "content": content_summary}]
    assistant_content = await generate_response(history)

    assistant_msg = await create_message(
        db, session.id, RoleEnum.assistant, assistant_content
    )

    response_payload = {
        "assistant_message": assistant_msg.content,
        "session_id": str(session.id),
        "message_id": str(assistant_msg.id),
    }

    # Step 3: Audio Output
    if audio_output:
        # Convert text to audio and upload to S3
        audio_output_service = AudioOutput()
        audio_s3_url = await audio_output_service.convert_text_into_audio(
            assistant_content=assistant_content,
            voice_style=voice_style.value,
        )

        response_payload["audio_output_url"] = audio_s3_url

        # Save assistant audio as an attachment in DB
        await create_attachment(
            db=db,
            session_id=session.id,
            message_id=assistant_msg.id,
            url=file_url,
            media_type=media_type,
            metadata_={"voice_style": voice_style.value},
            audio_url=audio_s3_url,
        )

    # Add media file link if uploaded
    if file_url:
        response_payload["uploaded_file_url"] = file_url

    return response_payload
