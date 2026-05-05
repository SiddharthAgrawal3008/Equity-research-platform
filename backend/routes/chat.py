import concurrent.futures
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.chat import chat

logger = logging.getLogger(__name__)
router = APIRouter()

_CHAT_TIMEOUT_S = 120  # pipeline (90s max) + LLM calls (30s buffer)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    tool_used: str | None = None
    ticker_analyzed: str | None = None
    has_analysis: bool = False


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    history = [{"role": m.role, "content": m.content} for m in request.history]

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(chat, request.message, history)
        try:
            result = future.result(timeout=_CHAT_TIMEOUT_S)
        except concurrent.futures.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=f"Chat timed out after {_CHAT_TIMEOUT_S}s",
            )
        except Exception as exc:
            logger.exception("Chat endpoint failed")
            raise HTTPException(status_code=500, detail=str(exc))

    return ChatResponse(
        reply=result["reply"],
        tool_used=result.get("tool_used"),
        ticker_analyzed=result.get("ticker_analyzed"),
        has_analysis=result.get("analysis_data") is not None,
    )
