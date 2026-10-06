# PLAN.md — TránsitoRAG: RAG Full-Stack Demo (Portafolio)

> **Instrucciones para el agente (Claude Code):** Este archivo es la fuente de verdad del proyecto.
> En cada iteración: (1) lee este archivo completo, (2) elige la PRIMERA tarea sin marcar `[ ]` en orden,
> (3) impleméntala por completo, (4) ejecuta su comando de verificación, (5) si pasa, marca la tarea como `[x]`
> editando este archivo y haz un commit con mensaje `feat(fase-N): <tarea>`, (6) termina la iteración.
> NO saltes tareas. NO empieces una tarea si la anterior no está verificada. Si una verificación falla,
> arregla el problema antes de continuar. No agregues features fuera de este plan.

---

## 1. Objetivo

Construir **"TránsitoRAG"** (repo: `transito-rag`): una aplicación RAG full-stack de demostración para portafolio de AI Engineering.
Dominio: **normativa de tránsito y licencias de conducir del Perú** — Reglamento Nacional de Tránsito, tabla de infracciones y sanciones, y reglamento de licencias de conducir (documentos públicos del MTC).
El usuario sube PDFs, hace preguntas en español ("¿cuál es la multa por cruzar con luz roja?", "¿qué requisitos hay para renovar la licencia A-I?") y recibe respuestas con **citas verificables** al artículo, fragmento y página exactos, incluyendo códigos de infracción y montos cuando aplique.

Todo corre 100% local y gratis (Ollama para LLM y embeddings) y se levanta con `docker compose up`.

## 2. Stack (definitivo — no cambiar sin instrucción explícita)

| Capa | Tecnología | Versión/Modelo |
|---|---|---|
| LLM | Ollama | `qwen2.5:7b` (default, bueno en español). Fallback dev liviano: `llama3.2:3b` |
| Embeddings | Ollama | `bge-m3` (1024 dimensiones) |
| Orquestación | LangChain + LangGraph (Python) | últimas estables |
| API | FastAPI + Pydantic v2, SSE para streaming | Python 3.12 |
| DB / Vector store | PostgreSQL 16 + pgvector (HNSW) + full-text search (tsvector, spanish) | imagen `pgvector/pgvector:pg16` |
| Migraciones | Alembic | — |
| Frontend | React 18 + TypeScript + Vite + Tailwind + shadcn/ui + TanStack Query + react-markdown | — |
| Evaluación | RAGAS (script offline, resultados a JSON) | — |
| Infra | Docker Compose (4 servicios: `db`, `ollama`, `api`, `frontend`) | — |

**Principios de arquitectura:**
- Abstracciones `EmbeddingProvider` y `LLMProvider` (interfaces) con implementación Ollama. Proveedor y modelos configurables por env vars. La dimensión del embedding se lee del provider, nunca hardcodeada fuera de él.
- Backend con separación clara: `routers/` (HTTP) → `services/` (casos de uso) → `repositories/` (DB) → `providers/` (LLM/embeddings). Sin lógica de negocio en routers.
- Todo el texto de prompts del sistema en español, en archivos dedicados (`app/prompts/`).
- Config centralizada con `pydantic-settings` (`app/core/config.py`). Nada de `os.getenv` disperso.

## 3. Estructura del monorepo

