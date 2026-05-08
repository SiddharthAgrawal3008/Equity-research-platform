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
import time
from datetime import datetime, timezone
from typing import Any

import requests

from backend.engines.shared_config import AV_API_KEYS

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

# ---------------------------------------------------------------------------
# AV key pool — env key goes first (backward compat), then hardcoded list
# ---------------------------------------------------------------------------

def _build_av_key_pool() -> list[str]:
    """Return ordered key pool. ALPHA_VANTAGE_API_KEY from .env is tried first."""
    env_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "").strip()
    if env_key:
        return [env_key] + [k for k in AV_API_KEYS if k != env_key]
    return list(AV_API_KEYS)


_AV_KEY_POOL: list[str] = []   # populated lazily on first call
_AV_KEY_INDEX: int = 0         # current position in the pool


def _get_av_key_pool() -> list[str]:
    global _AV_KEY_POOL
    if not _AV_KEY_POOL:
        _AV_KEY_POOL = _build_av_key_pool()
    return _AV_KEY_POOL


class _RateLimitError(Exception):
    """Internal signal: AV returned a rate-limit or plan-limit response."""


def _get_fh_key() -> str:
    """Read FINNHUB_API_KEY from environment."""
    key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not key:
        raise DataFetchError(
            "FINNHUB_API_KEY environment variable is not set."
        )
    return key


