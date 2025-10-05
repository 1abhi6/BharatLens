# sessions, send message, history
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.api.deps import get_current_user
from app.crud.message import create_message
from app.crud.session import create_chat_session, get_chat_session
from app.db.session import get_async_session
from app.models.message import RoleEnum
from app.schemas.message import MessageCreate, MessageRead
from app.schemas.session import SessionCreate, SessionRead
from app.services.llm_client import generate_response
from app.models.chat_session import ChatSession
from app.schemas.session import SessionWithMessages
from app.models import Message

router = APIRouter(prefix="/chat", tags=["Chat"])


# List all the user sessions and their related messages
@router.get("/sessions", response_model=List[SessionWithMessages])
async def list_user_sessions(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    query = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .options(selectinload(ChatSession.messages).selectinload(Message.attachments))
        .order_by(ChatSession.created_at.desc())
    )
    result = await db.execute(query)
    sessions = result.scalars().unique().all()
    return sessions


# Create a new chat session
@router.post("/sessions", response_model=SessionRead)
async def create_session(
    session_in: SessionCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    return await create_chat_session(
        db, user_id=current_user.id, title=session_in.title
    )


# Send a message in a session and get LLM response
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
    await create_message(db, session_id, RoleEnum.user, message_in.content)

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


# Based on a session_id, fetch all messages in that session
@router.get("/sessions/{session_id}/messages", response_model=List[MessageRead])
async def get_session_messages(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    session = await get_chat_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your session")

    query = (
        select(Message)
        .where(Message.session_id == session_id)
        .options(selectinload(Message.attachments))
        .order_by(Message.created_at)
    )
    result = await db.execute(query)
    messages = result.scalars().all()
    return messages


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
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

    await db.delete(session)
    await db.commit()
    return None