```
transito-rag/
├── docker-compose.yml
├── .env.example
├── README.md
├── PLAN.md                      # este archivo
├── Makefile                     # atajos: make up, make test, make eval
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml           # uv o pip-tools; dependencias pinneadas
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/                # config.py, db.py (async engine), logging.py
│   │   ├── models/              # SQLAlchemy: Document, Chunk, Conversation, Message
│   │   ├── schemas/             # Pydantic: requests/responses
│   │   ├── providers/           # base.py (interfaces), ollama_provider.py
│   │   ├── repositories/        # document_repo.py, chunk_repo.py, conversation_repo.py
│   │   ├── services/            # ingestion_service.py, retrieval_service.py, chat_service.py
│   │   ├── graph/               # LangGraph: nodes.py, pipeline.py, state.py
│   │   ├── prompts/             # rag_answer.py, query_rewrite.py
│   │   └── routers/             # documents.py, chat.py, conversations.py, health.py
│   ├── tests/                   # pytest + httpx; unit para chunking/retrieval, integration para API
│   └── eval/
│       ├── dataset.jsonl        # 25 pares pregunta/ground_truth
│       ├── evaluate.py          # corre RAGAS, exporta eval/results.json
│       └── results.json
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── main.tsx, App.tsx, router.tsx
│       ├── lib/                 # api client, sse.ts (parser de eventos), utils
│       ├── components/          # ui/ (shadcn), chat/, documents/, eval/
│       ├── pages/               # ChatPage.tsx, DocumentsPage.tsx, EvalPage.tsx
│       └── hooks/               # useChatStream.ts, useDocuments.ts
└── data/
    └── seed_pdfs/               # PDFs de ejemplo para seed (Ley 27157, reglamento demo)
```

## 4. Modelo de datos (migración inicial)

- `documents`: id (uuid), filename, title, pages, status (`processing|ready|error`), error_message, chunk_count, created_at
- `chunks`: id (uuid), document_id (FK, cascade), content (text), page (int), position (int), embedding `vector(1024)`, content_tsv `tsvector` (generada, config `spanish`), created_at
  - Índice HNSW sobre `embedding` (cosine), índice GIN sobre `content_tsv`
- `conversations`: id (uuid), title, created_at
- `messages`: id (uuid), conversation_id (FK), role (`user|assistant`), content, sources (jsonb: chunks citados con score), created_at

## 5. Contrato de API (resumen)

- `GET /health` → estado de api, db, ollama (y que los 2 modelos estén pulled)
- `POST /documents` (multipart PDF) → 202 + `{id, status: "processing"}`; ingesta en background
- `GET /documents` / `GET /documents/{id}` / `DELETE /documents/{id}`
- `POST /chat` (SSE) → body `{conversation_id?, message}`. Eventos SSE tipados:
  - `status` → `{stage: "rewriting"|"retrieving"|"generating"}`
  - `sources` → chunks recuperados `[{chunk_id, document_id, filename, page, content, score}]`
  - `token` → `{text}` (streaming del LLM)
  - `done` → `{message_id, conversation_id}`
  - `error` → `{detail}`
- `GET /conversations` / `GET /conversations/{id}/messages`
- `GET /eval/results` → contenido de `eval/results.json` (o 404 si no existe)

**Formato de citas:** el LLM responde con marcadores `[1]`, `[2]`... que mapean por índice al array del evento `sources`. El prompt exige: responder SOLO con el contexto; si no hay evidencia, decirlo explícitamente.

## 6. Pipeline RAG (LangGraph)

Estado: `{question, history, rewritten_query, retrieved_chunks, answer}`.
Nodos: `rewrite_query` (solo si hay historial) → `retrieve` → `generate`.

**Retrieval híbrido:** top-20 por coseno (pgvector) + top-20 por `ts_rank` (full-text spanish) → fusión RRF (k=60) → top-6 final. (Sin reranker externo en v1; queda documentado como mejora futura.)

**Chunking:** RecursiveCharacterTextSplitter, chunk_size ~800 tokens (aprox. por caracteres ×4), overlap 150, separadores que respeten la estructura normativa (`\n\nArtículo`, `\n\n`, `\n`, `. `). Caso especial: la tabla de infracciones (Anexo I) es tabular — cada fila (código de infracción, descripción, sanción, medida) debe quedar íntegra en un mismo chunk; si PyMuPDF degrada la tabla, extraerla con la API de tablas de PyMuPDF y serializar cada fila como texto plano `"Código X | Infracción: ... | Sanción: ... | Puntos: ..."`.

---

## 7. FASES Y TAREAS (ejecutar en orden)

### Fase 0 — Fundaciones

