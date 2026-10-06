"""Router de evaluación: expone los resultados de RAGAS."""
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services import eval_service

router = APIRouter(prefix="/eval", tags=["eval"])


@router.get("/results")
async def get_eval_results() -> dict[str, Any]:
    results = eval_service.get_results()
    if results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aún no hay resultados de evaluación.",
        )
    return results
