.PHONY: up down logs test eval seed lint

# Levanta todos los servicios en segundo plano
up:
	docker compose up -d --build

# Detiene y elimina los contenedores
down:
	docker compose down

# Sigue los logs de todos los servicios
logs:
	docker compose logs -f

# Corre la suite de tests dentro del contenedor api
test:
	docker compose exec api pytest -q

# Ejecuta la evaluación RAGAS (genera eval/results.json)
eval:
	docker compose exec api python -m eval.evaluate

# Ingesta los PDFs presentes en data/seed_pdfs/ vía la API
seed:
	docker compose exec api python -m app.scripts.seed

# Linters: ruff (backend) + eslint/prettier (frontend)
lint:
	docker compose exec api ruff check .
	docker compose exec frontend sh -c "npx eslint . && npx prettier --check ."
