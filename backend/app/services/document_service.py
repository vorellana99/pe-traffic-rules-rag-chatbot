"""Casos de uso de documentos: creación, ingesta background, listado y borrado.

Flujo de ingesta (background): leer PDF del volumen -> parse -> chunk ->
embeddings en batches -> insert. Actualiza `status`/`chunk_count`/`pages` y
captura cualquier error en `error_message`.
"""
import logging
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.models.chunk import Chunk
from app.models.document import Document
from app.providers.factory import build_embedding_provider
from app.repositories import chunk_repo, document_repo
from app.services.ingestion_service import parse_pdf

logger = logging.getLogger(__name__)
settings = get_settings()


def _pdf_path(document_id: uuid.UUID) -> Path:
    return Path(settings.upload_dir) / f"{document_id}.pdf"


async def create_pending(
    session: AsyncSession, filename: str, data: bytes
) -> Document:
    """Crea el registro en estado `processing` y guarda el PDF en el volumen."""
    document = await document_repo.create(session, filename=filename)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    _pdf_path(document.id).write_bytes(data)
    await session.commit()
    await session.refresh(document)
    return document


async def list_documents(session: AsyncSession) -> list[Document]:
    return await document_repo.list_all(session)


async def get_document(
    session: AsyncSession, document_id: uuid.UUID
) -> Document | None:
    return await document_repo.get(session, document_id)


async def delete_document(session: AsyncSession, document_id: uuid.UUID) -> bool:
    document = await document_repo.get(session, document_id)
    if document is None:
        return False
    await document_repo.delete(session, document)
    await session.commit()
    _pdf_path(document_id).unlink(missing_ok=True)
    return True


async def ingest_document(document_id: uuid.UUID) -> None:
    """Tarea en background: usa su propia sesión (no la del request)."""
    async with AsyncSessionLocal() as session:
        document = await document_repo.get(session, document_id)
        if document is None:
            logger.warning("ingest_document: documento %s no existe", document_id)
            return
        try:
            data = _pdf_path(document_id).read_bytes()
            parsed = parse_pdf(data)

            embedder = build_embedding_provider()
            batch_size = settings.embedding_batch_size
            orm_chunks: list[Chunk] = []
            for start in range(0, len(parsed.chunks), batch_size):
                batch = parsed.chunks[start : start + batch_size]
                vectors = await embedder.embed_texts([c.content for c in batch])
                orm_chunks.extend(
                    Chunk(
                        document_id=document_id,
                        content=c.content,
                        page=c.page,
                        position=c.position,
                        embedding=vector,
                    )
                    for c, vector in zip(batch, vectors, strict=False)
                )

            await chunk_repo.bulk_insert(session, orm_chunks)
            document.pages = parsed.pages
            document.chunk_count = len(orm_chunks)
            document.status = "ready"
            await session.commit()
            logger.info(
                "Documento %s ingerido: %d chunks", document_id, len(orm_chunks)
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error ingiriendo documento %s", document_id)
            await session.rollback()
            document = await document_repo.get(session, document_id)
            if document is not None:
                document.status = "error"
                document.error_message = str(exc)[:2000]
                await session.commit()
