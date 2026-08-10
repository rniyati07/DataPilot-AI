"""Database-management endpoints (TRD §3, Architecture data-flow §3).

Wired directly to the real Database Manager — validation, controlled
storage, and session-scoped active-database resolution (Phase 3).
"""
from fastapi import APIRouter, Header, HTTPException, UploadFile

from app.db import database_manager
from app.models.schemas import DatabaseInfo
from app.session.store import resolve_session_id

router = APIRouter()


@router.post("/database/upload", response_model=DatabaseInfo)
async def upload_database(
    file: UploadFile,
    x_session_id: str | None = Header(default=None),
) -> DatabaseInfo:
    session_id = resolve_session_id(x_session_id)
    content = await file.read()

    try:
        display_name = database_manager.register_database(
            session_id, file.filename or "", content
        )
    except database_manager.UploadValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"type": "invalid_upload", "message": str(exc)},
        ) from exc

    return DatabaseInfo(name=display_name, source="upload", active=True)


@router.get("/database/current", response_model=DatabaseInfo)
def current_database(x_session_id: str | None = Header(default=None)) -> DatabaseInfo:
    session_id = resolve_session_id(x_session_id)
    name, source = database_manager.get_active_database_info(session_id)
    return DatabaseInfo(name=name, source=source, active=True)


@router.delete("/database/current", response_model=DatabaseInfo)
def clear_database(x_session_id: str | None = Header(default=None)) -> DatabaseInfo:
    session_id = resolve_session_id(x_session_id)
    database_manager.clear_active_database(session_id)
    name, source = database_manager.get_active_database_info(session_id)
    return DatabaseInfo(name=name, source=source, active=True)
