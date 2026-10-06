"""Acceso a datos de `documents`."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


async def create(
    session: AsyncSession, *, filename: str, title: str | None = None
) -> Document:
    document = Document(filename=filename, title=title, status="processing")
    session.add(document)
    await session.flush()
    return document


async def get(session: AsyncSession, document_id: uuid.UUID) -> Document | None:
    return await session.get(Document, document_id)


async def list_all(session: AsyncSession) -> list[Document]:
    result = await session.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def delete(session: AsyncSession, document: Document) -> None:
    # Los chunks se eliminan por el FK ON DELETE CASCADE de la DB.
    await session.delete(document)
