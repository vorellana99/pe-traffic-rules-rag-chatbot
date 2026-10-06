"""Retrieval híbrido: vectorial (coseno) + full-text (español) fusionados con RRF.

Pipeline (ver sección 6 del PLAN):
  - top-20 por distancia coseno (pgvector, índice HNSW)
  - top-20 por `ts_rank` sobre `content_tsv` (full-text español, índice GIN)
  - fusión Reciprocal Rank Fusion (k=60)
  - top-6 final
"""
import uuid
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document
from app.providers.factory import build_embedding_provider

CANDIDATE_K = 20  # candidatos por cada método
TOP_K = 6         # resultado final
RRF_K = 60        # constante de Reciprocal Rank Fusion


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page: int | None
    content: str
    score: float


async def _vector_search(
    session: AsyncSession, query_vector: list[float], limit: int
) -> list[uuid.UUID]:
    stmt = (
        select(Chunk.id)
        .where(Chunk.embedding.isnot(None))
        .order_by(Chunk.embedding.cosine_distance(query_vector))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [row[0] for row in result.all()]


async def _fulltext_search(
    session: AsyncSession, query: str, limit: int
) -> list[uuid.UUID]:
    stmt = text(
        """
        SELECT id
        FROM chunks
        WHERE content_tsv @@ plainto_tsquery('spanish', :q)
        ORDER BY ts_rank(content_tsv, plainto_tsquery('spanish', :q)) DESC
        LIMIT :limit
        """
    )
    result = await session.execute(stmt, {"q": query, "limit": limit})
    return [row[0] for row in result.all()]


def _rrf_fuse(
    ranked_lists: list[list[uuid.UUID]], k: int
) -> list[tuple[uuid.UUID, float]]:
    """Reciprocal Rank Fusion: score(d) = Σ 1/(k + rank_i(d))."""
    scores: dict[uuid.UUID, float] = {}
    for ranked in ranked_lists:
        for rank, chunk_id in enumerate(ranked, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


async def _hydrate(
    session: AsyncSession, scored: list[tuple[uuid.UUID, float]]
) -> list[RetrievedChunk]:
    if not scored:
        return []
    ids = [chunk_id for chunk_id, _ in scored]
    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Chunk.page,
            Chunk.content,
            Document.filename,
        )
        .join(Document, Document.id == Chunk.document_id)
        .where(Chunk.id.in_(ids))
    )
    result = await session.execute(stmt)
    rows = {row.id: row for row in result.all()}

    hydrated: list[RetrievedChunk] = []
    for chunk_id, score in scored:
        row = rows.get(chunk_id)
        if row is None:
            continue
        hydrated.append(
            RetrievedChunk(
                chunk_id=row.id,
                document_id=row.document_id,
                filename=row.filename,
                page=row.page,
                content=row.content,
                score=score,
            )
        )
    return hydrated


async def retrieve(
    session: AsyncSession,
    query: str,
    *,
    top_k: int = TOP_K,
    candidate_k: int = CANDIDATE_K,
    rrf_k: int = RRF_K,
) -> list[RetrievedChunk]:
    """Recupera los `top_k` chunks más relevantes para `query` (híbrido + RRF)."""
    embedder = build_embedding_provider()
    query_vector = await embedder.embed_query(query)

    vector_ids = await _vector_search(session, query_vector, candidate_k)
    fulltext_ids = await _fulltext_search(session, query, candidate_k)

    fused = _rrf_fuse([vector_ids, fulltext_ids], k=rrf_k)
    return await _hydrate(session, fused[:top_k])
