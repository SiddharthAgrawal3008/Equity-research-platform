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

router = APIRouter()


class PipelineRequest(BaseModel):
    """Request body for the pipeline endpoint."""
    ticker: str


@router.post("/pipeline")
def run_pipeline_endpoint(request: PipelineRequest) -> dict:
    """Execute the full 5-engine equity research pipeline.

    Args:
        request: JSON body with a ``ticker`` field.

    Returns:
        The complete data bus dict with all engine outputs,
        status tracking, error log, and pipeline metadata.
    """
    try:
        result = run_pipeline(request.ticker, engines=DEFAULT_ENGINES)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
