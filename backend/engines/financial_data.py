"""
Engine 1 — Financial Data Engine (Step 1: Raw Data Pull)
=========================================================

RESPONSIBILITY:
    Pull ALL raw financial data for a given ticker using two APIs:
      - Alpha Vantage  : company overview + all financial statements
      - Finnhub        : real-time current price only

    Nothing is renamed, mapped, or filtered here. Every field the APIs
    return is preserved so the standardization layer (Step 2) has the
    full picture to work with.

WHAT THIS MODULE DOES NOT DO:
    - Does not rename fields to match the contract schema  (that's Step 2)
    - Does not validate array lengths or None values       (that's Step 3)
    - Does not compute TTM                                 (that's Step 4)
    - Does not compute derived metrics                     (that's Step 2)

ERRORS THIS MODULE RAISES:
    TickerNotFoundError         — symbol does not exist (AV OVERVIEW returns empty)
    CompanyDataUnavailableError — company exists but has no financial statements
    DataFetchError              — network/upstream failure or missing API key

ENVIRONMENT VARIABLES (add to .env):
    ALPHA_VANTAGE_API_KEY — Alpha Vantage API key
    FINNHUB_API_KEY       — Finnhub API key
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

AV_BASE_URL = "https://www.alphavantage.co/query"
FH_BASE_URL = "https://finnhub.io/api/v1"


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
    the API is unreachable (timeout, rate limit, connection error, etc.).

    Frontend message: "Unable to fetch data right now. Please try again
    in a moment."
    """


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _get_av_key() -> str:
    """Read ALPHA_VANTAGE_API_KEY from environment."""
    key = os.environ.get("ALPHA_VANTAGE_API_KEY", "").strip()
    if not key:
        raise DataFetchError(
            "ALPHA_VANTAGE_API_KEY environment variable is not set."
        )
    return key


def _get_fh_key() -> str:
    """Read FINNHUB_API_KEY from environment."""
    key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not key:
        raise DataFetchError(
            "FINNHUB_API_KEY environment variable is not set."
        )
    return key


