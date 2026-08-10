"""GET /api/schema — stub for Batch 1.

The real dynamic schema-discovery contract (Tool 1 in 04_AGENT_TOOLS.md) is
implemented in Phase 4. Returning a placeholder here rather than an empty
`tables: []` payload avoids implying "this database has no tables."
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/schema")
def get_schema_stub() -> dict:
    return {
        "status": "not_implemented",
        "message": "Schema introspection will be available in Batch 2 (Phase 4).",
    }
