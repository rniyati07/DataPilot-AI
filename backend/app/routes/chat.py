"""POST /api/chat — routes a user message through the LangChain agent.

The route stays thin (Architecture §9): it resolves the session, delegates
to the Agent Service, and returns the response envelope unchanged.
"""
import anyio
from fastapi import APIRouter, Header

from app.agent import agent_service
from app.models.schemas import ChatRequest, ChatResponse
from app.session.store import resolve_session_id

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, x_session_id: str | None = Header(default=None)
) -> ChatResponse:
    session_id = resolve_session_id(x_session_id)
    # The agent call is blocking (provider HTTP + SQLite I/O); run it in a
    # worker thread so one slow turn does not block the event loop (TRD §3).
    return await anyio.to_thread.run_sync(agent_service.run_agent, session_id, request.message)
