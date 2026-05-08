"""
Pipeline route — HTTP endpoint to trigger the full equity research pipeline.
============================================================================

POST /api/pipeline  {"ticker": "AAPL"}
    → Runs all 5 engines through the orchestrator
    → Returns the complete data bus (context) as JSON
"""

import threading

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
    result_box: dict = {}
    error_box:  dict = {}
    done = threading.Event()

    def _run() -> None:
        try:
            result_box["v"] = run_pipeline(request.ticker, DEFAULT_ENGINES)
        except Exception as exc:  # noqa: BLE001
            error_box["v"] = exc
        finally:
            done.set()

    # Daemon thread: if we return before it finishes it won't block the process.
    t = threading.Thread(target=_run, daemon=True)
    t.start()

    if not done.wait(timeout=_PIPELINE_TIMEOUT_S):
        raise HTTPException(
            status_code=504,
            detail=(
                f"Pipeline timed out after {_PIPELINE_TIMEOUT_S}s — "
                "an engine is stalling on an external API call. Try again."
            ),
        )

    if "v" in error_box:
        raise HTTPException(status_code=500, detail=str(error_box["v"]))

    result = result_box["v"]

    if request.session_id and request.user_id:
        try:
            save_research_result(request.session_id, request.user_id, request.ticker, result)
        except Exception:
            pass  # never fail the response because of a DB write

    return result