def _av_get_raw(function: str, symbol: str, av_key: str) -> dict:
    """
    Single attempt: call Alpha Vantage with one key and return the JSON.
    Raises _RateLimitError on rate-limit/plan-limit responses so the caller
    can rotate to the next key. Raises DataFetchError on network failures.
    """
    params: dict[str, Any] = {
        "function": function,
        "symbol":   symbol,
        "apikey":   av_key,
    }
    try:
        response = requests.get(AV_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        # AV signals rate limits / plan restrictions via these keys instead of HTTP errors.
        if "Information" in data:
            raise _RateLimitError(data["Information"])
        if "Note" in data:
            raise _RateLimitError(data["Note"])
        return data
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


def _av_get(function: str, symbol: str) -> dict:
    """
    Call Alpha Vantage with automatic key rotation on rate-limit responses.
    Cycles through all keys in the pool before giving up.

    Raises:
        DataFetchError: If all keys are rate-limited or a network error occurs.
    """
    global _AV_KEY_INDEX
    pool = _get_av_key_pool()
    n = len(pool)

    for attempt in range(n):
        key = pool[_AV_KEY_INDEX % n]
        try:
            return _av_get_raw(function, symbol, key)
        except _RateLimitError:
            print(f"AV key {(_AV_KEY_INDEX % n) + 1}/{n} rate-limited, switching to next key...")
            _AV_KEY_INDEX = (_AV_KEY_INDEX + 1) % n

    raise DataFetchError(
        f"All {n} Alpha Vantage API keys are rate-limited for '{function}'. "
        "Please wait before retrying."
    )


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
# yfinance Fallback (used when all AV keys are rate-limited)
# ---------------------------------------------------------------------------

def _fetch_yfinance_fallback(symbol: str) -> dict:
    """
    Pull financial data via yfinance when all Alpha Vantage keys are exhausted.
    Returns the identical dict structure as fetch_raw() so downstream steps
    (standardiser, validator, TTM) work without modification.

    Yahoo Finance blocks t.info on cloud IPs (Render, AWS, etc.) with 429.
    We skip t.info entirely and use:
      - t.history()     for current price  (uses chart endpoint, not blocked)
      - t.fast_info     for market cap / shares (lighter endpoint)
      - t.financials / t.balance_sheet / t.cashflow  (timeseries endpoint, not blocked)
    """
    import yfinance as yf

    logger.info("Engine 1 | yfinance fallback | fetching '%s'", symbol)

    try:
        t = yf.Ticker(symbol)

        # ── Price: use history endpoint (not blocked on cloud IPs) ──────────
        current_price = 0.0
        try:
            hist = t.history(period="5d")
            if not hist.empty:
                current_price = float(hist["Close"].iloc[-1])
        except Exception as e:
            logger.warning("Engine 1 | yfinance | history failed (%s)", e)

        if not current_price:
            raise TickerNotFoundError(
                f"Ticker '{symbol}' not found. Please check the symbol and try again."
            )

        # ── Company metadata: fast_info (lighter than t.info) ───────────────
        market_cap = 0
        shares_outstanding = 0
        currency = "USD"
        try:
            fi = t.fast_info
            market_cap         = int(getattr(fi, "market_cap",        0) or 0)
            shares_outstanding = int(getattr(fi, "shares",            0) or 0)
            currency           = str(getattr(fi, "currency",       "USD") or "USD")
        except Exception as e:
            logger.warning("Engine 1 | yfinance | fast_info failed (%s)", e)

        overview = {
            "Symbol":                symbol,
            "Name":                  symbol,   # t.info blocked on cloud; name filled downstream
            "Description":           "",
            "Sector":                "",
            "Industry":              "",
            "Exchange":              "",
            "Currency":              currency,
            "MarketCapitalization":  str(market_cap),
            "SharesOutstanding":     str(shares_outstanding),
            "EPS":                   "0",
            "PERatio":               "0",
            "PriceToBookRatio":      "0",
            "Beta":                  "1.0",
            "52WeekHigh":            "0",
            "52WeekLow":             "0",
            "DividendYield":         "0",
            "BookValue":             "0",
        }

        def _df_to_reports(df, field_map: dict) -> list[dict]:
            if df is None or df.empty:
                return []
            reports = []
            for col in df.columns:
                date_str = str(col)[:10]
                report: dict = {"fiscalDateEnding": date_str, "reportedCurrency": "USD"}
                for yf_key, av_key in field_map.items():
                    val = df.loc[yf_key, col] if yf_key in df.index else None
                    if val is None or (isinstance(val, float) and (val != val)):
                        report[av_key] = "None"
                    else:
                        try:
                            report[av_key] = str(int(val))
                        except (TypeError, ValueError):
                            report[av_key] = str(val)
                reports.append(report)
            return reports

        INCOME_MAP = {
            "Total Revenue":                        "totalRevenue",
            "Gross Profit":                         "grossProfit",
            "Cost Of Revenue":                      "costOfRevenue",
            "Operating Income":                     "operatingIncome",
            "Ebit":                                 "ebit",
            "Ebitda":                               "ebitda",
            "Net Income":                           "netIncome",
            "Net Income Common Stockholders":       "netIncomeFromContinuingOperations",
            "Research And Development":             "researchAndDevelopment",
            "Selling General And Administration":   "sellingGeneralAndAdministrative",
            "Operating Expense":                    "operatingExpenses",
            "Reconciled Depreciation":              "depreciationAndAmortization",
            "Tax Provision":                        "incomeTaxExpense",
            "Interest Expense Non Operating":       "interestAndDebtExpense",
        }
        BALANCE_MAP = {
            "Total Assets":                                 "totalAssets",
            "Current Assets":                              "totalCurrentAssets",
            "Cash And Cash Equivalents":                   "cashAndCashEquivalentsAtCarryingValue",
            "Total Liabilities Net Minority Interest":     "totalLiabilities",
            "Current Liabilities":                         "totalCurrentLiabilities",
            "Stockholders Equity":                         "totalShareholderEquity",
            "Long Term Debt":                              "longTermDebt",
            "Current Debt":                                "currentLongTermDebt",
            "Inventory":                                   "inventory",
            "Receivables":                                 "currentNetReceivables",
            "Retained Earnings":                           "retainedEarnings",
            "Share Issued":                                "commonStockSharesOutstanding",
        }
        CASHFLOW_MAP = {
            "Operating Cash Flow":                  "operatingCashflow",
            "Capital Expenditure":                  "capitalExpenditures",
            "Investing Cash Flow":                  "cashflowFromInvestment",
            "Financing Cash Flow":                  "cashflowFromFinancing",
            "Net Income":                           "netIncome",
            "Depreciation Amortization Depletion":  "depreciationDepletionAndAmortization",
            "Common Stock Dividend Paid":           "dividendPayout",
        }

        annual_income      = _df_to_reports(t.financials,           INCOME_MAP)
        annual_balance     = _df_to_reports(t.balance_sheet,        BALANCE_MAP)
        annual_cashflow    = _df_to_reports(t.cashflow,             CASHFLOW_MAP)
        quarterly_income   = _df_to_reports(t.quarterly_financials, INCOME_MAP)
        quarterly_cashflow = _df_to_reports(t.quarterly_cashflow,   CASHFLOW_MAP)

        if not annual_income and not annual_balance and not annual_cashflow:
            raise CompanyDataUnavailableError(
                f"'{symbol}' has no publicly available financial statements."
            )

        logger.info(
            "Engine 1 | yfinance fallback | success for '%s' | periods: %d | price: %.2f",
            symbol, len(annual_income), current_price,
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

    except (TickerNotFoundError, CompanyDataUnavailableError):
        raise
    except Exception as exc:
        raise DataFetchError(f"yfinance fallback failed for '{symbol}': {exc}") from exc


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

    # ── AV path ─────────────────────────────────────────────────────────────
    try:
        return _fetch_av(symbol)
    except DataFetchError as exc:
        logger.warning("Engine 1 | AV unavailable (%s) — switching to yfinance fallback", exc)
        return _fetch_yfinance_fallback(symbol)


def _fetch_av(symbol: str) -> dict:
    """Alpha Vantage data path — extracted so fetch_raw can fall back cleanly."""
    fh_key = _get_fh_key()

    # ── 1. Company overview ─────────────────────────────────────────────────
    overview = _av_get("OVERVIEW", symbol)

    if not overview or overview.get("Symbol") is None:
        raise TickerNotFoundError(
            f"Ticker '{symbol}' not found. "
            "Please check the symbol and try again."
        )

    # AV free tier: 1 request/second. Sleep 1.2s between each call to stay safe.

    # ── 2. Income statement (annual + quarterly in one call) ────────────────
    time.sleep(1.2)
    income_data      = _av_get("INCOME_STATEMENT", symbol)
    annual_income    = income_data.get("annualReports", [])
    quarterly_income = income_data.get("quarterlyReports", [])

    # ── 3. Balance sheet (annual) ───────────────────────────────────────────
    time.sleep(1.2)
    balance_data   = _av_get("BALANCE_SHEET", symbol)
    annual_balance = balance_data.get("annualReports", [])

    # ── 4. Cash flow (annual + quarterly in one call) ───────────────────────
    time.sleep(1.2)
    cashflow_data      = _av_get("CASH_FLOW", symbol)
    annual_cashflow    = cashflow_data.get("annualReports", [])
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
