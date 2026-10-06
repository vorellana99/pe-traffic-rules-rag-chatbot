"""Tests unitarios de los prompts (renderizado, sin LLM)."""
from types import SimpleNamespace

from app.prompts.query_rewrite import (
    QUERY_REWRITE_SYSTEM_PROMPT,
    build_rewrite_prompt,
)
from app.prompts.rag_answer import (
    RAG_SYSTEM_PROMPT,
    build_user_prompt,
    render_context,
)


def _chunk(filename: str, page: int | None, content: str) -> SimpleNamespace:
    return SimpleNamespace(filename=filename, page=page, content=content)


def test_render_context_numbers_chunks() -> None:
    chunks = [
        _chunk("rnt-tuo.pdf", 71, "En zonas residenciales: 50 km/h."),
        _chunk("licencias-ds007-2016.pdf", 45, "Requisitos de la clase A."),
    ]
    context = render_context(chunks)

    assert "[1]" in context and "[2]" in context
    assert "rnt-tuo.pdf" in context and "pág. 71" in context
    assert "50 km/h" in context
    assert "Requisitos de la clase A." in context


def test_render_context_empty_is_explicit() -> None:
    assert "No se encontró" in render_context([])


def test_build_user_prompt_has_numbered_context_and_question() -> None:
    chunks = [_chunk("a.pdf", 1, "contenido uno")]
    prompt = build_user_prompt("¿cuál es la multa por luz roja?", chunks)

    assert "[1]" in prompt
    assert "contenido uno" in prompt
    assert "¿cuál es la multa por luz roja?" in prompt
    assert "CONTEXTO:" in prompt and "PREGUNTA:" in prompt


def test_rag_system_prompt_states_key_rules() -> None:
    lowered = RAG_SYSTEM_PROMPT.lower()
    assert "[1]" in RAG_SYSTEM_PROMPT  # cita con corchetes
    assert "contexto" in lowered
    assert "no encontraste" in lowered or "no inventes" in lowered


def test_build_rewrite_prompt_includes_history_and_question() -> None:
    history = [("user", "¿qué es cruzar con luz roja?"), ("assistant", "Es ...")]
    prompt = build_rewrite_prompt("¿y cuál es su multa?", history)

    assert "¿y cuál es su multa?" in prompt
    assert "luz roja" in prompt
    assert "HISTORIAL:" in prompt


def test_build_rewrite_prompt_without_history() -> None:
    prompt = build_rewrite_prompt("¿cuál es el límite de velocidad?", [])
    assert "(sin historial)" in prompt
    assert QUERY_REWRITE_SYSTEM_PROMPT  # existe y no está vacío
