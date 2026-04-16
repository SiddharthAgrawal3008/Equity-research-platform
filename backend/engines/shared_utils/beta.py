"""
Shared Beta Utility
====================

Regression-based beta calculation shared by Engine 2 (Valuation) and
Engine 3 (Risk & Financial Health).  Falls back to sector-average beta
from shared_config when market data is unavailable or insufficient.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import yfinance as yf
from scipy.stats import linregress

from backend.engines.shared_config import (
    BENCHMARK_TICKER,
    BETA_FREQUENCY,
    BETA_LOOKBACK_YEARS,
    BETA_USE_ADJUSTED,
    DEFAULT_BETA,
    MIN_PRICE_HISTORY_YEARS,
    SECTOR_AVG_BETAS,
)

logger = logging.getLogger(__name__)

# Weekly returns per year — used to convert MIN_PRICE_HISTORY_YEARS to a
# minimum-observation count.
_WEEKS_PER_YEAR = 52


def _fallback_result(sector: str, reason: str) -> dict:
    """Return a sector-average beta dict when calculation is not possible.

    Args:
        sector:  The company sector (UPPERCASE).
        reason:  Human-readable reason for the fallback (logged as WARNING).

    Returns:
        Beta result dict with source = "industry_fallback".
    """
    fallback_beta = SECTOR_AVG_BETAS.get(sector.upper(), DEFAULT_BETA)
    logger.warning(
        "Beta fallback to sector average (%.2f) for sector '%s': %s",
        fallback_beta,
        sector,
        reason,
    )
    return {
        "value": fallback_beta,
        "raw_beta": None,
        "source": "industry_fallback",
        "benchmark": BENCHMARK_TICKER,
        "lookback_years": BETA_LOOKBACK_YEARS,
        "frequency": BETA_FREQUENCY,
        "r_squared": None,
    }


def compute_beta(ticker: str, sector: str) -> dict:
    """Compute equity beta via OLS regression against the benchmark index.

    Downloads weekly price history for *ticker* and the benchmark
    (S&P 500 by default), computes periodic returns, and regresses
    stock returns on benchmark returns.  Applies the Bloomberg
    adjustment (0.67 * raw + 0.33 * 1.0) when enabled in shared_config.

    Falls back to the sector-average beta from ``SECTOR_AVG_BETAS`` when:
    - yfinance returns no data for the ticker,
    - price history is shorter than ``MIN_PRICE_HISTORY_YEARS``, or
    - the regression fails for any reason.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        sector: Company sector in UPPERCASE (e.g. "TECHNOLOGY").

    Returns:
        A dict with keys: value, raw_beta, source, benchmark,
        lookback_years, frequency, r_squared.
    """
    # ── 1. Fetch price history ────────────────────────────────────────
    try:
        df = yf.download(
            [ticker, BENCHMARK_TICKER],
            period=f"{BETA_LOOKBACK_YEARS}y",
            interval="1wk",
            auto_adjust=True,
            progress=False,
        )
    except Exception as exc:
        return _fallback_result(sector, f"yfinance download failed: {exc}")

    if df is None or df.empty:
        return _fallback_result(sector, "yfinance returned no data")

    # ── 2. Extract Close prices for each ticker ───────────────────────
    # yfinance returns a MultiIndex DataFrame when downloading multiple
    # tickers: columns are (Price, Ticker).
    try:
        if isinstance(df.columns, pd.MultiIndex):
            stock_close = df["Close"][ticker].dropna()
            bench_close = df["Close"][BENCHMARK_TICKER].dropna()
        else:
            # Single-ticker fallback (shouldn't happen with two tickers,
            # but defensive).
            stock_close = df["Close"].dropna()
            bench_close = pd.Series(dtype=float)
    except KeyError:
        return _fallback_result(
            sector,
            f"Ticker '{ticker}' not found in downloaded data",
        )

    if stock_close.empty or bench_close.empty:
        return _fallback_result(
            sector,
            "Empty price series after extraction",
        )

    # ── 3. Compute periodic returns ───────────────────────────────────
    stock_returns = stock_close.pct_change().dropna()
    bench_returns = bench_close.pct_change().dropna()

    # Align on common dates (inner join).
    aligned = pd.concat(
        {"stock": stock_returns, "bench": bench_returns},
        axis=1,
    ).dropna()

    # ── 4. Check minimum data requirement ─────────────────────────────
    min_observations = MIN_PRICE_HISTORY_YEARS * _WEEKS_PER_YEAR
    if len(aligned) < min_observations:
        return _fallback_result(
            sector,
            f"Insufficient data: {len(aligned)} observations "
            f"(need >= {min_observations})",
        )

    # ── 5. OLS regression ─────────────────────────────────────────────
    try:
        result = linregress(aligned["bench"], aligned["stock"])
    except Exception as exc:
        return _fallback_result(sector, f"Regression failed: {exc}")

    raw_beta: float = result.slope
    r_squared: float = result.rvalue ** 2

    # ── 6. Bloomberg adjustment ───────────────────────────────────────
    if BETA_USE_ADJUSTED:
        adjusted_beta = 0.67 * raw_beta + 0.33 * 1.0
    else:
        adjusted_beta = raw_beta

    # ── 7. Sanity check ──────────────────────────────────────────────
    if not (0 < adjusted_beta < 5):
        logger.warning(
            "Beta for %s is outside expected range (0, 5): %.4f",
            ticker,
            adjusted_beta,
        )

    logger.info(
        "Beta for %s: adjusted=%.4f, raw=%.4f, R²=%.4f (%d obs)",
        ticker,
        adjusted_beta,
        raw_beta,
        r_squared,
        len(aligned),
    )

    return {
        "value": round(adjusted_beta, 4),
        "raw_beta": round(raw_beta, 4),
        "source": "calculated",
        "benchmark": BENCHMARK_TICKER,
        "lookback_years": BETA_LOOKBACK_YEARS,
        "frequency": BETA_FREQUENCY,
        "r_squared": round(r_squared, 4),
    }
