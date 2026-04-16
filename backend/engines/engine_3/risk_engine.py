"""
Engine 3 — Risk & Financial Health Engine
==========================================

Owner: Siddharth

Orchestrates the three Engine 3 modules (market_risk, financial_health,
red_flags), merges their outputs into the risk_metrics output contract,
and publishes to the bus.

Input:  context["financial_data"]  (from Engine 1)
Output: context["risk_metrics"]
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.engines.shared_config import (
    BENCHMARK_TICKER,
    BETA_FREQUENCY,
    BETA_LOOKBACK_YEARS,
    BETA_USE_ADJUSTED,
    DRAWDOWN_LOOKBACK_YEARS,
    RISK_FREE_RATE,
    SHARPE_LOOKBACK_YEARS,
    VAR_CONFIDENCE_LEVEL,
)
from backend.engines.engine_3.financial_health import compute_financial_health
from backend.engines.engine_3.market_risk import compute_market_risk
from backend.engines.engine_3.red_flags import detect_red_flags

logger = logging.getLogger(__name__)


def _empty_market_result() -> dict:
    """Return market risk result when the module fails completely."""
    return {
        "beta": {
            "value": None,
            "raw_beta": None,
            "source": "unavailable",
            "benchmark": BENCHMARK_TICKER,
            "lookback_years": BETA_LOOKBACK_YEARS,
            "frequency": BETA_FREQUENCY,
            "r_squared": None,
        },
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
        "warnings": [],
    }


def _empty_health_result() -> dict:
    """Return financial health result when the module fails completely."""
    return {
        "financial_health": {
            "altman_z_score": None,
            "altman_z_zone": None,
            "interest_coverage": None,
            "debt_to_ebitda": None,
            "current_ratio": None,
            "quick_ratio": None,
            "debt_to_equity": None,
            "cash_to_debt": None,
            "earnings_quality": None,
        },
        "financial_years_used": 0,
        "warnings": [],
    }


class RiskEngine:
    """Engine 3 — Risk & Financial Health Engine.

    Reads ``financial_data`` from the context bus, calls three modules
    (market_risk, financial_health, red_flags), and assembles the
    ``risk_metrics`` output contract.

    Attributes:
        name:     Engine identifier used by the orchestrator.
        requires: Bus keys this engine reads from.
        produces: Bus key this engine writes to.
    """

    name = "engine_3"
    requires = ["financial_data"]
    produces = "risk_metrics"

    def run(self, context: dict) -> dict:
        """Execute all risk & financial health computations.

        Args:
            context: The shared pipeline context dict.
                     Must contain ``context["financial_data"]``.

        Returns:
            The ``risk_metrics`` dict matching the output contract.
        """
        financial_data = context["financial_data"]
        all_warnings: list[str] = []

        # ── A. Market risk module ─────────────────────────────────────
        try:
            market_result = compute_market_risk(financial_data)
            all_warnings.extend(market_result.get("warnings", []))
        except Exception as exc:
            logger.exception("Market risk module failed")
            market_result = _empty_market_result()
            all_warnings.append(f"Market risk computation failed: {exc}")

        # ── B. Financial health module ────────────────────────────────
        try:
            health_result = compute_financial_health(financial_data)
            all_warnings.extend(health_result.get("warnings", []))
        except Exception as exc:
            logger.exception("Financial health module failed")
            health_result = _empty_health_result()
            all_warnings.append(f"Financial health computation failed: {exc}")

        # ── C. Red flags module ───────────────────────────────────────
        z_score = None
        fh = health_result.get("financial_health")
        if fh:
            z_score = fh.get("altman_z_score")

        try:
            red_flags = detect_red_flags(financial_data, altman_z_score=z_score)
        except Exception as exc:
            logger.exception("Red flags module failed")
            red_flags = []
            all_warnings.append(f"Red flag detection failed: {exc}")

        # ── D. Assemble output contract ───────────────────────────────
        return {
            "beta": market_result["beta"],
            "market_risk": market_result["market_risk"],
            "financial_health": health_result["financial_health"],
            "red_flags": red_flags,
            "meta": {
                "computed_at": datetime.now(timezone.utc).isoformat(),
                "config_used": {
                    "risk_free_rate": RISK_FREE_RATE,
                    "beta_lookback": BETA_LOOKBACK_YEARS,
                    "beta_frequency": BETA_FREQUENCY,
                    "beta_adjusted": BETA_USE_ADJUSTED,
                    "benchmark": BENCHMARK_TICKER,
                    "var_confidence": VAR_CONFIDENCE_LEVEL,
                    "drawdown_lookback": DRAWDOWN_LOOKBACK_YEARS,
                    "sharpe_lookback": SHARPE_LOOKBACK_YEARS,
                },
                "price_data_start": market_result.get("price_data_start"),
                "price_data_end": market_result.get("price_data_end"),
                "warnings": all_warnings,
                "financial_years_used": health_result.get(
                    "financial_years_used", 0
                ),
            },
        }
