"""
Engine 1 — Financial Data Engine (Step 1: Raw Data Pull)
=========================================================

RESPONSIBILITY:
    Pull ALL raw financial data from FMP (Financial Modeling Prep) for a
    given ticker. Nothing is renamed, mapped, or filtered here. Every field
    FMP returns is preserved so the standardization layer (Step 2) has the
    full picture to work with.

WHAT THIS MODULE DOES NOT DO:
    - Does not rename fields to match Contract A schema  (that's Step 2)
    - Does not validate array lengths or None values     (that's Step 3)
    - Does not compute TTM                               (that's Step 4)
    - Does not compute derived metrics like EBITDA       (that's Step 2)

ERRORS THIS MODULE RAISES:
    TickerNotFoundError         — symbol does not exist on any exchange
    CompanyDataUnavailableError — company exists but has no public financial data
                                  (private company, OTC-only, or pre-revenue startup)
    DataFetchError              — network/upstream failure (timeout, connection error, etc.)

ENVIRONMENT VARIABLES:
    FMP_API_KEY — Financial Modeling Prep API key (required).
                  Add to your .env file: FMP_API_KEY=your_key_here
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

FMP_BASE_URL = "https://financialmodelingprep.com/stable"


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class TickerNotFoundError(Exception):
    """
    Raised when the ticker symbol does not exist on any exchange.

    Frontend message: "Ticker '<symbol>' not found.
    Please check the symbol and try again."
    """


class CompanyDataUnavailableError(Exception):
    """
    Raised when the company exists but financial statements are not
    publicly available.

    Common reasons:
      - Private company (not listed on a public exchange)
      - OTC-only listing with no reported financials
      - Very recently listed company with no annual filings yet

    Frontend message: "<Company Name> does not have publicly
    available financial statements. This platform covers publicly
    listed companies with at least one year of filed financials."
    """


class DataFetchError(Exception):
    """
    Raised when a network or upstream API failure prevents data retrieval.
    This is distinct from an invalid ticker — the symbol may be valid but
    FMP is unreachable (timeout, rate limit, connection error, etc.).

    Frontend message: "Unable to fetch data right now. Please try again
    in a moment."
    """


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """
    Read the FMP API key from the environment.

    Raises:
        DataFetchError: If FMP_API_KEY is not set.
    """
    key = os.environ.get("FMP_API_KEY", "").strip()
    if not key:
        raise DataFetchError(
            "FMP_API_KEY environment variable is not set. "
            "Please add it to your .env file."
        )
    return key


def _fmp_get(endpoint: str, api_key: str, params: dict[str, Any] | None = None) -> Any:
    """
    Make a GET request to an FMP endpoint and return the parsed JSON response.

    Args:
        endpoint: Path relative to FMP_BASE_URL, e.g. "/profile/AAPL"
        api_key:  FMP API key.
        params:   Optional extra query parameters (apikey is added automatically).

    Returns:
        Parsed JSON response (list or dict depending on endpoint).

    Raises:
        DataFetchError: On any HTTP error, timeout, or connection failure.
    """
    url = f"{FMP_BASE_URL}{endpoint}"
    query_params: dict[str, Any] = {"apikey": api_key}
    if params:
        query_params.update(params)

    try:
        response = requests.get(url, params=query_params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as exc:
        raise DataFetchError(
            f"Request to FMP timed out for endpoint '{endpoint}'. "
            "Please try again."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise DataFetchError(
            f"Could not connect to Financial Modeling Prep: {exc}"
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise DataFetchError(
            f"FMP returned HTTP {exc.response.status_code} for '{endpoint}': {exc}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise DataFetchError(
            f"Unexpected error fetching '{endpoint}' from FMP: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Main Entry Point for Step 1
# ---------------------------------------------------------------------------

def fetch_raw(ticker_symbol: str) -> dict:
    """
    Pull ALL raw financial data for a ticker from FMP.

    This is the only public function in this module.
    It is called by the orchestrating run() function (built in later steps).

    Endpoints called:
        GET /profile/{ticker}
        GET /income-statement/{ticker}?period=annual&limit=10
        GET /balance-sheet-statement/{ticker}?period=annual&limit=10
        GET /cash-flow-statement/{ticker}?period=annual&limit=10
        GET /income-statement/{ticker}?period=quarter&limit=6
        GET /cash-flow-statement/{ticker}?period=quarter&limit=6

    Args:
        ticker_symbol: Stock ticker string, e.g. "AAPL" or "INFY.NS".
                       Case-insensitive — will be uppercased internally.

    Returns:
        A raw dict with these top-level keys:

        profile            — list with one profile dict from FMP /profile
        annual_income      — list of annual income statement dicts (newest first)
        annual_balance     — list of annual balance sheet dicts (newest first)
        annual_cashflow    — list of annual cash flow dicts (newest first)
        quarterly_income   — list of last 6 quarterly income statement dicts
        quarterly_cashflow — list of last 6 quarterly cash flow dicts

    Raises:
        TickerNotFoundError:         /profile returns an empty list.
        CompanyDataUnavailableError: Profile exists but all financial statements empty.
        DataFetchError:              HTTP error, timeout, or connection failure.
    """
    symbol = ticker_symbol.strip().upper()
    logger.info("Engine 1 | fetch_raw | starting pull for '%s'", symbol)

    api_key = _get_api_key()

    # ── 1. Profile ──────────────────────────────────────────────────────────
    profile = _fmp_get(f"/profile/{symbol}", api_key)

    if not profile:
        raise TickerNotFoundError(
            f"Ticker '{symbol}' not found. "
            "Please check the symbol and try again."
        )

    # ── 2. Annual financial statements ──────────────────────────────────────
    annual_income = _fmp_get(
        f"/income-statement/{symbol}", api_key,
        params={"period": "annual", "limit": 10},
    )
    annual_balance = _fmp_get(
        f"/balance-sheet-statement/{symbol}", api_key,
        params={"period": "annual", "limit": 10},
    )
    annual_cashflow = _fmp_get(
        f"/cash-flow-statement/{symbol}", api_key,
        params={"period": "annual", "limit": 10},
    )

    # ── 3. Check financial data availability ────────────────────────────────
    # Profile exists but no statements → private company or pre-revenue startup
    if not annual_income and not annual_balance and not annual_cashflow:
        company_name = profile[0].get("companyName", symbol)
        raise CompanyDataUnavailableError(
            f"'{company_name}' does not have publicly available financial "
            "statements. This platform currently covers publicly listed "
            "companies with at least one year of filed annual financials."
        )

    # ── 4. Quarterly statements (for TTM computation in Step 4) ─────────────
    quarterly_income = _fmp_get(
        f"/income-statement/{symbol}", api_key,
        params={"period": "quarter", "limit": 6},
    )
    quarterly_cashflow = _fmp_get(
        f"/cash-flow-statement/{symbol}", api_key,
        params={"period": "quarter", "limit": 6},
    )

    logger.info(
        "Engine 1 | fetch_raw | success for '%s' | annual periods: %d | quarterly periods: %d",
        symbol,
        len(annual_income) if annual_income else 0,
        len(quarterly_income) if quarterly_income else 0,
    )

    return {
        "profile":            profile,
        "annual_income":      annual_income,
        "annual_balance":     annual_balance,
        "annual_cashflow":    annual_cashflow,
        "quarterly_income":   quarterly_income,
        "quarterly_cashflow": quarterly_cashflow,
    }
