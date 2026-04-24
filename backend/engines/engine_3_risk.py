"""
Engine 3 — Risk & Financial Health Engine (Owner: Siddharth)
============================================================

Orchestrator: delegates computation to the engine_3/ sub-modules and
maps their rich output to the risk_metrics bus schema.

Sub-modules:
    engine_3/market_risk.py      — beta, volatility, Sharpe, drawdown, VaR
    engine_3/financial_health.py — Altman Z, interest coverage, debt/EBITDA, ratios
"""

from backend.pipeline.base_engine import BaseEngine
from backend.engines.engine_3.market_risk import compute_market_risk
from backend.engines.engine_3.financial_health import compute_financial_health


class RiskEngine(BaseEngine):
    name = "engine_3"
    requires = ["financial_data"]
    produces = "risk_metrics"

    def run(self, context: dict) -> dict:
        fd = context.get("financial_data", {})

        mr = compute_market_risk(fd)
        fh = compute_financial_health(fd)

        return {
            "market_risk": {
                # Required fields
                "beta":              mr["beta"]["value"],
                "volatility_annual": mr["market_risk"]["historical_volatility"],
                "sharpe_ratio":      mr["market_risk"]["sharpe_ratio"],
                "max_drawdown":      mr["market_risk"]["max_drawdown"],
                "var_95":            mr["market_risk"]["var_95_daily"],
                # Richer fields
                "beta_source":        mr["beta"]["source"],
                "annualized_return":  mr["market_risk"]["annualized_return"],
                "max_drawdown_start": mr["market_risk"]["max_drawdown_start"],
                "max_drawdown_end":   mr["market_risk"]["max_drawdown_end"],
            },
            "financial_health": {
                # Required fields
                "altman_z_score":    fh["financial_health"]["altman_z_score"],
                "interest_coverage": fh["financial_health"]["interest_coverage"],
                "debt_to_ebitda":    fh["financial_health"]["debt_to_ebitda"],
                "current_ratio":     fh["financial_health"]["current_ratio"],
                # Richer fields
                "altman_z_zone":  fh["financial_health"]["altman_z_zone"],
                "quick_ratio":    fh["financial_health"]["quick_ratio"],
                "debt_to_equity": fh["financial_health"]["debt_to_equity"],
                "cash_to_debt":   fh["financial_health"]["cash_to_debt"],
                "earnings_quality": fh["financial_health"]["earnings_quality"],
            },
            "warnings": mr["warnings"] + fh["warnings"],
        }
