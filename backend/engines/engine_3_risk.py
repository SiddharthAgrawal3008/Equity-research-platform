"""
Engine 3 — Risk & Financial Health Engine (Owner: Siddharth)
============================================================

Input:  financial_data (from bus)
Output: risk_metrics (to bus)

Market risk metrics (beta, vol, Sharpe, drawdown, VaR) are read from
financial_data["derived"] where Engine 1 stores pre-computed price stats.
When those fields are absent, the engine falls back gracefully and records
warnings rather than raising.

Financial health metrics (Z-score, coverage, leverage, liquidity) are
computed directly from balance sheet and income statement data.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from backend.pipeline.base_engine import BaseEngine
from backend.engines.shared_config import (
    RISK_FREE_RATE,
    SECTOR_AVG_BETAS,
    DEFAULT_BETA,
    ZSCORE_SAFE,
    ZSCORE_DISTRESS,
    ZSCORE_EXCLUDED_SECTORS,
)

logger = logging.getLogger(__name__)

MODEL_VERSION = "3.0.0"

_ZSCORE_EXCLUDED_UPPER: frozenset = frozenset(
    s.upper() for s in ZSCORE_EXCLUDED_SECTORS
)


# ── Module-level helpers ───────────────────────────────────────────────


def _safe_divide(
    a: Optional[float],
    b: Optional[float],
    fallback: Optional[float] = None,
) -> Optional[float]:
    if a is None or b is None or b == 0:
        return fallback
    return a / b


def _last_valid(series: list) -> Optional[float]:
    if not series:
        return None
    for val in reversed(series):
        if val is not None:
            return float(val)
    return None


# ── RiskEngine ─────────────────────────────────────────────────────────


class RiskEngine(BaseEngine):
    name = "engine_3"
    requires = ["financial_data"]
    produces = "risk_metrics"

    def run(self, context: dict) -> dict:
        fd = context.get("financial_data", {})
        warnings: list[str] = []

        quality = fd.get("quality", {})
        if not quality.get("is_valid", False):
            errors = quality.get("errors", ["Data marked as invalid"])
            return self._assemble(
                self._failed_market_risk("Invalid input data"),
                self._failed_financial_health("Invalid input data"),
                [],
                fd,
                warnings + [f"Skipped: {e}" for e in errors],
            )

        market_risk = self._compute_market_risk(fd, warnings)
        financial_health = self._compute_financial_health(fd, warnings)
        red_flags = self._generate_red_flags(market_risk, financial_health)

        return self._assemble(market_risk, financial_health, red_flags, fd, warnings)

    # ── Failed-state builders ──────────────────────────────────────────

    def _failed_market_risk(self, reason: str) -> dict:
        return {
            "beta": None,
            "beta_source": None,
            "volatility_annual": None,
            "sharpe_ratio": None,
            "max_drawdown": None,
            "max_drawdown_start": None,
            "max_drawdown_end": None,
            "var_95": None,
            "_error": reason,
        }

    def _failed_financial_health(self, reason: str) -> dict:
        return {
            "altman_z_score": None,
            "altman_z_zone": "N/A",
            "interest_coverage": None,
            "debt_to_ebitda": None,
            "current_ratio": None,
            "quick_ratio": None,
            "_error": reason,
        }

    # ── Module A: Market Risk ──────────────────────────────────────────

    def _compute_market_risk(self, fd: dict, warnings: list[str]) -> dict:
        derived = fd.get("derived", {})
        meta = fd.get("meta", {})
        sector = (meta.get("sector") or "").upper()

        # Beta: use Engine 1's calculated value; fall back to sector average
        beta = derived.get("beta")
        if beta is not None:
            beta_source = "calculated"
        else:
            beta = float(SECTOR_AVG_BETAS.get(sector, DEFAULT_BETA))
            beta_source = "sector_average"
            warnings.append(
                f"Beta not provided by Engine 1 — using sector average ({beta:.2f})"
            )

        # Annual volatility
        volatility = derived.get("price_volatility_annual")
        if volatility is None:
            volatility = 0.0
            warnings.append(
                "Annual price volatility not provided by Engine 1 — defaulting to 0.0"
            )

        # Sharpe ratio
        annual_return = derived.get("annual_return_1yr")
        if annual_return is not None and float(volatility) > 0:
            sharpe_ratio = round(
                (float(annual_return) - RISK_FREE_RATE) / float(volatility), 4
            )
        else:
            sharpe_ratio = None
            if annual_return is None:
                warnings.append(
                    "Annual return not provided by Engine 1 — Sharpe ratio not computed"
                )

        # Max drawdown
        max_drawdown = derived.get("max_drawdown")
        max_drawdown_start = derived.get("max_drawdown_start")
        max_drawdown_end = derived.get("max_drawdown_end")
        if max_drawdown is None:
            warnings.append("Max drawdown not provided by Engine 1")

        # VaR (95 %)
        var_95 = derived.get("var_95")
        if var_95 is None:
            warnings.append("VaR (95%) not provided by Engine 1")

        return {
            "beta": float(beta),
            "beta_source": beta_source,
            "volatility_annual": float(volatility),
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "max_drawdown_start": max_drawdown_start,
            "max_drawdown_end": max_drawdown_end,
            "var_95": var_95,
        }

    # ── Module B: Financial Health ─────────────────────────────────────

    def _compute_financial_health(self, fd: dict, warnings: list[str]) -> dict:
        financials = fd.get("financials", {})
        ttm = fd.get("ttm", {})
        meta = fd.get("meta", {})
        sector = (meta.get("sector") or "").upper()

        # Balance sheet — last valid observation from annual series
        total_assets = _last_valid(financials.get("total_assets", []))
        total_liabilities = _last_valid(financials.get("total_liabilities", []))
        current_assets = _last_valid(financials.get("current_assets", []))
        current_liabilities = _last_valid(financials.get("current_liabilities", []))
        retained_earnings = _last_valid(financials.get("retained_earnings", []))
        inventory = _last_valid(financials.get("inventory", [])) or 0.0
        total_debt = _last_valid(financials.get("total_debt", []))

        market_cap = meta.get("market_cap")

        # Income (TTM preferred)
        ebit = ttm.get("ebit")
        ebitda = ttm.get("ebitda")
        revenue = ttm.get("revenue")

        # Interest expense: TTM first, then last valid from annual series
        interest_expense = ttm.get("interest_expense")
        if interest_expense is None:
            interest_expense = _last_valid(financials.get("interest_expense", []))

        # ── Altman Z-Score ─────────────────────────────────────────────
        if sector in _ZSCORE_EXCLUDED_UPPER:
            altman_z_score = None
            altman_z_zone = "N/A"
            warnings.append(f"Altman Z-Score not applicable for {sector} sector")
        else:
            altman_z_score = self._compute_altman_z(
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                current_assets=current_assets,
                current_liabilities=current_liabilities,
                retained_earnings=retained_earnings,
                ebit=ebit,
                market_cap=market_cap,
                revenue=revenue,
                warnings=warnings,
            )
            if altman_z_score is not None:
                if altman_z_score >= ZSCORE_SAFE:
                    altman_z_zone = "Safe"
                elif altman_z_score >= ZSCORE_DISTRESS:
                    altman_z_zone = "Grey"
                else:
                    altman_z_zone = "Distress"
            else:
                altman_z_zone = "N/A"

        # ── Interest Coverage ──────────────────────────────────────────
        interest_coverage = _safe_divide(ebit, interest_expense)
        if interest_coverage is None:
            warnings.append(
                "Interest coverage not computable — interest expense unavailable or zero"
            )

        # ── Debt to EBITDA ─────────────────────────────────────────────
        if ebitda is not None and ebitda > 0:
            debt_to_ebitda = _safe_divide(total_debt, ebitda)
        else:
            debt_to_ebitda = None
            if ebitda is not None and ebitda <= 0:
                warnings.append("Debt/EBITDA not computed — negative EBITDA")

        # ── Current Ratio ──────────────────────────────────────────────
        current_ratio = _safe_divide(current_assets, current_liabilities)
        if current_ratio is None:
            warnings.append(
                "Current ratio not computable — missing balance sheet data"
            )

        # ── Quick Ratio ────────────────────────────────────────────────
        if (
            current_assets is not None
            and current_liabilities is not None
            and current_liabilities > 0
        ):
            quick_ratio = (current_assets - inventory) / current_liabilities
        else:
            quick_ratio = None

        def _r(val: Optional[float]) -> Optional[float]:
            return round(val, 2) if val is not None else None

        return {
            "altman_z_score": _r(altman_z_score),
            "altman_z_zone": altman_z_zone,
            "interest_coverage": _r(interest_coverage),
            "debt_to_ebitda": _r(debt_to_ebitda),
            "current_ratio": _r(current_ratio),
            "quick_ratio": _r(quick_ratio),
        }

    def _compute_altman_z(
        self,
        total_assets: Optional[float],
        total_liabilities: Optional[float],
        current_assets: Optional[float],
        current_liabilities: Optional[float],
        retained_earnings: Optional[float],
        ebit: Optional[float],
        market_cap: Optional[float],
        revenue: Optional[float],
        warnings: list[str],
    ) -> Optional[float]:
        """
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        X1 = working capital / total assets
        X2 = retained earnings / total assets
        X3 = EBIT / total assets
        X4 = market cap / total liabilities
        X5 = revenue / total assets
        """
        if not total_assets or total_assets <= 0:
            warnings.append("Altman Z-Score not computed — total assets unavailable")
            return None

        working_capital = (
            (current_assets - current_liabilities)
            if current_assets is not None and current_liabilities is not None
            else None
        )

        x1 = _safe_divide(working_capital, total_assets, 0.0)
        x2 = _safe_divide(retained_earnings, total_assets, 0.0)
        x3 = _safe_divide(ebit, total_assets, 0.0)
        x4 = _safe_divide(market_cap, total_liabilities, 0.0)
        x5 = _safe_divide(revenue, total_assets, 0.0)

        return 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

    # ── Module C: Red Flags ────────────────────────────────────────────

    def _generate_red_flags(
        self,
        market_risk: dict,
        financial_health: dict,
    ) -> list[str]:
        flags: list[str] = []

        z = financial_health.get("altman_z_score")
        if z is not None and z < ZSCORE_DISTRESS:
            flags.append(f"Altman Z-Score in distress zone (Z={z:.2f})")

        coverage = financial_health.get("interest_coverage")
        if coverage is not None and coverage < 1.5:
            flags.append(
                f"Interest coverage below 1.5x ({coverage:.1f}x) — debt service risk"
            )

        d2e = financial_health.get("debt_to_ebitda")
        if d2e is not None and d2e > 5.0:
            flags.append(f"Debt/EBITDA above 5x ({d2e:.1f}x) — elevated leverage")

        mdd = market_risk.get("max_drawdown")
        if mdd is not None and mdd < -0.50:
            flags.append(f"Maximum drawdown exceeded 50% ({mdd:.0%})")

        beta = market_risk.get("beta")
        if beta is not None and beta > 1.5:
            flags.append(
                f"High beta ({beta:.2f}) — above-average market sensitivity"
            )

        cr = financial_health.get("current_ratio")
        if cr is not None and cr < 1.0:
            flags.append(
                f"Current ratio below 1.0 ({cr:.2f}) — potential liquidity concern"
            )

        return flags

    # ── Assembly ───────────────────────────────────────────────────────

    def _assemble(
        self,
        market_risk: dict,
        financial_health: dict,
        red_flags: list[str],
        fd: dict,
        warnings: list[str],
    ) -> dict:
        quality = fd.get("quality", {})
        data_warnings = quality.get("warnings", [])
        for w in data_warnings:
            warnings.append(f"Data quality: {w}")

        if quality.get("errors"):
            flag = "degraded"
        elif data_warnings:
            flag = "imputed"
        else:
            flag = "clean"

        return {
            "market_risk": market_risk,
            "financial_health": financial_health,
            "red_flags": red_flags,
            "meta": {
                "computed_at": datetime.now(timezone.utc).isoformat(),
                "model_version": MODEL_VERSION,
                "warnings": warnings,
                "data_quality_flag": flag,
            },
        }
