"""Nodos del grafo RAG: rewrite_query -> retrieve -> generate."""
from langchain_core.runnables import RunnableConfig
from langgraph.types import StreamWriter

from app.graph.state import RAGState
from app.prompts.query_rewrite import (
    QUERY_REWRITE_SYSTEM_PROMPT,
    build_rewrite_prompt,
)
from app.prompts.rag_answer import RAG_SYSTEM_PROMPT, build_user_prompt
from app.providers.factory import build_llm_provider
from app.services import retrieval_service


async def rewrite_query(state: RAGState) -> dict:
    """Reformula la pregunta a una consulta autocontenida (solo con historial)."""
    llm = build_llm_provider()
    prompt = build_rewrite_prompt(state["question"], state.get("history") or [])
    rewritten = (
        await llm.generate(prompt, system=QUERY_REWRITE_SYSTEM_PROMPT)
    ).strip()
    return {"rewritten_query": rewritten or state["question"]}


async def retrieve(state: RAGState, config: RunnableConfig) -> dict:
    """Recupera los chunks relevantes (retrieval híbrido)."""
    session = config["configurable"]["session"]
    query = state.get("rewritten_query") or state["question"]
    chunks = await retrieval_service.retrieve(session, query)
    return {"retrieved_chunks": chunks}


async def generate(state: RAGState, writer: StreamWriter) -> dict:
    """Genera la respuesta citando el contexto; emite tokens vía StreamWriter."""
    llm = build_llm_provider()
    chunks = state.get("retrieved_chunks") or []
    prompt = build_user_prompt(state["question"], chunks)

    parts: list[str] = []
    async for token in llm.stream(prompt, system=RAG_SYSTEM_PROMPT):
        parts.append(token)
        if writer:
            writer({"token": token})
    return {"answer": "".join(parts)}
