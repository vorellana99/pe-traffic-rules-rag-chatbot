"""Test de integración del grafo RAG end-to-end (contra Ollama).

Invoca el pipeline compilado y verifica que produce una respuesta con al menos
una cita `[n]`. Lento: la generación con qwen2.5:7b corre en CPU.
"""
import re

from app.core.db import AsyncSessionLocal
from app.graph.pipeline import graph


async def test_graph_end_to_end_returns_answer_with_citation() -> None:
    async with AsyncSessionLocal() as session:
        result = await graph.ainvoke(
            {
                "question": "¿cuál es el límite de velocidad en zona residencial?",
                "history": [],
            },
            config={"configurable": {"session": session}},
        )

    assert result["retrieved_chunks"], "el retrieval no devolvió chunks"
    answer = result["answer"]
    assert answer.strip(), "la respuesta está vacía"
    # Debe citar el contexto con al menos un marcador [n].
    assert re.search(r"\[\d+\]", answer), f"sin cita [n] en la respuesta: {answer!r}"