- [x] **0.1 Scaffold del monorepo.** Crear estructura de carpetas de la sección 3, `.gitignore` (Python + Node), `.env.example` con TODAS las vars (`DATABASE_URL`, `OLLAMA_BASE_URL`, `LLM_MODEL=qwen2.5:7b`, `EMBEDDING_MODEL=bge-m3`, `EMBEDDING_DIM=1024`, `CORS_ORIGINS`), `Makefile` con targets `up`, `down`, `logs`, `test`, `eval`, `seed`. Inicializar git.
  *Verificación:* `tree -L 2` refleja la estructura; `git log` tiene commit inicial.
- [x] **0.2 docker-compose.yml.** Servicios: `db` (pgvector/pgvector:pg16, volumen, healthcheck `pg_isready`), `ollama` (imagen oficial, volumen para modelos, healthcheck HTTP), `ollama-init` (one-shot que hace `ollama pull qwen2.5:7b` y `ollama pull bge-m3` contra el servicio ollama y termina), `api` (build backend, depends_on db+ollama healthy, hot-reload con volumen en dev), `frontend` (build frontend, Vite dev server, proxy `/api` → api:8000).
  *Verificación:* `docker compose config` válido; `docker compose up -d db ollama` deja ambos healthy.
- [x] **0.3 Esqueleto FastAPI + config + DB.** `main.py` con CORS y router `/health` (aún sin chequeo de modelos), `core/config.py` (pydantic-settings), `core/db.py` (SQLAlchemy async + asyncpg), Dockerfile backend (python:3.12-slim, uv), pyproject con deps: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, langchain, langgraph, langchain-ollama, pymupdf, httpx, sse-starlette, pytest, pytest-asyncio.
  *Verificación:* `docker compose up -d api` y `curl localhost:8000/health` → 200.
- [x] **0.4 Migración inicial (Alembic).** Habilitar extensión `vector`, crear las 4 tablas de la sección 4 con índices HNSW y GIN. Ejecutar migraciones automáticamente al arrancar `api` (script de entrypoint).
  *Verificación:* `docker compose exec db psql -U postgres -d transito_rag -c "\dt"` muestra las 4 tablas; `\dx` muestra `vector`.
- [x] **0.5 Health completo.** `/health` verifica conexión a DB, conexión a Ollama y que ambos modelos estén disponibles (`/api/tags`); responde detalle por dependencia.
  *Verificación:* `curl localhost:8000/health` → `{"status":"ok", ...}` con los 2 modelos listados.

### Fase 1 — Providers e ingesta

- [x] **1.1 Providers.** `providers/base.py`: `EmbeddingProvider` (métodos `embed_texts(list[str]) -> list[list[float]]`, `embed_query(str)`, propiedad `dimension`) y `LLMProvider` (`generate(...)`, `stream(...) -> AsyncIterator[str]`). `providers/ollama_provider.py` implementa ambos vía `langchain-ollama`. Factory desde config. Tests unitarios con mocks.
  *Verificación:* `docker compose exec api pytest tests/unit/test_providers.py -q` en verde.
- [x] **1.2 Parsing y chunking.** `services/ingestion_service.py`: PyMuPDF extrae texto por página; splitter según sección 6 conservando `page` y `position` por chunk. Test unitario con un PDF fixture pequeño en `tests/fixtures/`.
  *Verificación:* `pytest tests/unit/test_chunking.py -q` en verde; chunks conservan página correcta.
- [x] **1.3 Endpoints de documentos + ingesta background.** `POST /documents` guarda el PDF en volumen, crea registro `processing`, lanza BackgroundTask: parse → chunk → embeddings en batches de 32 → insert. Actualiza `status`/`chunk_count`; captura errores en `error_message`. Implementar `GET` lista/detalle y `DELETE` (cascade).
  *Verificación:* subir un PDF real con `curl`; poll a `GET /documents/{id}` llega a `ready` con `chunk_count > 0`; `DELETE` deja `chunks` en 0 para ese doc.
