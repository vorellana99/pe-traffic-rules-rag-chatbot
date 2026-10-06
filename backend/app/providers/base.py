"""Interfaces de proveedores de embeddings y LLM.

La implementación concreta (Ollama) vive en `ollama_provider.py`. El resto de
la app depende solo de estas abstracciones. La dimensión del embedding se lee
del provider (`dimension`), nunca se hardcodea fuera de él.
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensión de los vectores de embedding."""

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embeddings para una lista de textos (ingesta en batch)."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embedding para una consulta individual."""


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Genera una respuesta completa (no streaming)."""

    @abstractmethod
    def stream(
        self, prompt: str, *, system: str | None = None
    ) -> AsyncIterator[str]:
        """Genera la respuesta como stream de tokens (fragmentos de texto)."""
