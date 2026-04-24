"""
Engine 3 — Market Risk Module

Computes all price-based risk metrics from closing prices:
  beta, historical volatility, Sharpe ratio, max drawdown, VaR (95%).

Input keys read from financial_data:
    financial_data["market_data"]["weekly_close"]           — weekly stock prices (beta)
    financial_data["market_data"]["benchmark_weekly_close"] — weekly benchmark prices (beta)
    financial_data["market_data"]["daily_close"]            — daily stock prices (vol/Sharpe/drawdown/VaR)
    financial_data["market_data"]["daily_dates"]            — ISO date strings, same length as daily_close
    financial_data["meta"]["sector"]                        — sector string, for beta fallback

Does NOT call any external API — all data must be pre-fetched by Engine 1.
"""

from __future__ import annotations

import logging

import numpy as np

from backend.engines.shared_config import (
    RISK_FREE_RATE,
    VAR_CONFIDENCE_LEVEL,
)
from backend.engines.shared_utils.beta import compute_beta, prices_to_returns

logger = logging.getLogger(__name__)


def compute_market_risk(financial_data: dict) -> dict:
    """Compute market risk metrics from price history on the data bus.

    Returns:
        {
            "beta":        {"value": float, "raw_beta": float|None, "source": str},
            "market_risk": {
                "historical_volatility": float|None,   # annualised (daily std × √252)
                "sharpe_ratio":          float|None,
                "max_drawdown":          float|None,
                "max_drawdown_start":    str|None,     # "YYYY-MM"
                "max_drawdown_end":      str|None,
                "var_95_daily":          float|None,   # 5th-pct of daily log returns
                "annualized_return":     float|None,
            },
            "warnings": list[str],
        }
    """
    market_data   = financial_data.get("market_data", {})
    sector        = financial_data.get("meta", {}).get("sector", "")

    daily_prices  = market_data.get("daily_close")            or []
    daily_dates   = market_data.get("daily_dates")            or []
    weekly_prices = market_data.get("weekly_close")           or []
    weekly_bench  = market_data.get("benchmark_weekly_close") or []

    warnings: list[str] = []

    # ── Beta (weekly prices via shared_utils — single source of truth) ───
    stock_rets  = prices_to_returns(weekly_prices)
    bench_rets  = prices_to_returns(weekly_bench)
    beta_result = compute_beta(stock_rets, bench_rets, sector)
    if beta_result["source"] != "calculated":
        warnings.append(f"Beta: sector average ({beta_result['value']}) used — insufficient weekly price data")

    # ── Daily-based metrics ───────────────────────────────────────────────
    if len(daily_prices) < 2:
        warnings.append("No price history — all market risk metrics unavailable")
        return {
            "beta":        beta_result,
            "market_risk": _empty_market_risk(),
            "warnings":    warnings,
        }

    price_arr = np.array(daily_prices, dtype=float)
    log_rets  = np.log(price_arr[1:] / price_arr[:-1])

    # ── Volatility (annualised) ───────────────────────────────────────────
    volatility = None
    try:
        volatility = round(float(np.std(log_rets, ddof=1) * np.sqrt(252)), 4)
    except Exception as exc:
        warnings.append(f"Volatility failed: {exc}")

    # ── Annualised return (CAGR) ──────────────────────────────────────────
    ann_return = None
    try:
        n = len(log_rets)
        ann_return = round(float((price_arr[-1] / price_arr[0]) ** (252 / n) - 1), 4)
    except Exception as exc:
        warnings.append(f"Annualised return failed: {exc}")

    # ── Sharpe ratio ──────────────────────────────────────────────────────
    sharpe = None
    try:
        if ann_return is not None and volatility:
            sharpe = round((ann_return - RISK_FREE_RATE) / volatility, 4)
    except Exception as exc:
        warnings.append(f"Sharpe failed: {exc}")

    # ── Max drawdown ──────────────────────────────────────────────────────
    max_dd = max_dd_start = max_dd_end = None
    try:
        peak       = np.maximum.accumulate(price_arr)
        dd         = (price_arr - peak) / peak
        max_dd     = round(float(dd.min()), 4)
        trough_idx = int(dd.argmin())
        peak_idx   = int(price_arr[:trough_idx + 1].argmax())
        if daily_dates:
            max_dd_start = daily_dates[peak_idx][:7]
            max_dd_end   = daily_dates[trough_idx][:7]
    except Exception as exc:
        warnings.append(f"Max drawdown failed: {exc}")

    # ── VaR 95% (historical simulation, daily) ───────────────────────────
    var_95 = None
    try:
        var_95 = round(float(np.percentile(log_rets, (1 - VAR_CONFIDENCE_LEVEL) * 100)), 4)
    except Exception as exc:
        warnings.append(f"VaR failed: {exc}")

    logger.info(
        "Market risk: beta=%.4f (%s), vol=%.4f, sharpe=%.4f, dd=%.4f, var95=%.4f",
        beta_result["value"], beta_result["source"],
        volatility or 0, sharpe or 0, max_dd or 0, var_95 or 0,
    )

    return {
        "beta": beta_result,
        "market_risk": {
            "historical_volatility": volatility,
            "sharpe_ratio":          sharpe,
            "max_drawdown":          max_dd,
            "max_drawdown_start":    max_dd_start,
            "max_drawdown_end":      max_dd_end,
            "var_95_daily":          var_95,
            "annualized_return":     ann_return,
        },
        "warnings": warnings,
    }


def _empty_market_risk() -> dict:
    return {
        "historical_volatility": None,
        "sharpe_ratio":          None,
        "max_drawdown":          None,
        "max_drawdown_start":    None,
        "max_drawdown_end":      None,
        "var_95_daily":          None,
        "annualized_return":     None,
    }
