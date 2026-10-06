"""Chequeo de salud de las dependencias: base de datos y Ollama.

Verifica conexión a la DB, conexión a Ollama y que los dos modelos configurados
(LLM y embeddings) estén efectivamente disponibles (`GET /api/tags`).
"""
import httpx
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal

settings = get_settings()


async def _check_db() -> dict:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "detail": str(exc)}


def _model_present(required: str, available: list[str]) -> bool:
    """Un modelo cuenta como disponible si su tag coincide.

    Ollama guarda un pull sin tag como `<nombre>:latest` (p. ej. `bge-m3` ->
    `bge-m3:latest`), mientras que `qwen2.5:7b` conserva su tag explícito.
    """
    if required in available:
        return True
    if ":" not in required and f"{required}:latest" in available:
        return True
    return False


async def _check_ollama() -> dict:
    required = [settings.llm_model, settings.embedding_model]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
        available = [m.get("name", "") for m in data.get("models", [])]
        models_status = {m: _model_present(m, available) for m in required}
        ok = all(models_status.values())
        return {
            "status": "ok" if ok else "error",
            "models": models_status,
            "available": available,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "detail": str(exc),
            "models": {m: False for m in required},
        }


async def check_health() -> tuple[dict, bool]:
    """Devuelve (payload, ok). `ok` es True solo si todo está sano."""
    db = await _check_db()
    ollama = await _check_ollama()
    ok = db["status"] == "ok" and ollama["status"] == "ok"
    payload = {
        "status": "ok" if ok else "degraded",
        "dependencies": {"database": db, "ollama": ollama},
    }
    return payload, ok
