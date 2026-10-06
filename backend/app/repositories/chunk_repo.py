"""Acceso a datos de `chunks`."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk


async def bulk_insert(session: AsyncSession, chunks: list[Chunk]) -> None:
    session.add_all(chunks)
    await session.flush()


async def count_by_document(session: AsyncSession, document_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count()).select_from(Chunk).where(Chunk.document_id == document_id)
    )
    return int(result.scalar_one())
