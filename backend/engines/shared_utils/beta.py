"""
Shared Beta Utility
====================

Pure-computation beta calculator shared by Engine 2 (Valuation) and
Engine 3 (Risk & Financial Health).  Receives pre-computed return arrays,
runs OLS regression, and returns the result.  Does NOT fetch any external
data — data retrieval is Engine 1's responsibility.

Typical usage by a calling engine:

    from backend.engines.shared_utils.beta import compute_beta, prices_to_returns

    stock_returns = prices_to_returns(bus["market_data"]["weekly_close"])
    bench_returns = prices_to_returns(bus["market_data"]["benchmark_weekly_close"])
    result = compute_beta(stock_returns, bench_returns, sector="TECHNOLOGY")
"""

from __future__ import annotations

import logging

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

# Map frequency codes to approximate data points per year.
_FREQ_POINTS_PER_YEAR = {"W": 52, "M": 12, "D": 252}


def prices_to_returns(prices: list[float]) -> list[float]:
    """Convert a list of prices to periodic percentage returns.

    Args:
        prices: Chronological list of prices (oldest first).
                Must contain at least 2 elements.

    Returns:
        List of returns, length = len(prices) - 1.
        E.g. [100, 105, 103] -> [0.05, -0.019047...]
    """
    if len(prices) < 2:
        return []
    return [
        (prices[i] - prices[i - 1]) / prices[i - 1]
        for i in range(1, len(prices))
        if prices[i - 1] != 0
    ]


def _fallback_result(sector: str, reason: str, frequency: str) -> dict:
    """Return a sector-average beta dict when calculation is not possible.

    Args:
        sector:    The company sector (UPPERCASE).
        reason:    Human-readable reason for the fallback (logged as WARNING).
        frequency: Frequency code for the output metadata.

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
        "frequency": frequency,
        "r_squared": None,
    }


def compute_beta(
    stock_returns: list[float],
    benchmark_returns: list[float],
    sector: str,
    frequency: str | None = None,
) -> dict:
    """Compute equity beta via OLS regression of stock returns on benchmark.

    This is a pure computation — it expects pre-computed, aligned, clean
    return arrays.  The caller (typically Engine 3 or Engine 2) is
    responsible for fetching prices from the data bus and converting
    them to returns via :func:`prices_to_returns`.

    Falls back to sector-average beta from ``SECTOR_AVG_BETAS`` when:

    - Input arrays are empty or too short (< ~52 weekly observations),
    - Arrays have different lengths, or
    - The regression fails for any reason.

    Args:
        stock_returns:     Periodic percentage returns for the stock,
                           e.g. [0.012, -0.005, 0.023, ...].
                           Already cleaned (no NaN).
        benchmark_returns: Periodic percentage returns for the benchmark
                           index, same length and date-aligned.
        sector:            Company sector in UPPERCASE (e.g. "TECHNOLOGY").
                           Used for fallback beta lookup.
        frequency:         Optional frequency code ("W", "M", "D").
                           Defaults to ``BETA_FREQUENCY`` from shared_config.
                           Passed through to the output dict for metadata.

    Returns:
        A dict with keys: value, raw_beta, source, benchmark,
        lookback_years, frequency, r_squared.
    """
    freq = frequency or BETA_FREQUENCY

    # ── 1. Validate inputs ────────────────────────────────────────────
    if not stock_returns or not benchmark_returns:
        return _fallback_result(sector, "Empty return arrays", freq)

    if len(stock_returns) != len(benchmark_returns):
        return _fallback_result(
            sector,
            f"Length mismatch: stock has {len(stock_returns)} returns, "
            f"benchmark has {len(benchmark_returns)}",
            freq,
        )

    # ── 2. Check minimum data requirement ─────────────────────────────
    points_per_year = _FREQ_POINTS_PER_YEAR.get(freq, 52)
    min_points = MIN_PRICE_HISTORY_YEARS * points_per_year
    if len(stock_returns) < min_points:
        return _fallback_result(
            sector,
            f"Insufficient data: {len(stock_returns)} observations "
            f"(need >= {min_points})",
            freq,
        )

    # ── 3. OLS regression ─────────────────────────────────────────────
    try:
        slope, _intercept, r_value, _p_value, _std_err = linregress(
            benchmark_returns, stock_returns,
        )
    except Exception as exc:
        return _fallback_result(sector, f"Regression failed: {exc}", freq)

    raw_beta: float = slope
    r_squared: float = r_value ** 2

    # ── 4. Bloomberg adjustment ───────────────────────────────────────
    if BETA_USE_ADJUSTED:
        adjusted_beta = 0.67 * raw_beta + 0.33 * 1.0
    else:
        adjusted_beta = raw_beta

    # ── 5. Sanity check ──────────────────────────────────────────────
    if not (0 < adjusted_beta < 5):
        logger.warning(
            "Beta is outside expected range (0, 5): %.4f (sector=%s)",
            adjusted_beta,
            sector,
        )

    logger.info(
        "Beta calculated: adjusted=%.4f, raw=%.4f, R²=%.4f (%d obs, freq=%s)",
        adjusted_beta,
        raw_beta,
        r_squared,
        len(stock_returns),
        freq,
    )

    return {
        "value": round(adjusted_beta, 4),
        "raw_beta": round(raw_beta, 4),
        "source": "calculated",
        "benchmark": BENCHMARK_TICKER,
        "lookback_years": BETA_LOOKBACK_YEARS,
        "frequency": freq,
        "r_squared": round(r_squared, 4),
    }
