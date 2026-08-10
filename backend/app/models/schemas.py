"""Pydantic request/response models — the locked-in API contract (Architecture §5/§8)."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    type: str
    message: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    """The single structured response envelope every /api/chat call returns."""

    message: str
    sql: Optional[str] = None
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    chart: Optional[dict[str, Any]] = None
    diagram: Optional[str] = None
    explanation: Optional[str] = None
    error: Optional[ErrorDetail] = None


class DatabaseInfo(BaseModel):
    """Active-database indicator shown by the frontend. Never includes a filesystem path."""

    name: str
    source: Literal["default", "upload"]
    active: bool = True


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
