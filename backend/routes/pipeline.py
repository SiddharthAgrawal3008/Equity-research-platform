"""
Pipeline route — HTTP endpoint to trigger the full equity research pipeline.
============================================================================

POST /api/pipeline  {"ticker": "AAPL"}
    → Runs all 5 engines through the orchestrator
    → Returns the complete data bus (context) as JSON
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.pipeline.orchestrator import run_pipeline
from backend.engines import DEFAULT_ENGINES
from backend.db.supabase_client import save_research_result

router = APIRouter()


class PipelineRequest(BaseModel):
    ticker: str
    session_id: str | None = None
    user_id: str | None = None


@router.post("/pipeline")
def run_pipeline_endpoint(request: PipelineRequest) -> dict:
    try:
        result = run_pipeline(request.ticker, engines=DEFAULT_ENGINES)

        if request.session_id and request.user_id:
            try:
                save_research_result(request.session_id, request.user_id, request.ticker, result)
            except Exception:
                pass  # never fail the response because of a DB write

        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
