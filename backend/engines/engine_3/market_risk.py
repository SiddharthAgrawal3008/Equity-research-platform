"""
Engine 3 — Market Risk Module

Computes all price-based risk metrics from daily closing prices:
  beta, historical volatility, Sharpe ratio, max drawdown, VaR (95%).

Input keys read from financial_data:
    financial_data["market_data"]["historical_prices"]  — daily stock closing prices
    financial_data["market_data"]["sp500_prices"]       — daily S&P 500 prices (optional)
    financial_data["market_data"]["historical_dates"]   — ISO date strings, same length as prices (optional)
    financial_data["meta"]["sector"]                    — sector string, for beta fallback

Does NOT call any external API — all data must be pre-fetched by Engine 1.
"""

from __future__ import annotations

import logging

import numpy as np

from backend.engines.shared_config import (
    DEFAULT_BETA,
    RISK_FREE_RATE,
    SECTOR_AVG_BETAS,
    VAR_CONFIDENCE_LEVEL,
)

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
    market_data = financial_data.get("market_data", {})
    sector      = financial_data.get("meta", {}).get("sector", "")

    prices = market_data.get("historical_prices") or []
    sp500  = market_data.get("sp500_prices")       or []
    dates  = market_data.get("historical_dates")   or []

    warnings: list[str] = []

    if len(prices) < 2:
        warnings.append("No price history — all market risk metrics unavailable")
        return {
            "beta": {"value": _sector_beta(sector), "raw_beta": None, "source": "industry_fallback"},
            "market_risk": _empty_market_risk(),
            "warnings": warnings,
        }

    price_arr = np.array(prices, dtype=float)
    log_rets  = np.log(price_arr[1:] / price_arr[:-1])

    # ── Beta ──────────────────────────────────────────────────────────
    beta_result = _compute_beta(log_rets, sp500, sector, warnings)

    # ── Volatility (annualised) ───────────────────────────────────────
    volatility = None
    try:
        volatility = round(float(np.std(log_rets, ddof=1) * np.sqrt(252)), 4)
    except Exception as exc:
        warnings.append(f"Volatility failed: {exc}")

    # ── Annualised return (CAGR) ──────────────────────────────────────
    ann_return = None
    try:
        n = len(log_rets)
        ann_return = round(float((price_arr[-1] / price_arr[0]) ** (252 / n) - 1), 4)
    except Exception as exc:
        warnings.append(f"Annualised return failed: {exc}")

    # ── Sharpe ratio ──────────────────────────────────────────────────
    sharpe = None
    try:
        if ann_return is not None and volatility:
            sharpe = round((ann_return - RISK_FREE_RATE) / volatility, 4)
    except Exception as exc:
        warnings.append(f"Sharpe failed: {exc}")

    # ── Max drawdown ──────────────────────────────────────────────────
    max_dd = max_dd_start = max_dd_end = None
    try:
        peak   = np.maximum.accumulate(price_arr)
        dd     = (price_arr - peak) / peak
        max_dd = round(float(dd.min()), 4)
        trough_idx = int(dd.argmin())
        peak_idx   = int(price_arr[:trough_idx + 1].argmax())
        if dates:
            max_dd_start = dates[peak_idx][:7]
            max_dd_end   = dates[trough_idx][:7]
    except Exception as exc:
        warnings.append(f"Max drawdown failed: {exc}")

    # ── VaR 95% (historical simulation, daily) ───────────────────────
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


# ── Helpers ──────────────────────────────────────────────────────────────────

def _sector_beta(sector: str) -> float:
    return SECTOR_AVG_BETAS.get(sector.upper(), DEFAULT_BETA)


def _compute_beta(
    stock_rets: np.ndarray,
    sp500_prices: list,
    sector: str,
    warnings: list,
) -> dict:
    """OLS beta via numpy; Bloomberg-adjusted. Falls back to sector average."""
    try:
        if len(sp500_prices) >= 2:
            bench_arr  = np.array(sp500_prices, dtype=float)
            bench_rets = np.log(bench_arr[1:] / bench_arr[:-1])
            n = min(len(stock_rets), len(bench_rets))
            if n >= 252:
                s, b  = stock_rets[-n:], bench_rets[-n:]
                var_b = float(np.var(b, ddof=1))
                if var_b > 0:
                    raw  = float(np.cov(s, b)[0, 1] / var_b)
                    adj  = round(0.67 * raw + 0.33 * 1.0, 4)  # Bloomberg adjustment
                    return {"value": adj, "raw_beta": round(raw, 4), "source": "calculated"}
    except Exception as exc:
        warnings.append(f"Beta regression failed: {exc}")

    fb = _sector_beta(sector)
    warnings.append(f"Beta: sector average ({fb}) used — insufficient SP500 price data")
    return {"value": fb, "raw_beta": None, "source": "industry_fallback"}


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
