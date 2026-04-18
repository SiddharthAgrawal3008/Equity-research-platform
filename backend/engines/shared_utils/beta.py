"""
Shared Beta Utility — used by Engine 2 (WACC) and Engine 3 (Market Risk)
=========================================================================

Provides two public functions:
    prices_to_returns  — convert price series to simple period returns
    compute_beta       — OLS regression beta with Bloomberg adjustment,
                         falls back to sector average when data is insufficient
"""

from __future__ import annotations

from statistics import mean
from typing import Optional

from backend.engines.shared_config import (
    SECTOR_AVG_BETAS,
    DEFAULT_BETA,
    BENCHMARK_TICKER,
    BETA_LOOKBACK_YEARS,
    BETA_FREQUENCY,
    BETA_USE_ADJUSTED,
    MIN_PRICE_HISTORY_YEARS,
)

# Minimum number of weekly return observations required for a regression beta
# (1 year of weekly data ≈ 52 observations)
_MIN_RETURNS: int = int(MIN_PRICE_HISTORY_YEARS * 52)


def prices_to_returns(prices: list) -> list:
    """Convert a price series to simple period returns.

    Returns a list one element shorter than the input. Skips pairs where
    the prior price is zero or None.
    """
    returns: list[float] = []
    for i in range(1, len(prices)):
        prev = prices[i - 1]
        curr = prices[i]
        if prev and prev != 0 and curr is not None:
            returns.append((curr - prev) / prev)
    return returns


def compute_beta(
    stock_returns: list,
    benchmark_returns: list,
    sector: str,
) -> dict:
    """OLS beta with optional Bloomberg adjustment.

    Falls back to sector average when fewer than MIN_PRICE_HISTORY_YEARS
    years of weekly data are available or when the regression is undefined.

    Returns a dict with keys: value, raw_beta, source, benchmark,
    lookback_years, frequency, r_squared.
    """
    sector_key = (sector or "").upper()
    fallback_beta = float(SECTOR_AVG_BETAS.get(sector_key, DEFAULT_BETA))

    n = min(len(stock_returns), len(benchmark_returns))
    if n < _MIN_RETURNS:
        return _sector_fallback(fallback_beta)

    s = stock_returns[-n:]
    b = benchmark_returns[-n:]

    s_mean = mean(s)
    b_mean = mean(b)

    cov_sb = sum((si - s_mean) * (bi - b_mean) for si, bi in zip(s, b)) / (n - 1)
    var_b = sum((bi - b_mean) ** 2 for bi in b) / (n - 1)

    if var_b == 0:
        return _sector_fallback(fallback_beta)

    raw_beta: float = cov_sb / var_b

    adjusted: float = (0.67 * raw_beta + 0.33 * 1.0) if BETA_USE_ADJUSTED else raw_beta

    var_s = sum((si - s_mean) ** 2 for si in s) / (n - 1)
    r_squared: Optional[float] = (
        round(cov_sb ** 2 / (var_b * var_s), 4) if var_s > 0 else None
    )

    return {
        "value": adjusted,
        "raw_beta": raw_beta,
        "source": "calculated",
        "benchmark": BENCHMARK_TICKER,
        "lookback_years": BETA_LOOKBACK_YEARS,
        "frequency": BETA_FREQUENCY,
        "r_squared": r_squared,
    }


def _sector_fallback(fallback_beta: float) -> dict:
    return {
        "value": fallback_beta,
        "raw_beta": None,
        "source": "industry_fallback",
        "benchmark": BENCHMARK_TICKER,
        "lookback_years": BETA_LOOKBACK_YEARS,
        "frequency": BETA_FREQUENCY,
        "r_squared": None,
    }
