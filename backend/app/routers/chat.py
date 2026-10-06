"""Router de chat con streaming SSE."""
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.schemas.chat import ChatRequest
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest) -> EventSourceResponse:
    return EventSourceResponse(
        chat_service.stream_chat(request.conversation_id, request.message)
    )
