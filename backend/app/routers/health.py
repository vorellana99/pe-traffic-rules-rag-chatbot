"""Router de health-check.

Verifica DB, conexión a Ollama y disponibilidad de los dos modelos. La lógica
vive en `services/health_service.py` (routers sin lógica de negocio).
"""
from fastapi import APIRouter, Response, status

from app.services import health_service

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(response: Response) -> dict:
    payload, ok = await health_service.check_health()
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload
