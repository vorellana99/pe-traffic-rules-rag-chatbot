"""Schemas Pydantic para documentos."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    title: str | None
    pages: int | None
    status: str
    error_message: str | None
    chunk_count: int
    created_at: datetime


class DocumentCreated(BaseModel):
    id: uuid.UUID
    status: str
