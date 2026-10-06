"""Acceso a datos de `conversations`."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


async def create(session: AsyncSession, *, title: str | None = None) -> Conversation:
    conversation = Conversation(title=title)
    session.add(conversation)
    await session.flush()
    return conversation


async def get(
    session: AsyncSession, conversation_id: uuid.UUID
) -> Conversation | None:
    return await session.get(Conversation, conversation_id)


async def list_all(session: AsyncSession) -> list[Conversation]:
    result = await session.execute(
        select(Conversation).order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())
