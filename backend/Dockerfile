FROM python:3.12-slim

# uv como instalador de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Instala dependencias (capa cacheada) — se instalan en el Python del sistema,
# fuera de /app, para no ser ocultadas por el bind-mount de código en dev.
COPY pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

# Código de la app (en dev queda sobrescrito por el volumen ./backend:/app)
COPY . .

EXPOSE 8000

# El entrypoint aplica migraciones (alembic upgrade head) y luego ejecuta el CMD.
# Se invoca con `sh` para no depender del bit de ejecución (checkout en Windows).
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
