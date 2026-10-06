"""Fixtures para tests de integración.

pytest-asyncio crea un event loop nuevo por test; el engine async global mantiene
conexiones asyncpg atadas al loop en que se crearon. Desechar el engine tras cada
test fuerza conexiones frescas en el loop correcto (evita el error
"attached to a different loop") sin cambiar el pooling de producción.
"""
import pytest

from app.core.db import engine


@pytest.fixture(autouse=True)
async def _dispose_db_engine():
    yield
    await engine.dispose()
