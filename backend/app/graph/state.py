"""Estado tipado del grafo RAG (LangGraph)."""
from typing import TypedDict

from app.services.retrieval_service import RetrievedChunk


class RAGState(TypedDict, total=False):
    question: str
    history: list[tuple[str, str]]  # (rol, contenido), del más antiguo al reciente
    rewritten_query: str
    retrieved_chunks: list[RetrievedChunk]
    answer: str
