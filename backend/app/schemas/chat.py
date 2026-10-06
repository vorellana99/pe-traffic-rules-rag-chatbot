"""Schemas de chat y conversaciones."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID | None = None
    message: str


class SourceOut(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page: int | None
    content: str
    score: float


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    sources: list[SourceOut] | None = None
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    created_at: datetime
