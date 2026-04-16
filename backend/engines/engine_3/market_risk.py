"""
Engine 3 — Market Risk Module
===============================

Computes all price-based risk metrics: beta, historical volatility,
Sharpe ratio, max drawdown, and Value at Risk (VaR).

This module reads pre-fetched price arrays from the shared context bus
(populated by Engine 1) and performs pure computation.  It does NOT call
yfinance or any external API.

Data flow:
    Engine 1 (fetches prices) → bus["market_data"]
        → this module reads price arrays
        → passes returns to shared compute_beta()
        → computes volatility, Sharpe, drawdown, VaR
        → returns results dict
"""

from __future__ import annotations

import logging
from datetime import datetime
from math import sqrt

import numpy as np

from backend.engines.shared_config import (
    RISK_FREE_RATE,
    VAR_CONFIDENCE_LEVEL,
)
from backend.engines.shared_utils.beta import compute_beta, prices_to_returns

logger = logging.getLogger(__name__)


def compute_market_risk(financial_data: dict) -> dict:
    """Compute all market risk metrics from price data on the bus.

    Args:
        financial_data: The full financial_data dict from the context bus.
                        Reads from financial_data["market_data"] for prices
                        and financial_data["meta"]["sector"] for beta fallback.

    Returns:
        Dict with beta, market_risk, price metadata, and warnings.
    """
    meta = financial_data["meta"]
    market_data = financial_data.get("market_data", {})
    sector = meta.get("sector", "")

    daily_close = market_data.get("daily_close", [])
    weekly_close = market_data.get("weekly_close", [])
    benchmark_weekly_close = market_data.get("benchmark_weekly_close", [])
    benchmark_daily_close = market_data.get("benchmark_daily_close", [])
    daily_dates = market_data.get("daily_dates", [])
    weekly_dates = market_data.get("weekly_dates", [])

    warnings: list[str] = []

    # ── A. Compute returns ────────────────────────────────────────────
    stock_weekly_returns = prices_to_returns(weekly_close)
    bench_weekly_returns = prices_to_returns(benchmark_weekly_close)
    stock_daily_returns = prices_to_returns(daily_close)

    # ── B. Beta (always attempted — handles fallback internally) ──────
    beta_result = compute_beta(
        stock_returns=stock_weekly_returns,
        benchmark_returns=bench_weekly_returns,
        sector=sector,
    )
    if beta_result["source"] == "industry_fallback":
        warnings.append(
            f"Beta: using sector average ({beta_result['value']}) — "
            "insufficient weekly price data for regression"
        )

    # ── C. Check data availability ──────────────────────────────────
    has_weekly = bool(weekly_close)
    has_daily = bool(daily_close)

    if not has_weekly and not has_daily:
        logger.warning(
            "No price history available — market risk metrics unavailable"
        )
        warnings.append(
            "No price history available — market risk metrics unavailable"
        )
        return {
            "beta": beta_result,
            "market_risk": {
                "historical_volatility": None,
                "sharpe_ratio": None,
                "max_drawdown": None,
                "max_drawdown_start": None,
                "max_drawdown_end": None,
                "var_95_daily": None,
                "annualized_return": None,
            },
            "price_data_start": None,
            "price_data_end": None,
            "warnings": warnings,
        }

    if not has_daily:
        warnings.append(
            "No daily price data — max drawdown and VaR unavailable"
        )
    if not has_weekly:
        warnings.append(
            "No weekly price data — volatility, Sharpe, and annualized "
            "return unavailable"
        )

    # ── D. Historical volatility (annualized from weekly returns) ─────
    historical_volatility = None
    try:
        if stock_weekly_returns:
            weekly_std = np.std(stock_weekly_returns, ddof=1)
            historical_volatility = round(float(weekly_std * sqrt(52)), 4)
    except Exception as exc:
        logger.warning("Volatility computation failed: %s", exc)
        warnings.append(f"Volatility computation failed: {exc}")

    # ── E. Annualized return (CAGR from weekly close prices) ──────────
    annualized_return = None
    try:
        if len(weekly_close) >= 2 and len(weekly_dates) >= 2:
            start_price = weekly_close[0]
            end_price = weekly_close[-1]
            start_date = datetime.strptime(weekly_dates[0], "%Y-%m-%d")
            end_date = datetime.strptime(weekly_dates[-1], "%Y-%m-%d")
            n_years = (end_date - start_date).days / 365.25
            if n_years > 0 and start_price > 0:
                annualized_return = round(
                    float((end_price / start_price) ** (1 / n_years) - 1), 4
                )
    except Exception as exc:
        logger.warning("Annualized return computation failed: %s", exc)
        warnings.append(f"Annualized return computation failed: {exc}")

    # ── F. Sharpe ratio ───────────────────────────────────────────────
    sharpe_ratio = None
    try:
        if annualized_return is not None and historical_volatility:
            sharpe_ratio = round(
                float(
                    (annualized_return - RISK_FREE_RATE)
                    / historical_volatility
                ),
                4,
            )
    except Exception as exc:
        logger.warning("Sharpe ratio computation failed: %s", exc)
        warnings.append(f"Sharpe ratio computation failed: {exc}")

    # ── G. Max drawdown (from daily data) ─────────────────────────────
    max_drawdown = None
    max_drawdown_start = None
    max_drawdown_end = None
    try:
        if len(daily_close) >= 2:
            daily_arr = np.array(daily_close, dtype=float)
            running_max = np.maximum.accumulate(daily_arr)
            drawdown = (daily_arr - running_max) / running_max
            max_drawdown = round(float(drawdown.min()), 4)
            trough_idx = int(drawdown.argmin())
            peak_idx = int(daily_arr[: trough_idx + 1].argmax())
            if daily_dates:
                max_drawdown_start = daily_dates[peak_idx][:7]  # "YYYY-MM"
                max_drawdown_end = daily_dates[trough_idx][:7]
    except Exception as exc:
        logger.warning("Max drawdown computation failed: %s", exc)
        warnings.append(f"Max drawdown computation failed: {exc}")

    # ── H. VaR — Historical Simulation, 95%, Daily ────────────────────
    var_95_daily = None
    try:
        if stock_daily_returns:
            percentile = (1 - VAR_CONFIDENCE_LEVEL) * 100  # 5th percentile
            var_95_daily = round(
                float(np.percentile(stock_daily_returns, percentile)), 4
            )
    except Exception as exc:
        logger.warning("VaR computation failed: %s", exc)
        warnings.append(f"VaR computation failed: {exc}")

    # ── I. Price data date range ──────────────────────────────────────
    if daily_dates:
        price_data_start = daily_dates[0]
        price_data_end = daily_dates[-1]
    elif weekly_dates:
        price_data_start = weekly_dates[0]
        price_data_end = weekly_dates[-1]
    else:
        price_data_start = None
        price_data_end = None

    logger.info(
        "Market risk computed: vol=%.4f, sharpe=%.4f, drawdown=%.4f, "
        "var95=%.4f (%s to %s)",
        historical_volatility or 0,
        sharpe_ratio or 0,
        max_drawdown or 0,
        var_95_daily or 0,
        price_data_start,
        price_data_end,
    )

    return {
        "beta": beta_result,
        "market_risk": {
            "historical_volatility": historical_volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "max_drawdown_start": max_drawdown_start,
            "max_drawdown_end": max_drawdown_end,
            "var_95_daily": var_95_daily,
            "annualized_return": annualized_return,
        },
        "price_data_start": price_data_start,
        "price_data_end": price_data_end,
        "warnings": warnings,
    }