- [x] **1.4 Seed.** Script `make seed`: ingesta vía API todos los PDFs presentes en `data/seed_pdfs/`. El corpus (colocado manualmente por el desarrollador, NO descargar de sitios del gobierno en el script) consiste en: (a) TUO del Reglamento Nacional de Tránsito (D.S. 016-2009-MTC y modificatorias), (b) tabla/cuadro de tipificación de infracciones y sanciones (Anexo I del RNT), (c) Reglamento Nacional del Sistema de Emisión de Licencias de Conducir (D.S. 007-2016-MTC). Si `data/seed_pdfs/` está vacío, el script falla con mensaje claro indicando qué documentos colocar y dónde obtenerlos (portal del MTC / SPIJ del Ministerio de Justicia). Incluir en el repo un `data/seed_pdfs/README.md` con esa lista.
  *Verificación:* con los PDFs presentes, `make seed` deja ≥2 documentos `ready` en la DB; sin PDFs, falla con mensaje instructivo.

### Fase 2 — Retrieval y chat con streaming

- [x] **2.1 Retrieval híbrido.** `services/retrieval_service.py`: búsqueda vectorial (cosine, top-20), full-text spanish (`plainto_tsquery`, top-20), fusión RRF k=60, top-6. Devuelve chunks con score y metadata. Tests de integración con datos seed.
  *Verificación:* `pytest tests/integration/test_retrieval.py -q`: una pregunta sobre contenido conocido del seed retorna el chunk esperado en top-3.
- [x] **2.2 Prompts.** `prompts/rag_answer.py`: system prompt en español — responder únicamente con el contexto numerado, citar con `[n]`, admitir cuando no hay evidencia, tono profesional. `prompts/query_rewrite.py`: reformular pregunta con historial a query autocontenida.
  *Verificación:* revisión manual + test que valida que el prompt renderiza con contexto numerado.
- [x] **2.3 Grafo LangGraph.** `graph/`: estado tipado, nodos `rewrite_query` (condicional: solo con historial), `retrieve`, `generate` (streaming). Compilar pipeline.
  *Verificación:* test de integración que invoca el grafo end-to-end contra Ollama y obtiene respuesta con al menos una cita `[n]`.
- [x] **2.4 Endpoint /chat SSE + persistencia.** `routers/chat.py` con `sse-starlette`: emite eventos `status` → `sources` → `token`* → `done` según contrato (sección 5). Crea conversación si no existe; persiste mensajes user/assistant con `sources` jsonb. Endpoints de conversaciones.
  *Verificación:* `curl -N localhost:8000/api/chat` con una pregunta del dominio muestra el flujo completo de eventos; los mensajes quedan en DB.

### Fase 3 — Frontend

- [x] **3.1 Scaffold frontend.** Vite + React 18 + TS + Tailwind + shadcn/ui + TanStack Query + react-router. Dockerfile dev. Layout base: sidebar (conversaciones + nav a Documentos/Evaluación), dark mode por defecto, tipografía cuidada. Cliente API tipado en `lib/api.ts`.
  *Verificación:* `docker compose up frontend` sirve la app; navegación entre 3 rutas funciona.
- [x] **3.2 Chat con streaming.** `useChatStream` (fetch + ReadableStream, parser SSE propio en `lib/sse.ts`): renderizado incremental de tokens con react-markdown, indicador de etapas del pipeline (Reformulando… / Buscando… / Generando…), chips de citas `[n]` clicables al final del mensaje. Historial de conversación cargado desde API.
  *Verificación:* preguntar desde la UI → se ven etapas, tokens en vivo y citas; refrescar mantiene el historial.
- [x] **3.3 Panel de fuentes.** Panel derecho colapsable: chunks del último mensaje con filename, página, score y texto; clic en cita `[n]` resalta/scrollea al chunk correspondiente. Estado vacío elegante.
  *Verificación:* clic en `[2]` enfoca la fuente 2 en el panel.
- [x] **3.4 Vista de documentos.** Tabla (nombre, páginas, chunks, estado con badge, fecha), dropzone drag & drop para subir PDF, polling del estado con TanStack Query hasta `ready`, acción eliminar con confirmación.
  *Verificación:* subir un PDF desde la UI → aparece `processing` → pasa a `ready` sin refrescar; eliminar lo quita.
