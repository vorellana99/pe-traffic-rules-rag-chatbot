# TránsitoRAG — Reglas del proyecto

## Fuente de verdad

- **PLAN.md es la única fuente de verdad.** Léelo completo antes de hacer cualquier cosa.
- No implementes nada que no esté en PLAN.md. Si falta una decisión, elige la opción más simple y anótala en la sección "Decisiones tomadas" de PLAN.md.

## Flujo de trabajo

1. Identifica la PRIMERA tarea sin marcar `[ ]` en PLAN.md, en orden estricto.
2. Implementa SOLO esa tarea, por completo.
3. Ejecuta su comando de *Verificación* tal como está escrito.
4. Solo si la verificación pasa: marca la tarea `[x]` en PLAN.md y haz commit (`feat|fix|chore(fase-N): descripción` en inglés).
5. Si la verificación falla: arregla y reintenta. Nunca marques una tarea sin verificación exitosa.
6. Una tarea por iteración. Al terminar, detente.

## Stack y restricciones (resumen — detalle en PLAN.md)

- Backend: Python 3.12, FastAPI, LangChain + LangGraph, SQLAlchemy async, Alembic.
- LLM/embeddings: SOLO Ollama local (`qwen2.5:7b` + `bge-m3`, 1024 dims). Prohibido introducir APIs de pago o servicios cloud.
- DB: PostgreSQL 16 + pgvector. Frontend: React 18 + TS + Vite + Tailwind + shadcn/ui + TanStack Query.
- Todo se levanta con `docker compose up`. Ejecuta tests y comandos DENTRO de los contenedores (`docker compose exec api ...`).
- Dependencias siempre pinneadas. Prompts del sistema en español, en `backend/app/prompts/`.

## Comandos (desde la raíz del repo; ver `Makefile`)

- `cp .env.example .env` y luego `make up` (build + arranque; el primer boot descarga los modelos de Ollama vía `ollama-init`). `make down`, `make logs`.
- `make test` = `docker compose exec api pytest -q`. Un solo test: `docker compose exec api pytest tests/unit/test_rrf.py::test_nombre -q`. Los tests de `tests/integration/` necesitan Ollama y son lentos.
- `make lint` = `ruff check .` (backend, line-length 88) + eslint/prettier (frontend). Frontend: `npm run build` hace `tsc -b && vite build`.
- `make seed` ingesta `data/seed_pdfs/`; `make eval` corre `python -m eval.evaluate` (`backend/eval/evaluate.py`, RAGAS) sobre `eval/dataset.jsonl` y escribe `eval/results.json` (lo muestra la página Eval).
- Puertos: api 8000, frontend 5173, Postgres 5432, Ollama 11434.
- `./loop.sh [N]` ejecuta Claude Code en bucle (una tarea de PLAN.md por iteración, con `--dangerously-skip-permissions`).

## Arquitectura (visión general)

- **Pipeline RAG** (`backend/app/graph/`): grafo LangGraph `START → [rewrite_query solo si hay historial] → retrieve → generate → END`, compilado como singleton en `pipeline.py`; el estado está en `state.py` y los nodos en `nodes.py`.
- **Recuperación híbrida** (`services/retrieval_service.py`): búsqueda vectorial (pgvector HNSW) + full-text (`tsvector` en español), fusionadas con RRF (cubierto por `tests/unit/test_rrf.py`).
- **Streaming**: `POST /api/chat` responde por SSE (etapas del pipeline, tokens, fuentes citadas `[n]`); el frontend lo consume con `lib/sse.ts` + `hooks/useChatStream.ts`. Mensajes y fuentes se persisten en Postgres.
- **Ingesta** (`services/ingestion_service.py`): PyMuPDF → chunking por estructura → embeddings, en segundo plano; el estado del documento (`processing → ready`) se consulta por polling desde el frontend (`hooks/useDocuments.ts`).
- **Providers** (`app/providers/`): `EmbeddingProvider`/`LLMProvider` en `base.py`, implementación Ollama y selección en `factory.py`; es la única capa que conoce el modelo/dimensión.
- Routers montados en `app/main.py` (`/api/{documents,chat,conversations,eval}` + health sin prefijo).

## Convenciones de código

- Routers sin lógica de negocio: routers → services → repositories → providers.
- Config solo vía `app/core/config.py` (pydantic-settings). Nada de `os.getenv` disperso.
- La dimensión del embedding se lee del provider; nunca hardcodearla fuera de él.
- Tests: pytest en backend (unit + integration). Los tests de integración contra Ollama usan timeouts generosos (≥120s) porque el modelo corre en CPU.

## Cosas que NO debes hacer

- No descargues PDFs de sitios del gobierno en scripts; el seed usa los archivos ya presentes en `data/seed_pdfs/`.
- No refactorices tareas ya completadas salvo que una verificación posterior lo exija.
- No cambies modelos, dimensiones ni stack sin instrucción explícita del usuario.
- No inventes contenido normativo: el dataset de evaluación se redacta leyendo los PDFs reales.
