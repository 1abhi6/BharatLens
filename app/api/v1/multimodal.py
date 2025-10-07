import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud.attachments import create_attachment
from app.crud.message import create_message, get_messages_by_session
from app.crud.session import create_chat_session, get_chat_session
from app.db.session import get_async_session
from app.models import VoiceStyle
from app.models.attachment import MediaType
from app.models.message import RoleEnum
from app.services import (
    AudioOutput,
    UploadToS3,
    extract_text_from_s3_docs,
    analyze_image_vision_fn,
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
    - Accepts optional text (`prompt`) or media file (image/audio/docs[pdf, docx])
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
        "document": [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ],
    }

    all_types = (
        SUPPORTED_TYPES["image"]
        + SUPPORTED_TYPES["audio"]
        + SUPPORTED_TYPES["document"]
    )

    if not file and not prompt:
        raise HTTPException(status_code=400, detail="Either file or prompt is required")

    # Session handling
    if not session_id:
        session = await create_chat_session(db, current_user.id, title="Media Session")
    else:
        session = await get_chat_session(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Invalid session")

    file_url = None
    media_type = None
    attachment_metadata = {}

    # Step 1: Save User Message & Attachment if provided
    if file:
        if file.content_type not in all_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        file_bytes = await file.read()
        s3_obj = UploadToS3()
        file_url = s3_obj.upload_file_to_s3(
            file_bytes, file.filename, file.content_type
        )

        attachment_metadata = {"filename": file.filename}

        # ----- IMAGE -----
        if file.content_type in SUPPORTED_TYPES["image"]:
            media_type = MediaType.image
            image_description = await analyze_image_vision_fn(file_url)
            attachment_metadata["image_description"] = image_description

        # ----- AUDIO -----
        elif file.content_type in SUPPORTED_TYPES["audio"]:
            media_type = MediaType.audio
            text_content = transcribe_file(job_name="audio_transcribe", s3_uri=file_url)
            attachment_metadata["transcription"] = text_content

        # ----- DOCUMENT -----
        elif file.content_type in SUPPORTED_TYPES["document"]:
            media_type = MediaType.document
            doc_text = await extract_text_from_s3_docs(file_url)
            attachment_metadata["document_text"] = doc_text

        else:
            media_type = None

        message_content = (
            prompt or f"Uploaded a {media_type.value if media_type else 'file'}"
        )

        user_msg = await create_message(db, session.id, RoleEnum.user, message_content)

        await create_attachment(
            db,
            session.id,
            user_msg.id,
            file_url,
            media_type,
            attachment_metadata,
        )
    else:
        message_content = prompt or "User sent a text message"
        user_msg = await create_message(
            db,
            session.id,
            RoleEnum.user,
            message_content,
        )

    # Step 2: Build conversation history directly from DB
    previous_messages = await get_messages_by_session(db, session.id)

    history = [
        {"role": msg.role.value, "content": msg.content} for msg in previous_messages
    ]

    # Step 2a: Inject image description or Transcription or or extracted doc text
    system_context_msg = None
    if file:
        if "image_description" in attachment_metadata:
            system_context_msg = (
                f"OCR extracted from image: {attachment_metadata['image_description']}"
            )
        elif "transcription" in attachment_metadata:
            system_context_msg = (
                f"Transcription of audio: {attachment_metadata['transcription']}"
            )
        elif "document_text" in attachment_metadata:
            system_context_msg = f"Extracted text from document: {attachment_metadata['document_text'][:2000]}"  # truncate for safety

        # if (
        #     file.content_type in SUPPORTED_TYPES["image"]
        #     and "image_description" in attachment_metadata
        #     and attachment_metadata["image_description"]
        # ):
        #     system_context_msg = f"Extracted description from image: {attachment_metadata['image_description']}"
        # elif (
        #     file.content_type in SUPPORTED_TYPES["audio"]
        #     and "transcription" in attachment_metadata
        #     and attachment_metadata["transcription"]
        # ):
        #     system_context_msg = (
        #         f"Transcription of audio: {attachment_metadata['transcription']}"
        #     )

        # elif "document_text" in attachment_metadata:
        #     system_context_msg = f"Extracted text from document: {attachment_metadata['document_text'][:2000]}"  # truncate for safety

        if system_context_msg:
            # Add as a system message as last in history
            history.append({"role": "system", "content": system_context_msg})

    # Step 3: Generate assistant response using enriched LLM context
    assistant_content = await generate_response(history)

    assistant_msg = await create_message(
        db, session.id, RoleEnum.assistant, assistant_content
    )

    response_payload = {
        "assistant_message": assistant_msg.content,
        "session_id": str(session.id),
        "message_id": str(assistant_msg.id),
    }

    # Step 4: Audio Output (Assistant reply)
    if audio_output:
        audio_output_service = AudioOutput()
        audio_s3_url = await audio_output_service.convert_text_into_audio(
            assistant_content=assistant_content,
            voice_style=voice_style.value,
        )

        response_payload["audio_output_url"] = audio_s3_url

        await create_attachment(
            db=db,
            session_id=session.id,
            message_id=assistant_msg.id,
            url=audio_s3_url,
            media_type=MediaType.audio,
            metadata_={"voice_style": voice_style.value},
            audio_url=audio_s3_url,
        )

    if file_url:
        response_payload["uploaded_file_url"] = file_url

    return response_payload