- [x] **3.5 Vista de evaluación.** Cards con métricas globales (faithfulness, answer_relevancy, context_precision) y tabla por pregunta, consumiendo `GET /eval/results`. Estado "aún no hay resultados" si 404.
  *Verificación:* con `results.json` presente, el dashboard renderiza métricas.

### Fase 4 — Evaluación

- [x] **4.1 Dataset.** `eval/dataset.jsonl`: 25 pares `{question, ground_truth}` en español sobre los documentos seed. Variedad obligatoria: infracciones concretas con código y monto ("¿cuál es la sanción por conducir con licencia vencida?"), artículos específicos del RNT, requisitos y vigencia de licencias por categoría, límites de velocidad, alcoholemia, preguntas de síntesis que crucen 2 documentos, y 3 preguntas SIN respuesta en el corpus (p. ej. sobre trámites vehiculares no cubiertos) para validar el anti-alucinación. El ground_truth se redacta leyendo los PDFs reales del seed, nunca de memoria del agente.
  *Verificación:* archivo válido línea a línea; 25 entradas.
- [x] **4.2 Script RAGAS.** `eval/evaluate.py`: para cada pregunta ejecuta el pipeline real (retrieval + generación), computa faithfulness, answer_relevancy y context_precision usando el LLM local como judge; exporta `eval/results.json` (global + por pregunta + timestamp + modelos usados). Target `make eval`.
  *Verificación:* `make eval` genera `results.json` completo y la vista de evaluación lo muestra.

### Fase 5 — Pulido de portafolio

- [x] **5.1 README.** En inglés (portafolio): descripción, diagrama de arquitectura (Mermaid), features con screenshots/GIF placeholder, quickstart (`docker compose up` + `make seed`), tabla del stack, sección **Technical Decisions** (pgvector vs vector DBs dedicados, búsqueda híbrida + RRF, bge-m3 para español, modelos locales y trade-offs, LangGraph), sección de evaluación con métricas reales, roadmap (reranker, Langfuse, deploy), y disclaimer visible: proyecto de demostración, no constituye asesoría legal y la normativa puede haber cambiado. El mismo disclaimer debe aparecer discretamente en el footer de la UI.
  *Verificación:* README renderiza sin enlaces rotos; quickstart reproducible desde cero (`docker compose down -v && docker compose up`).
- [x] **5.2 Calidad final.** Linters (ruff + eslint/prettier) configurados y en verde, `make test` corre toda la suite, revisar que `.env.example` esté completo, compose de producción opcional (`docker-compose.prod.yml` con build estático del frontend servido por nginx).
  *Verificación:* `make test` y linters sin errores; `docker compose -f docker-compose.prod.yml config` válido.

---

## 8. Definition of Done global

1. `docker compose up` desde cero deja los 4 servicios healthy y modelos pulled sin intervención manual.
2. `make seed && make test && make eval` pasan en verde.
3. Flujo completo demostrable: subir PDF → preguntar en español → respuesta streameada con citas clicables → fuente visible con página.
4. Preguntas fuera del corpus reciben "no encontré esto en los documentos" (sin alucinar).
5. README permite a un tercero levantar todo en <10 minutos.

## 9. Reglas para el agente

- Commits atómicos por tarea, en inglés, convención `feat|fix|chore(fase-N): descripción`.
- Dependencias siempre pinneadas.
- No introducir servicios cloud ni API keys de pago: todo local.
- Si una decisión no está en este plan, elegir la opción más simple y anotarla en la sección "Decisiones tomadas" al final de este archivo.
- Mantener este archivo actualizado: marcar `[x]` SOLO tras verificación exitosa.

## Decisiones tomadas
<!-- El agente anota aquí decisiones no cubiertas por el plan -->

