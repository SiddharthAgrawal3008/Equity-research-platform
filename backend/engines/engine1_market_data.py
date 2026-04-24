"""
Engine 1 — Market Data (Step 5)
================================

Fetches historical adjusted close prices for the stock and S&P 500
benchmark using yfinance and returns a market_data dict for Engine1Output.

WHAT THIS MODULE DOES:
    - Downloads daily adjusted close prices for 5 years (stock + benchmark)
    - Downloads weekly adjusted close prices for 2 years (stock + benchmark)
    - Inner-joins stock and benchmark on dates so arrays are always aligned
    - Sorts all arrays chronologically (oldest first)
    - Validates array lengths, price positivity, and date ordering
    - Returns (market_data dict, warnings list)

WHAT THIS MODULE DOES NOT DO:
    - Does not compute beta, volatility, Sharpe, drawdown, or VaR
    - Does not store pandas DataFrames — all output is plain Python lists
    - Does not hardcode lookback periods or benchmark ticker

CONSUMER:
    Engine 3 (Risk & Financial Health) — reads market_data to compute all
    market risk metrics. Engine 3 never imports yfinance directly.

ERROR HANDLING:
    On any failure, returns empty arrays and a warning. Engine 1 still
    succeeds — financial statement data is the primary output.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import yfinance as yf

from backend.engines.shared_config import (
    BENCHMARK_TICKER,
    BETA_LOOKBACK_YEARS,
    DRAWDOWN_LOOKBACK_YEARS,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _empty_market_data(current_price: Optional[float]) -> dict:
    """Return the fallback market_data dict with all price arrays empty."""
    return {
        "daily_close":            [],
        "daily_dates":            [],
        "weekly_close":           [],
        "weekly_dates":           [],
        "benchmark_daily_close":  [],
        "benchmark_daily_dates":  [],
        "benchmark_weekly_close": [],
        "benchmark_weekly_dates": [],
        "current_price":          current_price,
        "benchmark_ticker":       BENCHMARK_TICKER,
    }


def _download_and_align(
    ticker: str,
    period_years: int,
    interval: str,
) -> tuple[list[float], list[str], list[float], list[str]]:
    """
    Download adjusted close prices for ticker and benchmark, inner-join on
    date index, and return (stock_close, dates, bench_close, bench_dates).

    dates and bench_dates are identical by construction (inner join).
    Returns four empty lists if the download is empty or fails.
    """
    df = yf.download(
        [ticker, BENCHMARK_TICKER],
        period=f"{period_years}y",
        interval=interval,
        auto_adjust=True,
        progress=False,
    )

    if df.empty:
        return [], [], [], []

    # yfinance returns MultiIndex columns when downloading 2 tickers:
    # ("Close", "AAPL") and ("Close", "^GSPC")
    stock_close = df["Close"][ticker].dropna()
    bench_close = df["Close"][BENCHMARK_TICKER].dropna()

    # Inner join — only dates where BOTH have data, drop any remaining NaN
    aligned = pd.concat([stock_close, bench_close], axis=1, join="inner").dropna()
    aligned.columns = ["stock", "bench"]

    if aligned.empty:
        return [], [], [], []

    # Sort oldest first — matches the convention used in financials arrays
    aligned = aligned.sort_index()

    dates = [d.strftime("%Y-%m-%d") for d in aligned.index]
    stock_prices: list[float] = aligned["stock"].tolist()
    bench_prices: list[float] = aligned["bench"].tolist()

    # bench_dates are identical to dates by construction
    return stock_prices, dates, bench_prices, dates


def _validate(
    stock_close: list[float],
    dates: list[str],
    bench_close: list[float],
    label: str,
) -> list[str]:
    """
    Run validation checks on an aligned price pair.
    Returns a list of error strings (empty if all checks pass).
    """
    errors: list[str] = []

    if len(stock_close) != len(dates):
        errors.append(
            f"market_data {label}: stock array length {len(stock_close)} "
            f"!= dates length {len(dates)} — data malformed."
        )
    if len(bench_close) != len(stock_close):
        errors.append(
            f"market_data {label}: benchmark array length {len(bench_close)} "
            f"!= stock array length {len(stock_close)} — alignment broken."
        )
    if stock_close and not all(p > 0 for p in stock_close):
        errors.append(
            f"market_data {label}: non-positive price found in stock_close — data quality issue."
        )
    if dates and dates != sorted(dates):
        errors.append(
            f"market_data {label}: dates are not in chronological order."
        )

    return errors


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

def build_market_data(
    ticker: str,
    current_price: Optional[float],
) -> tuple[dict, list[str]]:
    """
    Fetch historical price data for ticker and benchmark and return a
    market_data dict aligned for Engine 3 risk metric computation.

    Args:
        ticker:        Stock ticker symbol, e.g. "AAPL".
        current_price: Latest price already fetched by Engine 1 (Finnhub) —
                       passed through unchanged.

    Returns:
        (market_data, warnings)

        market_data fields:
            daily_close            list[float]  — stock, daily, 5yr, oldest-first
            daily_dates            list[str]    — "YYYY-MM-DD", same length
            weekly_close           list[float]  — stock, weekly, 2yr, oldest-first
            weekly_dates           list[str]    — "YYYY-MM-DD", same length
            benchmark_daily_close  list[float]  — S&P 500, inner-joined to daily
            benchmark_daily_dates  list[str]    — identical to daily_dates
            benchmark_weekly_close list[float]  — S&P 500, inner-joined to weekly
            benchmark_weekly_dates list[str]    — identical to weekly_dates
            current_price          float | None — pass-through from argument
            benchmark_ticker       str          — from shared_config

        warnings: non-empty if any data was unavailable or fell back to empty.
        On full failure, all price arrays are [] and warnings describes why.
    """
    warnings: list[str] = []

    # ── Daily data (5 years — used by Engine 3 for drawdown and VaR) ─────────
    try:
        daily_close, daily_dates, benchmark_daily_close, benchmark_daily_dates = (
            _download_and_align(ticker, DRAWDOWN_LOOKBACK_YEARS, "1d")
        )

        if not daily_close:
            warnings.append(
                f"market_data: daily price download returned empty for '{ticker}' "
                f"or '{BENCHMARK_TICKER}' — market risk metrics will be unavailable."
            )
            return _empty_market_data(current_price), warnings

        daily_errors = _validate(daily_close, daily_dates, benchmark_daily_close, "daily")
        if daily_errors:
            warnings.extend(daily_errors)
            return _empty_market_data(current_price), warnings

        if len(daily_close) < 60:
            warnings.append(
                f"market_data: only {len(daily_close)} daily observations available — "
                "insufficient history for reliable VaR calculation."
            )

    except Exception as exc:
        logger.error("Engine 1 | build_market_data | daily download failed: %s", exc)
        warnings.append(
            f"Price data fetch failed (daily) — market risk metrics will be unavailable. "
            f"Error: {exc}"
        )
        return _empty_market_data(current_price), warnings

    # ── Weekly data (2 years — used by Engine 3 for beta, volatility, Sharpe) ─
    try:
        weekly_close, weekly_dates, benchmark_weekly_close, benchmark_weekly_dates = (
            _download_and_align(ticker, BETA_LOOKBACK_YEARS, "1wk")
        )

        if not weekly_close:
            warnings.append(
                f"market_data: weekly price download returned empty for '{ticker}' "
                "— beta/volatility/Sharpe metrics will be unavailable."
            )
            weekly_close, weekly_dates = [], []
            benchmark_weekly_close, benchmark_weekly_dates = [], []
        else:
            weekly_errors = _validate(
                weekly_close, weekly_dates, benchmark_weekly_close, "weekly"
            )
            if weekly_errors:
                warnings.extend(weekly_errors)
                weekly_close, weekly_dates = [], []
                benchmark_weekly_close, benchmark_weekly_dates = [], []
            elif len(weekly_close) < 52:
                warnings.append(
                    f"market_data: only {len(weekly_close)} weekly observations — "
                    "fewer than 52 weeks; Engine 3 will use sector beta fallback."
                )

    except Exception as exc:
        logger.error("Engine 1 | build_market_data | weekly download failed: %s", exc)
        warnings.append(
            f"Price data fetch failed (weekly) — beta/volatility/Sharpe metrics will be unavailable. "
            f"Error: {exc}"
        )
        weekly_close, weekly_dates = [], []
        benchmark_weekly_close, benchmark_weekly_dates = [], []

    market_data = {
        "daily_close":            daily_close,
        "daily_dates":            daily_dates,
        "weekly_close":           weekly_close,
        "weekly_dates":           weekly_dates,
        "benchmark_daily_close":  benchmark_daily_close,
        "benchmark_daily_dates":  benchmark_daily_dates,
        "benchmark_weekly_close": benchmark_weekly_close,
        "benchmark_weekly_dates": benchmark_weekly_dates,
        "current_price":          current_price,
        "benchmark_ticker":       BENCHMARK_TICKER,
    }

    logger.info(
        "Engine 1 | build_market_data | %s | daily=%d pts | weekly=%d pts",
        ticker,
        len(daily_close),
        len(weekly_close),
    )

    return market_data, warnings
