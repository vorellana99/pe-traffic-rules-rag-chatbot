"""Router de conversaciones."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories import conversation_repo, message_repo
from app.schemas.chat import ConversationOut, MessageOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    session: AsyncSession = Depends(get_db),
) -> list[ConversationOut]:
    return await conversation_repo.list_all(session)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> list[MessageOut]:
    conversation = await conversation_repo.get(session, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await message_repo.list_by_conversation(session, conversation_id)
