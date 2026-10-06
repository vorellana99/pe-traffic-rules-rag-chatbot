"""Lectura de los resultados de evaluación (`eval/results.json`)."""
import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings

settings = get_settings()


def get_results() -> dict[str, Any] | None:
    """Devuelve el contenido de results.json, o None si aún no existe."""
    path = Path(settings.eval_results_path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