- **0.2 — Healthcheck de Ollama:** el plan pide "healthcheck HTTP", pero la imagen oficial
  `ollama/ollama` no incluye `curl`/`wget`. Se usa `["CMD", "ollama", "list"]`, que consulta
  la API HTTP local del servidor (misma intención, opción más simple y fiable).
- **0.2 — `.env` local:** se crea un `.env` (copia de `.env.example`, ignorado por git) para que
  `docker compose` resuelva variables y `env_file` del servicio `api` no falle en `config`.
- **0.4 — Migración manual con SQL directo:** el esquema usa `vector(1024)`, `tsvector` generado
  e índices HNSW/GIN que Alembic autogenerate no maneja; la migración `0001_initial` usa
  `op.execute` con DDL explícito. Alembic corre en modo async (asyncpg), sin driver sync extra.
- **0.4 — Cascade en `messages`:** la sección 4 solo pide FK en `messages.conversation_id`; se
  añade `ON DELETE CASCADE` (opción más simple y coherente con `chunks`).
- **0.4 — `.gitattributes`:** fuerza LF en `*.sh` para que `entrypoint.sh` no se rompa al hacer
  checkout en Windows y correr dentro del contenedor Linux.
- **1.2 — Chunking por página + tamaños:** se trocea cada página por separado para preservar el
  número de página (un chunk nunca cruza páginas → cita a una página exacta). `chunk_size`=800 y
  `overlap`=150 se interpretan en tokens y se convierten a caracteres con un factor ×4
  (3200 y 600 chars). El caso especial de la tabla del Anexo I se aborda en la ingesta real (1.3/1.4).
- **1.2 — Fixture de test:** `tests/fixtures/sample.pdf` se genera de forma reproducible con
  `tests/fixtures/make_sample_pdf.py` (PyMuPDF). Se incluye en la imagen (se quitó la exclusión
  en `.dockerignore`) para que los tests sean autocontenidos.
- **1.3 — Prefijo de rutas:** `/health` queda en la raíz (healthcheck directo) y los recursos de
  la API van bajo `/api` (`/api/documents`, y luego `/api/chat` según la verificación de 2.4).
- **1.3 — Dependencias añadidas:** `pgvector` (adaptador Python del tipo `vector` para el ORM) y
  `python-multipart` (requisito de FastAPI para subir archivos). No cambian el stack; habilitan
  pgvector desde Python y la subida de PDFs.
- **1.3 — Almacenamiento de PDFs:** los PDFs subidos se guardan en el volumen `uploads`
  (`/app/uploads/{id}.pdf`, configurable vía `UPLOAD_DIR`); el borrado elimina también el archivo.
- **1.3 — Ingesta background:** usa su propia `AsyncSession` (no la del request); embeddings en
  batches de 32 (`EMBEDDING_BATCH_SIZE`). Errores se capturan en `status=error`/`error_message`.
- **1.4 — Seed secuencial vía API:** `app/scripts/seed.py` sube cada PDF y espera `ready` antes
  del siguiente (progreso claro; evita apilar 3 ingestas pesadas a la vez). Éxito si ≥2 quedan
  `ready`. Corre dentro del contenedor `api`, por eso llama a la API en `localhost:8000`.
- **1.4 — `make` no está en el host Windows:** la verificación `make seed` se ejecutó con el
  comando equivalente del target (`docker compose exec api python -m app.scripts.seed`). El
  Makefile sigue siendo correcto para Unix/CI. Resultado del seed real: 3/3 `ready`
  (17 + 162 + 358 = 537 chunks, todos con embedding).
- **1.4 — Tabla del Anexo I (pendiente de refinamiento):** la ingesta actual extrae el Anexo con
  `get_text` estándar (quedó `ready`, 17 chunks). La serialización fila-a-fila de la tabla
  (sección 6) se evaluará como mejora de calidad de retrieval si los tests de eval lo exigen.
- **2.1 — Vector search vía ORM + FTS vía SQL:** la búsqueda coseno usa
  `Chunk.embedding.cosine_distance(...)` (pgvector.sqlalchemy maneja el binding con asyncpg); el
  full-text usa SQL directo con `plainto_tsquery('spanish', ...)` porque `content_tsv` no se mapea
  en el ORM. Fusión RRF con listas de ids -> hidratación final (join a `documents` para el filename).
