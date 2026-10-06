"""Configuración centralizada (pydantic-settings).

Única fuente de configuración de la app. Nada de `os.getenv` disperso: todo
lee de aquí. Los valores vienen de variables de entorno (ver `.env.example`).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Base de datos
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/transito_rag"

    # Ollama (LLM + embeddings)
    ollama_base_url: str = "http://ollama:11434"
    llm_model: str = "qwen2.5:7b"
    embedding_model: str = "bge-m3"
    embedding_dim: int = 1024

    # CORS: lista separada por comas en la env var CORS_ORIGINS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Directorio (en volumen) donde se guardan los PDFs subidos
    upload_dir: str = "/app/uploads"

    # Tamaño de batch para calcular embeddings durante la ingesta
    embedding_batch_size: int = 32

    # Ruta del JSON de resultados de evaluación (lo genera `make eval`)
    eval_results_path: str = "/app/eval/results.json"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Instancia única de Settings (cacheada)."""
    return Settings()
