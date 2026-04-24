"""
Pipeline route — HTTP endpoint to trigger the full equity research pipeline.
============================================================================

POST /api/pipeline  {"ticker": "AAPL"}
    → Runs all 5 engines through the orchestrator
    → Returns the complete data bus (context) as JSON
"""

import concurrent.futures

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.pipeline.orchestrator import run_pipeline
from backend.engines import DEFAULT_ENGINES
from backend.db.supabase_client import save_research_result

router = APIRouter()

_PIPELINE_TIMEOUT_S = 90  # hard wall-clock limit per request


class PipelineRequest(BaseModel):
    ticker: str
    session_id: str | None = None
    user_id: str | None = None
    financial_override: dict | None = None  # parsed Excel data; Engine 1 checks this first


@router.post("/pipeline")
def run_pipeline_endpoint(request: PipelineRequest) -> dict:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run_pipeline, request.ticker, DEFAULT_ENGINES)
        try:
            result = future.result(timeout=_PIPELINE_TIMEOUT_S)
        except concurrent.futures.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=f"Pipeline timed out after {_PIPELINE_TIMEOUT_S}s — one or more engines hung. Try again.",
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    if request.session_id and request.user_id:
        try:
            save_research_result(request.session_id, request.user_id, request.ticker, result)
        except Exception:
            pass  # never fail the response because of a DB write

    return result