def _av_get(function: str, symbol: str, av_key: str) -> dict:
    """
    Call Alpha Vantage and return the parsed JSON response.

    Args:
        function: AV function name, e.g. "OVERVIEW", "INCOME_STATEMENT"
        symbol:   Ticker symbol, e.g. "AAPL"
        av_key:   Alpha Vantage API key

    Returns:
        Parsed JSON response dict.

    Raises:
        DataFetchError: On timeout, connection error, or non-200 response.
    """
    params: dict[str, Any] = {
        "function": function,
        "symbol":   symbol,
        "apikey":   av_key,
    }
    try:
        response = requests.get(AV_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as exc:
        raise DataFetchError(
            f"Alpha Vantage request timed out for function '{function}'. "
            "Please try again."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise DataFetchError(
            f"Could not connect to Alpha Vantage: {exc}"
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise DataFetchError(
            f"Alpha Vantage returned HTTP {exc.response.status_code} "
            f"for function '{function}': {exc}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise DataFetchError(
            f"Unexpected error calling Alpha Vantage '{function}': {exc}"
        ) from exc


def _fh_get(endpoint: str, params: dict, fh_key: str) -> dict:
    """
    Call Finnhub and return the parsed JSON response.

    Args:
        endpoint: Path relative to FH_BASE_URL, e.g. "/quote"
        params:   Query parameters (token is added automatically)
        fh_key:   Finnhub API key

    Returns:
        Parsed JSON response dict.

    Raises:
        DataFetchError: On timeout, connection error, or non-200 response.
    """
    url = f"{FH_BASE_URL}{endpoint}"
    query_params = {**params, "token": fh_key}
    try:
        response = requests.get(url, params=query_params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as exc:
        raise DataFetchError(
            f"Finnhub request timed out for endpoint '{endpoint}'. "
            "Please try again."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise DataFetchError(
            f"Could not connect to Finnhub: {exc}"
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise DataFetchError(
            f"Finnhub returned HTTP {exc.response.status_code} "
            f"for endpoint '{endpoint}': {exc}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise DataFetchError(
            f"Unexpected error calling Finnhub '{endpoint}': {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Main Entry Point for Step 1
# ---------------------------------------------------------------------------

def fetch_raw(ticker_symbol: str) -> dict:
    """
    Pull ALL raw financial data for a ticker from Alpha Vantage + Finnhub.

    This is the only public function in this module.

    Alpha Vantage provides:
        OVERVIEW          — company info, sector, industry, market cap, etc.
        INCOME_STATEMENT  — annual + quarterly income statements
        BALANCE_SHEET     — annual balance sheets
        CASH_FLOW         — annual + quarterly cash flows

    Finnhub provides:
        /quote            — real-time current price (field "c")

    Args:
        ticker_symbol: Stock ticker, e.g. "AAPL". Case-insensitive —
                       uppercased internally.

    Returns:
        {
            "ticker":              str   — uppercased symbol
            "pull_timestamp":      str   — ISO 8601 UTC timestamp
            "overview":            dict  — AV OVERVIEW response
            "annual_income":       list  — AV annual income statement reports
            "annual_balance":      list  — AV annual balance sheet reports
            "annual_cashflow":     list  — AV annual cash flow reports
            "quarterly_income":    list  — AV quarterly income statement reports
            "quarterly_cashflow":  list  — AV quarterly cash flow reports
            "current_price":       float — Finnhub real-time price (USD)
        }

    Raises:
        TickerNotFoundError:         AV OVERVIEW returns empty or no Symbol field.
        CompanyDataUnavailableError: Overview found but all statements are empty.
        DataFetchError:              Network failure, timeout, or missing API key.
    """
    symbol = ticker_symbol.strip().upper()
    logger.info("Engine 1 | fetch_raw | starting pull for '%s'", symbol)

    av_key = _get_av_key()
    fh_key = _get_fh_key()

    # ── 1. Company overview ─────────────────────────────────────────────────
    overview = _av_get("OVERVIEW", symbol, av_key)

    if not overview or overview.get("Symbol") is None:
        raise TickerNotFoundError(
            f"Ticker '{symbol}' not found. "
            "Please check the symbol and try again."
        )

    # ── 2. Income statement (annual + quarterly in one call) ────────────────
    income_data      = _av_get("INCOME_STATEMENT", symbol, av_key)
    annual_income    = income_data.get("annualReports", [])
    quarterly_income = income_data.get("quarterlyReports", [])

    # ── 3. Balance sheet (annual) ───────────────────────────────────────────
    balance_data   = _av_get("BALANCE_SHEET", symbol, av_key)
    annual_balance = balance_data.get("annualReports", [])

    # ── 4. Cash flow (annual + quarterly in one call) ───────────────────────
    cashflow_data     = _av_get("CASH_FLOW", symbol, av_key)
    annual_cashflow   = cashflow_data.get("annualReports", [])
    quarterly_cashflow = cashflow_data.get("quarterlyReports", [])

    # ── 5. Check financial data availability ────────────────────────────────
    # Overview exists but no statements → private company or pre-revenue startup
    if not annual_income and not annual_balance and not annual_cashflow:
        company_name = overview.get("Name", symbol)
        raise CompanyDataUnavailableError(
            f"'{company_name}' does not have publicly available financial "
            "statements. This platform currently covers publicly listed "
            "companies with at least one year of filed annual financials."
        )

    # ── 6. Current price from Finnhub ───────────────────────────────────────
    quote = _fh_get("/quote", {"symbol": symbol}, fh_key)
    current_price = quote.get("c")

    if not current_price:
        raise DataFetchError(
            f"Could not fetch current price from Finnhub for '{symbol}'. "
            "The quote endpoint returned no price data."
        )

    logger.info(
        "Engine 1 | fetch_raw | success for '%s' | "
        "annual income periods: %d | price: %.2f",
        symbol,
        len(annual_income),
        current_price,
    )

    return {
        "ticker":             symbol,
        "pull_timestamp":     datetime.now(timezone.utc).isoformat(),
        "overview":           overview,
        "annual_income":      annual_income,
        "annual_balance":     annual_balance,
        "annual_cashflow":    annual_cashflow,
        "quarterly_income":   quarterly_income,
        "quarterly_cashflow": quarterly_cashflow,
        "current_price":      current_price,
    }
