"""Tests de integración del retrieval híbrido contra los datos del seed.

Requieren la DB seedeada y Ollama corriendo (embedding de la query). Timeouts
generosos porque el modelo corre en CPU. La fusión RRF pura se testea en
`tests/unit/test_rrf.py`.
"""
from app.core.db import AsyncSessionLocal
from app.services.retrieval_service import retrieve


async def test_retrieve_returns_expected_chunk_in_top3() -> None:
    async with AsyncSessionLocal() as session:
        results = await retrieve(
            session, "¿cuál es el límite de velocidad en zona residencial?"
        )

    assert 0 < len(results) <= 6
    top3 = results[:3]
    # El cuadro de límites de velocidad del RNT (km/h por zona) debe aparecer.
    assert any(
        r.filename == "rnt-tuo.pdf" and "km/h" in r.content for r in top3
    ), [f"{r.filename} p{r.page}" for r in top3]


async def test_retrieve_returns_metadata_and_scores() -> None:
    async with AsyncSessionLocal() as session:
        results = await retrieve(
            session, "requisitos para obtener la licencia de conducir clase A"
        )

    assert results
    for r in results:
        assert r.filename
        assert r.content
        assert r.score > 0
    # Los scores vienen ordenados de mayor a menor.
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
