"""Evaluación offline del pipeline RAG.

Para cada pregunta del dataset ejecuta el pipeline real (retrieval + generación)
y computa tres métricas con el LLM local como juez (LLM-as-judge):
  - faithfulness: qué parte de la respuesta está respaldada por el contexto.
  - answer_relevancy: qué tan relevante es la respuesta a la pregunta.
  - context_precision: qué tan útil es el contexto recuperado (según ground_truth).

Exporta `eval/results.json` (global + por pregunta + timestamp + modelos).
Escribe checkpoints tras cada pregunta y es resumible (omite las ya evaluadas).

Nota (Decisión): el plan menciona RAGAS, pero RAGAS con un modelo 7B en CPU es
inviable (muchas llamadas al juez por métrica, horas de cómputo y NaN frecuentes).
Se implementa un juez local equivalente para las mismas tres métricas.

Uso:  python -m eval.evaluate [--limit N]
"""
import argparse
import asyncio
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.prompts.rag_answer import RAG_SYSTEM_PROMPT, build_user_prompt
from app.providers.base import LLMProvider
from app.providers.factory import build_llm_provider
from app.services.retrieval_service import retrieve

settings = get_settings()

DATASET_PATH = Path("/app/eval/dataset.jsonl")
OUTPUT_PATH = Path(settings.eval_results_path)
METRICS = ("faithfulness", "answer_relevancy", "context_precision")

JUDGE_SYSTEM = (
    "Eres un evaluador riguroso de sistemas de preguntas y respuestas. "
    "Respondes ÚNICAMENTE con un número decimal entre 0 y 1, sin explicaciones."
)


def _parse_score(text: str) -> float:
    match = re.search(r"(\d+(?:[.,]\d+)?)", text or "")
    if not match:
        return 0.0
    value = float(match.group(1).replace(",", "."))
    if value > 1.0:  # el juez respondió en porcentaje o escala 0-10/0-100
        value = value / 100.0 if value <= 100.0 else 1.0
    return max(0.0, min(1.0, value))


def _truncate_contexts(contexts: list[str], per_chunk: int = 600) -> str:
    parts = []
    for i, content in enumerate(contexts, 1):
        parts.append(f"[{i}] {content.strip()[:per_chunk]}")
    return "\n\n".join(parts)


async def _judge(llm: LLMProvider, prompt: str) -> float:
    return _parse_score(await llm.generate(prompt, system=JUDGE_SYSTEM))


async def _faithfulness(llm: LLMProvider, answer: str, contexts: list[str]) -> float:
    prompt = (
        f"CONTEXTO:\n{_truncate_contexts(contexts)}\n\n"
        f"RESPUESTA:\n{answer}\n\n"
        "¿Qué proporción de las afirmaciones de la RESPUESTA está respaldada por "
        "el CONTEXTO? 0.0 = nada respaldada, 1.0 = totalmente respaldada. "
        "Si la respuesta admite que no hay información y el contexto no la contiene, "
        "eso cuenta como respaldado."
    )
    return await _judge(llm, prompt)


async def _answer_relevancy(llm: LLMProvider, question: str, answer: str) -> float:
    prompt = (
        f"PREGUNTA:\n{question}\n\n"
        f"RESPUESTA:\n{answer}\n\n"
        "¿Qué tan relevante y directa es la RESPUESTA respecto de la PREGUNTA? "
        "0.0 = irrelevante, 1.0 = totalmente relevante."
    )
    return await _judge(llm, prompt)


async def _context_precision(
    llm: LLMProvider, question: str, ground_truth: str, contexts: list[str]
) -> float:
    prompt = (
        f"PREGUNTA:\n{question}\n\n"
        f"RESPUESTA DE REFERENCIA:\n{ground_truth}\n\n"
        f"CONTEXTO RECUPERADO:\n{_truncate_contexts(contexts)}\n\n"
        "¿Qué tan útil y preciso es el CONTEXTO para responder la PREGUNTA de "
        "acuerdo con la RESPUESTA DE REFERENCIA? 0.0 = inútil, 1.0 = muy preciso."
    )
    return await _judge(llm, prompt)


async def _evaluate_one(session, llm: LLMProvider, item: dict) -> dict:
    chunks = await retrieve(session, item["question"])
    contexts = [c.content for c in chunks]
    answer = await llm.generate(
        build_user_prompt(item["question"], chunks), system=RAG_SYSTEM_PROMPT
    )
    return {
        "question": item["question"],
        "answer": answer,
        "faithfulness": await _faithfulness(llm, answer, contexts),
        "answer_relevancy": await _answer_relevancy(llm, item["question"], answer),
        "context_precision": await _context_precision(
            llm, item["question"], item["ground_truth"], contexts
        ),
    }


def _write_results(per_question: list[dict]) -> None:
    glob = {
        m: round(sum(q[m] for q in per_question) / len(per_question), 4)
        for m in METRICS
    }
    results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "models": {"llm": settings.llm_model, "embedding": settings.embedding_model},
        "global": glob,
        "per_question": per_question,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_existing() -> list[dict]:
    if not OUTPUT_PATH.exists():
        return []
    try:
        return json.loads(OUTPUT_PATH.read_text(encoding="utf-8")).get(
            "per_question", []
        )
    except (json.JSONDecodeError, OSError):
        return []


async def main(limit: int | None) -> None:
    items = [
        json.loads(line)
        for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if limit:
        items = items[:limit]

    per_question = _load_existing()
    done = {q["question"] for q in per_question}
    llm = build_llm_provider()

    async with AsyncSessionLocal() as session:
        for i, item in enumerate(items, 1):
            if item["question"] in done:
                print(f"[{i}/{len(items)}] (ya evaluada) {item['question'][:55]}")
                continue
            print(f"[{i}/{len(items)}] {item['question'][:55]}…", flush=True)
            result = await _evaluate_one(session, llm, item)
            per_question.append(result)
            _write_results(per_question)  # checkpoint
            print(
                f"   faith={result['faithfulness']:.2f} "
                f"rel={result['answer_relevancy']:.2f} "
                f"prec={result['context_precision']:.2f}",
                flush=True,
            )

    print(f"\nListo. {len(per_question)} preguntas -> {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluación RAG offline")
    parser.add_argument("--limit", type=int, default=None, help="evaluar solo N")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.limit)))
