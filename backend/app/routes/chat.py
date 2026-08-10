"""POST /api/chat — Batch 1 returns a canned, correctly-shaped response.

The real LangChain agent is wired in here in Batch 2 (Phase 6). This route
exists now to lock in the response envelope contract early.
"""
from fastapi import APIRouter, Header

from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, x_session_id: str | None = Header(default=None)) -> ChatResponse:
    return ChatResponse(
        message="Chat agent will be connected in Batch 2.",
        sql=None,
        columns=[],
        rows=[],
        chart=None,
        diagram=None,
        explanation=None,
        error=None,
    )
