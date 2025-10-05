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
from app.core.config import settings
from app.models import VoiceStyle

from app.services import (
    UploadToS3,
    extract_text_from_s3_image,
    generate_response,
    transcribe_file,
)

router = APIRouter(prefix="/multimodal", tags=["Multimodal"])


@router.post("/media")
async def upload_meida(
    file: UploadFile = File(...),
    session_id: uuid.UUID | None = Form(None),
    prompt: str | None = Form(None),
    audio_output: bool = Form(False),
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
    Accepts image or audio, processes it via OCR or Transcription,
    and optionally returns the LLM response as audio.
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

    if file.content_type not in all_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Session handling
    if not session_id:
        session = await create_chat_session(db, current_user.id, title="Media Session")
    else:
        session = await get_chat_session(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Invalid session")

    # Upload to S3
    file_bytes = await file.read()
    s3_obj = UploadToS3()
    file_url = s3_obj.upload_file_to_s3(file_bytes, file.filename, file.content_type)

    # Handle type
    if file.content_type in SUPPORTED_TYPES["image"]:
        media_type = MediaType.image
        text_content = extract_text_from_s3_image(file_url)
        content_summary = f"User uploaded an image. Extracted text: {text_content}. Prompt: {prompt or ''}"

    elif file.content_type in SUPPORTED_TYPES["audio"]:
        media_type = MediaType.audio
        job_name = f"audio_transcribe_{uuid.uuid4().hex[:6]}"
        text_content = transcribe_file(job_name=job_name, s3_uri=file_url)
        content_summary = f"User uploaded audio. Transcription: {text_content}. Prompt: {prompt or ''}"
        
    else:
        raise HTTPException(status_code=400, detail="Unsupported media type")

    # Save user message
    user_msg = await create_message(
        db, session.id, RoleEnum.user, prompt or f"Uploaded {media_type.value}"
    )
    await create_attachment(
        db,
        session.id,
        user_msg.id,
        file_url,
        media_type,
        {"filename": file.filename},
    )

    # Generate assistant response
    history = [{"role": "user", "content": content_summary}]
    assistant_content = await generate_response(history)

    # Save assistant message
    assistant_msg = await create_message(
        db, session.id, RoleEnum.assistant, assistant_content
    )

    response_data = {
        "assistant_message": assistant_msg.content,
        "file_url": file_url,
        "session_id": str(session.id),
        "message_id": str(assistant_msg.id),
    }

    # --- Phase 3: Optional Audio Output ---
    if audio_output:
        from openai import AsyncOpenAI
        import tempfile

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            audio_resp = await client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice_style,
                input=assistant_content,
            )
            audio_resp.stream_to_file(temp_audio.name)

            # Upload generated audio to S3
            with open(temp_audio.name, "rb") as audio_file:
                audio_url = s3_obj.upload_file_to_s3(
                    audio_file.read(), f"{uuid.uuid4()}.mp3", "audio/mpeg"
                )

        # Save assistant audio attachment
        await create_attachment(
            db,
            session.id,
            assistant_msg.id,
            audio_url,
            MediaType.audio,
            {"source": "generated_speech"},
        )

        response_data["assistant_audio_url"] = audio_url

    return response_data