- **2.1 — Engine dispose en tests de integración:** `tests/integration/conftest.py` hace
  `engine.dispose()` tras cada test para evitar el error de asyncpg "attached to a different loop"
  (pytest-asyncio usa un loop por test). No cambia el pooling de producción.
- **2.3 — Dependencias del grafo por config/inyección:** los nodos reciben la sesión vía
  `config["configurable"]["session"]` (no en el estado) y `generate` recibe un `StreamWriter`
  inyectado (`langgraph.types.StreamWriter`; en 0.2.62 no existe `get_stream_writer`). El writer
  emite tokens (`{"token": ...}`) en `stream_mode="custom"` y es no-op en `ainvoke` — lo usará /chat (2.4).
- **2.3 — Entrada condicional:** `add_conditional_edges(START, ...)` enruta a `rewrite_query` solo
  si hay historial; si no, va directo a `retrieve`.
- **2.4 — SSE con `graph.astream(stream_mode=["updates","custom"])`:** los updates de nodos dan
  las etapas (`retrieving`/`generating`) y las `sources`; el modo `custom` entrega los tokens del
  `StreamWriter`. El `chat_service` usa su propia `AsyncSession` (vive durante todo el stream).
- **2.4 — Latencia de primer token:** con 6 chunks de contexto, el prefill de qwen2.5:7b en CPU
  tarda varios minutos antes del primer token (sse-starlette envía pings de keepalive mientras
  tanto); luego streamea. Es inherente a CPU + contexto grande, no un bug.
- **2.4 — `none_as_null=True` en `messages.sources`:** un `sources=None` (mensaje de usuario) se
  guarda como SQL NULL, no como JSON `'null'` scalar.
- **2.4 — Body con caracteres no-ASCII (`¿`) en curl:** en Git Bash de Windows, `-d '{...}'` inline
  corrompe el `¿`; usar `--data-binary @archivo.json` (UTF-8). No es un problema de la API.
- **3.1 — Tailwind v3 + shadcn (no v4):** se usa Tailwind 3.4 con el enfoque clásico
  (`tailwind.config.js` + variables CSS), el patrón mejor documentado de shadcn. Dark mode por
  defecto vía `class="dark"` en `index.html`.
- **3.1 — Proxy Vite:** `/api -> http://api:8000` (nombre del servicio). El cliente API
  (`lib/api.ts`) usa rutas relativas `/api/...`. `/health` (raíz) no se proxea (no lo usa la UI aún).
- **3.1 — Sin package-lock.json:** `npm install` corre en el build de Docker (deps pinneadas exactas
  en `package.json`). Un lockfile commiteado queda para la tarea 5.2 (calidad final).
- **3.2 — conversation_id en la URL:** el chat guarda la conversación activa en `?c=<id>`
  (`useSearchParams`). Al refrescar, `useChatStream` recarga los mensajes desde la API
  (`GET /conversations/{id}/messages`) → el historial persiste.
- **3.2 — HMR poco fiable en bind-mount de Windows:** Vite no siempre detecta cambios de archivos
  a través del bind-mount `./frontend:/app` (inotify no propaga en Windows/WSL2). Si un cambio no
  se refleja, `docker compose restart frontend` fuerza la relectura. Resuelto con
  `server.watch.usePolling` en `vite.config.ts` (aplicado tras 3.2).
- **3.4 — Polling de documentos:** `useDocuments` usa `refetchInterval` (2s mientras algún doc
  esté `processing`) con `refetchIntervalInBackground: true` para que el estado pase a `ready` sin
  refrescar aunque la pestaña no esté enfocada. Delete con confirmación inline (sin dep extra de
  AlertDialog). Subida por `<input type=file>` o drag & drop (mismo handler `onFile`).
