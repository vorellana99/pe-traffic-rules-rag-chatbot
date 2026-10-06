"""Servicio de chat: orquesta el grafo RAG, emite eventos SSE y persiste.

Emite el flujo tipado del contrato (sección 5):
  status -> sources -> token* -> done   (o error)
Crea la conversación si no existe y guarda los mensajes user/assistant
(con `sources` jsonb en el del asistente).
"""
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from app.core.db import AsyncSessionLocal
from app.graph.pipeline import graph
from app.repositories import conversation_repo, message_repo
from app.services.retrieval_service import RetrievedChunk


def _event(event: str, data: Any) -> dict[str, str]:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


def _to_source_dict(chunk: RetrievedChunk) -> dict[str, Any]:
    return {
        "chunk_id": str(chunk.chunk_id),
        "document_id": str(chunk.document_id),
        "filename": chunk.filename,
        "page": chunk.page,
        "content": chunk.content,
        "score": chunk.score,
    }


async def stream_chat(
    conversation_id: uuid.UUID | None, message: str
) -> AsyncIterator[dict[str, str]]:
    async with AsyncSessionLocal() as session:
        try:
            # --- Conversación (crea si no viene id) ---
            if conversation_id is not None:
                conversation = await conversation_repo.get(session, conversation_id)
                if conversation is None:
                    yield _event("error", {"detail": "Conversación no encontrada."})
                    return
            else:
                conversation = await conversation_repo.create(
                    session, title=message[:60]
                )
                await session.commit()

            # --- Historial previo (antes de guardar el mensaje actual) ---
            prior = await message_repo.list_by_conversation(session, conversation.id)
            history = [(m.role, m.content) for m in prior]

            # --- Persistir mensaje del usuario ---
            await message_repo.create(session, conversation.id, "user", message)
            await session.commit()

            # --- Ejecutar el grafo con streaming ---
            yield _event(
                "status", {"stage": "rewriting" if history else "retrieving"}
            )

            state = {"question": message, "history": history}
            config = {"configurable": {"session": session}}
            answer_parts: list[str] = []
            sources: list[RetrievedChunk] = []

            async for mode, data in graph.astream(
                state, config, stream_mode=["updates", "custom"]
            ):
                if mode == "custom":
                    token = data.get("token")
                    if token:
                        answer_parts.append(token)
                        yield _event("token", {"text": token})
                elif mode == "updates":
                    for node_name, update in data.items():
                        if node_name == "rewrite_query":
                            yield _event("status", {"stage": "retrieving"})
                        elif node_name == "retrieve":
                            sources = update.get("retrieved_chunks") or []
                            yield _event(
                                "sources", [_to_source_dict(c) for c in sources]
                            )
                            yield _event("status", {"stage": "generating"})
                        elif node_name == "generate" and update.get("answer"):
                            answer_parts = [update["answer"]]

            answer = "".join(answer_parts)

            # --- Persistir respuesta del asistente con sus fuentes ---
            assistant = await message_repo.create(
                session,
                conversation.id,
                "assistant",
                answer,
                sources=[_to_source_dict(c) for c in sources],
            )
            await session.commit()

            yield _event(
                "done",
                {
                    "message_id": str(assistant.id),
                    "conversation_id": str(conversation.id),
                },
            )
        except Exception as exc:  # noqa: BLE001
            yield _event("error", {"detail": str(exc)})
