"""
Engine 1 — Financial Data Engine (Step 1: Raw Data Pull)
=========================================================

RESPONSIBILITY:
    Pull ALL raw financial data from yfinance for a given ticker.
    Nothing is renamed, mapped, or filtered here.
    Every field yfinance returns is preserved so the
    standardization layer (Step 2) has the full picture to work with.

WHAT THIS MODULE DOES NOT DO:
    - Does not rename fields to match Contract A schema  (that's Step 2)
    - Does not validate array lengths or None values     (that's Step 3)
    - Does not compute TTM                               (that's Step 4)
    - Does not compute derived metrics like EBITDA       (that's Step 2)

ERRORS THIS MODULE RAISES:
    TickerNotFoundError         — symbol does not exist on any exchange
    CompanyDataUnavailableError — company exists but has no public financial data
                                  (private company, OTC-only, or pre-revenue startup)
    DataFetchError              — network/upstream failure (timeout, proxy block, etc.)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


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
    Yahoo Finance is unreachable (timeout, rate limit, proxy block, etc.).

    Frontend message: "Unable to fetch data right now. Please try again
    in a moment."
    """


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _dataframe_to_raw_dict(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """
    Convert a yfinance financial DataFrame to a plain nested dict.

    yfinance returns DataFrames where:
        rows    = financial line items  (e.g. "Total Revenue")
        columns = period-end dates      (Timestamp objects, NEWEST FIRST)

    We convert every value to float or None so the result is:
        1. JSON-serializable
        2. Lossless — no data is dropped before Step 2 can use it

    Date keys are stored as ISO date strings ("2024-09-30") so they
    survive serialization without any Timestamp objects floating around.

    Returns:
        {
            "Total Revenue": {
                "2024-09-30": 391035000000.0,
                "2023-09-30": 383285000000.0,
                ...
            },
            "Cost Of Revenue": { ... },
            ...
        }

        Returns {} if the DataFrame is None or empty.
    """
    if df is None or df.empty:
        return {}

    raw: dict[str, dict[str, Any]] = {}

    for row_label in df.index:
        row_data: dict[str, Any] = {}
        for col in df.columns:
            value = df.loc[row_label, col]
            # pd.isna catches both float NaN and pandas NA
            row_data[str(col.date())] = None if pd.isna(value) else float(value)
        raw[str(row_label)] = row_data

    return raw


def _check_ticker_validity(yfin_ticker: yf.Ticker, symbol: str) -> None:
    """
    Detect two distinct failure modes before we attempt any data pulls.

    WHY TWO SEPARATE ERRORS:
        The frontend needs to show different messages:
        - "Ticker not found" → user likely mistyped the symbol
        - "Company not available" → user found the right symbol but
          we can't serve data for it (private company, etc.)

    Failure Mode 1 — Ticker doesn't exist:
        yfinance returns a near-empty info dict with no company name.
        Example: yf.Ticker("BLAH123").info → {'trailingPegRatio': None}

    Failure Mode 2 — Company exists but no public financials:
        info has longName, sector, etc. but financials DataFrame is empty.
        Example: a private company whose ticker is listed but not traded.

    Args:
        yfin_ticker: The yfinance Ticker object (already instantiated).
        symbol:      The cleaned ticker string, used in error messages.

    Raises:
        TickerNotFoundError:         Symbol doesn't exist.
        CompanyDataUnavailableError: Company has no public financial data.
    """
    try:
        info = yfin_ticker.info
    except Exception as exc:
        exc_str = str(exc).lower()
        # Network-level failures (proxy, timeout, connection refused) are
        # a different problem from an invalid ticker — don't conflate them.
        if any(word in exc_str for word in ("proxy", "connect", "timeout", "network", "ssl")):
            raise DataFetchError(
                "Unable to reach Yahoo Finance right now. "
                "Please check your connection and try again."
            ) from exc
        # yfinance throws on badly formed / unknown tickers in some versions
        raise TickerNotFoundError(
            f"Ticker '{symbol}' not found. "
            "Please check the symbol and try again (e.g. 'AAPL', 'INFY.NS')."
        ) from exc

    # A valid ticker always has at least a company name in its info dict.
    # Invalid tickers return a sparse dict with no identifying information.
    has_company_name = bool(info.get("longName") or info.get("shortName"))
    if not has_company_name:
        raise TickerNotFoundError(
            f"Ticker '{symbol}' not found. "
            "Please check the symbol and try again (e.g. 'AAPL', 'INFY.NS')."
        )

    # Company name found, but if financials are empty it's private/unavailable.
    # We call .financials here once; yfinance caches internally so the second
    # call inside fetch_raw() does not make another network request.
    if yfin_ticker.financials.empty:
        company_name = info.get("longName", symbol)
        raise CompanyDataUnavailableError(
            f"'{company_name}' does not have publicly available financial "
            "statements. This platform currently covers publicly listed "
            "companies with at least one year of filed annual financials."
        )


# ---------------------------------------------------------------------------
# Main Entry Point for Step 1
# ---------------------------------------------------------------------------

def fetch_raw(ticker_symbol: str) -> dict:
    """
    Pull ALL raw financial data for a ticker from yfinance.

    This is the only public function in this module.
    It is called by the orchestrating run() function (built in later steps).

    IMPORTANT NOTES ON DATA VOLUME:
        - yfinance returns up to 4 years of annual data by default.
          If only 3-4 years are available, that is recorded in the output
          under 'annual_periods_available' so the standardizer (Step 2)
          knows what it received without having to infer it.
        - Quarterly data (last 4 quarters) is fetched separately for
          TTM computation in Step 4.
        - All data comes back newest-first from yfinance.
          Step 2 is responsible for sorting oldest-to-newest per
          Contract A Rule #2.

    Args:
        ticker_symbol: Stock ticker string, e.g. "AAPL" or "INFY.NS".
                       Case-insensitive — will be uppercased internally.

    Returns:
        A raw dict with these top-level keys:

        ticker                       — uppercased symbol
        pull_timestamp               — ISO 8601 UTC string of when data was fetched
        annual_periods_available     — int, how many annual columns yfinance returned
        company_info                 — full dict from yfinance .info (everything)
        annual_income_statement      — all rows × all annual date columns
        annual_balance_sheet         — all rows × all annual date columns
        annual_cash_flow             — all rows × all annual date columns
        quarterly_income_statement   — all rows × last 4 quarter columns (for TTM)
        quarterly_cash_flow          — all rows × last 4 quarter columns (for TTM)

    Raises:
        TickerNotFoundError:         Ticker symbol does not exist.
        CompanyDataUnavailableError: Company has no public financial data.
    """
    symbol = ticker_symbol.strip().upper()
    logger.info("Engine 1 | fetch_raw | starting pull for '%s'", symbol)

    yfin = yf.Ticker(symbol)

    # Fail fast — check validity before pulling anything else
    _check_ticker_validity(yfin, symbol)

    # --- Annual statements (yfinance caches after first call above) ---
    annual_income   = _dataframe_to_raw_dict(yfin.financials)
    annual_balance  = _dataframe_to_raw_dict(yfin.balance_sheet)
    annual_cashflow = _dataframe_to_raw_dict(yfin.cashflow)

    # --- Quarterly statements (needed for TTM in Step 4) ---
    quarterly_income   = _dataframe_to_raw_dict(yfin.quarterly_financials)
    quarterly_cashflow = _dataframe_to_raw_dict(yfin.quarterly_cashflow)

    # How many annual periods did we actually get?
    # Take the count from income statement (most complete statement typically).
    # Step 2 uses this to know if it has 3, 4, or 5 years to work with.
    annual_periods = len(
        next(iter(annual_income.values()), {}).keys()
    ) if annual_income else 0

    # --- Full company info dict (every key yfinance provides) ---
    company_info = dict(yfin.info)

    logger.info(
        "Engine 1 | fetch_raw | success for '%s' | annual periods fetched: %d",
        symbol,
        annual_periods,
    )

    return {
        "ticker":                     symbol,
        "pull_timestamp":             datetime.now(timezone.utc).isoformat(),
        "annual_periods_available":   annual_periods,
        "company_info":               company_info,
        "annual_income_statement":    annual_income,
        "annual_balance_sheet":       annual_balance,
        "annual_cash_flow":           annual_cashflow,
        "quarterly_income_statement": quarterly_income,
        "quarterly_cash_flow":        quarterly_cashflow,
    }