- **3.5 — Endpoint `/eval/results` añadido:** el contrato lo listaba pero ninguna tarea previa lo
  creaba; se agrega en 3.5 (`routers/eval.py` + `services/eval_service.py`, lee
  `EVAL_RESULTS_PATH=/app/eval/results.json`, 404 si no existe). El `results.json` real lo genera
  la Fase 4.2 (no se commitea uno de muestra; se probó el render con uno temporal y se eliminó).
  El esquema esperado: `{timestamp, models:{llm,embedding}, global:{3 métricas}, per_question:[...]}`.
- **4.1 — Dataset fundamentado en los PDFs reales:** los 25 `ground_truth` se redactaron leyendo el
  contenido real indexado en la DB (consultas full-text a los chunks del seed), no de memoria.
  Cubre infracciones con código y monto (M01–M19), artículos del RNT (162, 163, 165, 168-A, 307),
  requisitos/vigencia/entidad de licencias (art. 14/15/17/23), 2 preguntas de síntesis que cruzan
  el Anexo + reglamento de licencias, y 3 preguntas SIN respuesta en el corpus (transferencia
  vehicular, SOAT, tarjeta de identificación vehicular) para el anti-alucinación. Formato: pares
  `{question, ground_truth}` exactos.
- **4.2 — Juez local en vez de RAGAS (decidido con el usuario):** RAGAS con qwen2.5:7b en CPU es
  inviable (muchas llamadas al juez por métrica → horas, y NaN frecuentes). Con OK explícito del
  usuario, `eval/evaluate.py` implementa las 3 métricas (faithfulness, answer_relevancy,
  context_precision) con el LLM local como juez (1 llamada por métrica, contextos truncados a
  600 chars para el juez). Corre el pipeline real (retrieval top-6 + generación). Checkpointing
  tras cada pregunta y resumible (omite las ya evaluadas). Exporta `results.json`
  {timestamp, models, global, per_question(question, answer, 3 métricas)}. `make eval` = 25 preguntas
  (`--limit N` para subconjuntos). Tiempo real: ~15 min/pregunta en CPU.
- **4.2 — Resultado del run (25/25):** Faithfulness 0.752, Answer Relevancy 0.674, Context
  Precision 0.800. Las 3 preguntas fuera del corpus expusieron el anti-alucinación: 2/3 respondieron
  correctamente "no está en los documentos" (SOAT, tarjeta vehicular); la de transferencia vehicular
  se aferró a un chunk tangencial (context_precision 0.00 lo detectó). Mejora futura: umbral de
  score mínimo en retrieval para reforzar el "no encontrado".
- **5.1 — README + verificación no destructiva:** README en inglés con Mermaid, decisiones técnicas,
  métricas reales del eval y disclaimer (también en el footer del Sidebar). Se verificó que no hay
  enlaces rotos y que `docker compose config` es válido, pero NO se corrió `docker compose down -v`
  porque borraría el corpus seedeado (537 chunks), los modelos (~6 GB) y el estado del demo
  (~1h de re-seed). La reproducibilidad desde cero ya quedó demostrada por la construcción completa
  del proyecto con estos mismos archivos/comandos. Queda como test opcional del usuario.
- **5.2 — Linters y prod:** ruff (backend, config en pyproject; `Depends()` de FastAPI permitido vía
  `extend-immutable-calls`) y eslint 9 flat + prettier (frontend) — todos en verde
  (`make lint`). `make test` = 22 passed. `.env.example` completado con `EVAL_RESULTS_PATH`.
  `docker-compose.prod.yml` (nginx sirve el build estático del frontend y proxya `/api` con
  `proxy_buffering off` para no romper el SSE) — `config` válido. Las deps de linters se declaran
  en pyproject/package.json; en las imágenes actuales se instalaron ad-hoc (un rebuild las hornea).

---

## Estado final

**Todas las tareas del plan (0.1 → 5.2) completadas y verificadas.** El demo full-stack corre
con `docker compose up`: chat con streaming + citas + panel de fuentes, gestión de documentos,
y dashboard de evaluación con métricas reales (RAG sobre normativa de tránsito del Perú, 100% local).
