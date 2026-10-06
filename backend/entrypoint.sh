#!/bin/sh
set -e

echo "[entrypoint] Aplicando migraciones (alembic upgrade head)..."
alembic upgrade head

echo "[entrypoint] Iniciando: $@"
exec "$@"
