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
