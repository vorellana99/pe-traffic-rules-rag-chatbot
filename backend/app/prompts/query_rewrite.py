"""Prompt de reformulación de consulta (query rewrite).

Convierte la última pregunta del usuario en una consulta de búsqueda
autocontenida usando el historial para resolver referencias.
"""
from collections.abc import Sequence

QUERY_REWRITE_SYSTEM_PROMPT = """\
Tu tarea es reformular la última pregunta del usuario en una única consulta de \
búsqueda autocontenida, en español, sobre normativa de tránsito y licencias de \
conducir del Perú.

Reglas:
- Usa el historial SOLO para resolver referencias implícitas (por ejemplo "y esa \
multa", "ese artículo", "¿y para la clase B?").
- Devuelve UNA sola consulta, sin explicaciones, sin comillas y sin prefijos.
- Si la pregunta ya es autocontenida, devuélvela tal cual.
"""


def build_rewrite_prompt(
    question: str, history: Sequence[tuple[str, str]]
) -> str:
    """Arma el mensaje de usuario: historial + pregunta actual.

    `history` es una secuencia de (rol, contenido), del más antiguo al más reciente.
    """
    if history:
        lines = [f"{role}: {content}" for role, content in history]
        rendered_history = "\n".join(lines)
    else:
        rendered_history = "(sin historial)"
    return (
        f"HISTORIAL:\n{rendered_history}\n\n"
        f"PREGUNTA ACTUAL:\n{question}\n\n"
        "CONSULTA AUTOCONTENIDA:"
    )
