"""
Route handler for the Financial Analysis endpoint.

Connects the HTTP layer to Engine 2 (financial_analysis).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.engines import financial_analysis
from backend.engines.mock_data import MOCK_RAW_FINANCIALS

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request body for the analysis endpoint."""
    ticker: str


@router.post("/analysis")
def run_analysis(request: AnalysisRequest) -> dict:
    """Run Engine 2 on the given ticker and return analysis metrics.

    Args:
        request: JSON body with a ``ticker`` field.

    Returns:
        The Contract-B analysis_metrics dict.
    """
    try:
        # TODO: replace mock data with Engine 1 call once available
        raw_financials = MOCK_RAW_FINANCIALS
        result = financial_analysis.run(raw_financials)
        return result
    except financial_analysis.DataContractError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
