"""Prompt de respuesta RAG (system + render de contexto numerado).

El LLM responde citando con `[n]`, donde `n` mapea por índice al contexto
numerado (y al array `sources` del contrato SSE).
"""
from collections.abc import Sequence
from typing import Protocol

RAG_SYSTEM_PROMPT = """\
Eres un asistente experto en normativa de tránsito y licencias de conducir del \
Perú (Reglamento Nacional de Tránsito, cuadro de infracciones y sanciones, y \
reglamento de licencias de conducir).

Reglas que debes seguir estrictamente:
1. Responde ÚNICAMENTE con la información del CONTEXTO numerado que se te entrega. \
No uses conocimiento externo ni supongas datos.
2. Cita cada afirmación con el número de su fuente entre corchetes, por ejemplo \
[1] o [2]. Si combinas varias fuentes, cítalas todas: [1][3].
3. Si el contexto no contiene la respuesta, dilo con claridad: indica que no \
encontraste esa información en los documentos disponibles. Nunca inventes.
4. Cuando el contexto lo permita, incluye datos concretos: número de artículo, \
código de infracción, monto de la multa, puntos y medidas.
5. Responde en español, con un tono profesional, preciso y claro.
"""


class Citable(Protocol):
    filename: str
    page: int | None
    content: str


def render_context(chunks: Sequence[Citable]) -> str:
    """Formatea los chunks como bloques numerados [1], [2], ... con su fuente."""
    if not chunks:
        return "(No se encontró contexto relevante en los documentos.)"
    blocks: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        page = f", pág. {chunk.page}" if chunk.page is not None else ""
        blocks.append(f"[{index}] ({chunk.filename}{page})\n{chunk.content.strip()}")
    return "\n\n".join(blocks)


def build_user_prompt(question: str, chunks: Sequence[Citable]) -> str:
    """Arma el mensaje de usuario: contexto numerado + pregunta."""
    context = render_context(chunks)
    return (
        f"CONTEXTO:\n{context}\n\n"
        f"PREGUNTA:\n{question}\n\n"
        "RESPUESTA (responde solo con el contexto y cita con [n]):"
    )
