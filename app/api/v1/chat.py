# sessions, send message, history
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud.message import create_message, get_messages_by_session
from app.crud.session import create_chat_session, get_chat_session
from app.db.session import get_async_session
from app.models.message import RoleEnum
from app.schemas.message import MessageCreate, MessageRead
from app.schemas.session import SessionCreate, SessionRead
from app.services.llm_client import generate_response

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionRead)
async def create_session(
    session_in: SessionCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    return await create_chat_session(
        db, user_id=current_user.id, title=session_in.title
    )


@router.post("/sessions/{session_id}/messages", response_model=MessageRead)
async def send_message(
    session_id: uuid.UUID,
    message_in: MessageCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    session = await get_chat_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your session"
        )

    # Save user message
    user_msg = await create_message(db, session_id, RoleEnum.user, message_in.content)

    # Fetch recent messages for context
    history = [
        {"role": m.role.value, "content": m.content} for m in session.messages[-5:]
    ] + [{"role": "user", "content": message_in.content}]

    # Generate LLM response
    assistant_content = await generate_response(history)

    # Save assistant message
    assistant_msg = await create_message(
        db, session_id, RoleEnum.assistant, assistant_content
    )

    return assistant_msg


@router.get("/sessions/{session_id}/messages", response_model=List[MessageRead])
async def get_session_messages(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    session = await get_chat_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your session"
        )

    messages = await get_messages_by_session(db, session_id)
    return messages
