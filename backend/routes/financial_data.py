"""
Route handler for Engine 1 — Financial Data Engine.

Exposes fetch_raw() over HTTP so the frontend and other engines
can request raw financial data for any ticker.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.engines.engine_1.financial_data import (
    fetch_raw,
    TickerNotFoundError,
    CompanyDataUnavailableError,
    DataFetchError,
)

router = APIRouter()


class FinancialDataRequest(BaseModel):
    ticker: str


@router.post("/financial-data")
def get_financial_data(request: FinancialDataRequest) -> dict:
    """
    Pull raw financial data for a ticker via Engine 1.

    Request body:
        { "ticker": "AAPL" }

    Returns:
        Raw Contract-A dict with income statement, balance sheet,
        cash flow, market data, and company info.

    HTTP errors:
        404 — ticker not found or company has no public data
        503 — Yahoo Finance unreachable (rate limit / network block)
        500 — unexpected internal error
    """
    try:
        return fetch_raw(request.ticker)
    except TickerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except CompanyDataUnavailableError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DataFetchError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
