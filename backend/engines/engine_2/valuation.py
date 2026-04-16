"""
Engine 2 — Main Valuation Engine

Orchestrates five sequential valuation modules to produce a complete
company valuation analysis: DCF, relative valuation, sensitivity matrix,
summary verdict, and confidence scoring.

Never raises unhandled exceptions — every module is wrapped in try/except
and failures are communicated through status fields and warnings.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from statistics import median
from typing import Optional

from backend.pipeline.base_engine import BaseEngine
from backend.engines.shared_config import (
    PROJECTION_YEARS,
    TERMINAL_GROWTH_RATE,
    UNDERVALUED_THRESHOLD,
    OVERVALUED_THRESHOLD,
    MIXED_SIGNAL_DIVERGENCE,
    CONFIDENCE_DEDUCTIONS,
    CONFIDENCE_THRESHOLDS,
    DCF_EXTREME_HIGH,
    DCF_EXTREME_LOW,
    TV_WARNING_THRESHOLD,
    TV_CRITICAL_THRESHOLD,
)
from backend.engines.engine_2.modules import (
    forecast_revenue_and_fcf,
    compute_wacc,
    compute_dcf,
    compute_relative,
    compute_sensitivity,
)

logger = logging.getLogger(__name__)

MODEL_VERSION = "2.0.0"


# ── Failed-state template builders ─────────────────────────────────────


def _failed_dcf(reason: str) -> dict:
    return {
        "status": "failed",
        "intrinsic_value_per_share": None,
        "enterprise_value": None,
        "equity_value": None,
        "upside_pct": None,
        "wacc": None,
        "cost_of_equity": None,
        "cost_of_debt": None,
        "beta_used": None,
        "risk_free_rate": None,
        "equity_risk_premium": None,
        "debt_weight": None,
        "equity_weight": None,
        "projection_years": PROJECTION_YEARS,
        "projected_revenue": [],
        "projected_fcf": [],
        "projected_growth_rates": [],
        "projected_fcf_margins": [],
        "terminal_growth_rate": TERMINAL_GROWTH_RATE,
        "terminal_value": None,
        "terminal_value_pct": None,
        "_error": reason,
    }


def _failed_relative(reason: str) -> dict:
    return {
        "status": "failed",
        "peers": [],
        "num_peers": 0,
        "ev_ebitda_company": None,
        "ev_ebitda_peers_median": None,
        "ev_ebitda_implied_value": None,
        "pe_company": None,
        "pe_peers_median": None,
        "pe_implied_value": None,
        "pb_company": None,
        "pb_peers_median": None,
        "_implied_prices": [],
        "_error": reason,
    }


def _failed_sensitivity(reason: str) -> dict:
    return {
        "wacc_range": [],
        "growth_range": [],
        "value_matrix": [],
        "base_case_wacc_idx": 2,
        "base_case_growth_idx": 2,
        "_error": reason,
    }


# ── ValuationEngine ───────────────────────────────────────────────────


class ValuationEngine(BaseEngine):
    name = "engine_2"
    requires = ["financial_data"]
    produces = "valuation"

    def run(self, context: dict) -> dict:
        """Execute all valuation modules and return the assembled result.

        Reads context["financial_data"], writes to context["valuation"].
        """
        fd = context.get("financial_data", {})
        warnings: list[str] = []

        # ── Pre-flight checks ──────────────────────────────────────

        quality = fd.get("quality", {})
        if not quality.get("is_valid", False):
            errors = quality.get("errors", ["Data marked as invalid"])
            return self._assemble(
                _failed_dcf("Invalid input data"),
                _failed_relative("Invalid input data"),
                _failed_sensitivity("Invalid input data"),
                fd,
                warnings + [f"Skipped: {e}" for e in errors],
            )

        ttm = fd.get("ttm", {})
        meta = fd.get("meta", {})
        years_of_history = quality.get("years_of_history", 0)

        # Pre-revenue check
        ttm_revenue = ttm.get("revenue", 0) or 0
        if ttm_revenue <= 0:
            warnings.append("Pre-revenue company: all valuation modules skipped")
            return self._assemble(
                _failed_dcf("Pre-revenue company"),
                _failed_relative("Pre-revenue company"),
                _failed_sensitivity("Pre-revenue company"),
                fd,
                warnings,
            )

        # Determine if DCF is feasible
        ttm_ebitda = ttm.get("ebitda", 0) or 0
        run_dcf = ttm_ebitda > 0 and years_of_history >= 2

        if ttm_ebitda <= 0:
            warnings.append("Negative EBITDA: DCF skipped, using relative only")
        if years_of_history < 2:
            warnings.append(f"Only {years_of_history} year(s) of history: DCF skipped")

        # ── Module 1: Revenue & FCF Forecasting ────────────────────

        forecasts = None
        if run_dcf:
            try:
                forecasts = forecast_revenue_and_fcf(fd, warnings)
            except Exception as exc:
                logger.exception("Module 1 (forecast) failed")
                warnings.append(f"Forecast module failed: {exc}")
                run_dcf = False

        # ── Module 2: WACC ─────────────────────────────────────────

        wacc_result = None
        if run_dcf:
            try:
                wacc_result = compute_wacc(fd, warnings)
            except Exception as exc:
                logger.exception("Module 2 (WACC) failed")
                warnings.append(f"WACC module failed: {exc}")
                run_dcf = False

        # ── Module 3: DCF ──────────────────────────────────────────

        if run_dcf and forecasts and wacc_result:
            try:
                dcf_result = compute_dcf(forecasts, wacc_result, fd, warnings)
            except Exception as exc:
                logger.exception("Module 3 (DCF) failed")
                warnings.append(f"DCF module failed: {exc}")
                dcf_result = _failed_dcf(str(exc))
        else:
            dcf_result = _failed_dcf(
                "DCF skipped (negative EBITDA or insufficient history)"
            )

        # ── Module 4: Relative Valuation ───────────────────────────

        try:
            relative_result = compute_relative(fd, warnings)
        except Exception as exc:
            logger.exception("Module 4 (relative) failed")
            warnings.append(f"Relative valuation failed: {exc}")
            relative_result = _failed_relative(str(exc))

        # ── Module 5: Sensitivity Analysis ─────────────────────────

        if run_dcf and forecasts and wacc_result:
            try:
                sensitivity_result = compute_sensitivity(
                    forecasts, wacc_result["wacc"], fd, warnings
                )
            except Exception as exc:
                logger.exception("Module 5 (sensitivity) failed")
                warnings.append(f"Sensitivity analysis failed: {exc}")
                sensitivity_result = _failed_sensitivity(str(exc))
        else:
            sensitivity_result = _failed_sensitivity("DCF not available")

        # ── Propagate data quality warnings ────────────────────────

        data_warnings = quality.get("warnings", [])
        for w in data_warnings:
            warnings.append(f"Data quality: {w}")

        return self._assemble(
            dcf_result, relative_result, sensitivity_result, fd, warnings
        )

    # ── Summary & Confidence ───────────────────────────────────────

    def _assemble(
        self,
        dcf: dict,
        relative: dict,
        sensitivity: dict,
        fd: dict,
        warnings: list[str],
    ) -> dict:
        """Build the final output dict with summary and meta."""
        meta = fd.get("meta", {})
        quality = fd.get("quality", {})

        current_price = meta.get("current_price", 0)

        summary = self._build_summary(dcf, relative, current_price, quality, warnings)
        meta_out = self._build_meta(fd, warnings)

        return {
            "dcf": dcf,
            "relative": relative,
            "sensitivity": sensitivity,
            "summary": summary,
            "meta": meta_out,
        }

    def _build_summary(
        self,
        dcf: dict,
        relative: dict,
        current_price: float,
        quality: dict,
        warnings: list[str],
    ) -> dict:
        """Compute valuation verdict, confidence, and price ranges."""

        dcf_price = dcf.get("intrinsic_value_per_share")
        dcf_ok = dcf.get("status") == "success" and dcf_price is not None

        # Relative implied prices
        implied_prices = relative.get("_implied_prices", [])
        rel_ok = len(implied_prices) > 0

        # Price ranges
        if rel_ok:
            rel_low = min(implied_prices)
            rel_high = max(implied_prices)
            rel_mid = median(implied_prices)
        else:
            rel_low = rel_high = rel_mid = None

        # Overall range
        all_prices = []
        if dcf_ok:
            all_prices.append(dcf_price)
        all_prices.extend(implied_prices)

        if all_prices:
            range_low = min(all_prices)
            range_high = max(all_prices)
            range_mid = median(all_prices)
        else:
            range_low = range_high = range_mid = None

        # Upside (use DCF if available, else relative median)
        primary_price = dcf_price if dcf_ok else rel_mid
        if primary_price and current_price and current_price > 0:
            upside = (primary_price - current_price) / current_price
        else:
            upside = 0.0

        # ── Valuation Stance ───────────────────────────────────────

        verdict = self._determine_verdict(
            upside, dcf_price, rel_mid, current_price, dcf_ok, rel_ok, warnings
        )

        # ── Confidence ─────────────────────────────────────────────

        confidence = self._compute_confidence(dcf, relative, quality, warnings)

        return {
            "current_price": current_price,
            "dcf_value": dcf_price,
            "relative_value_low": rel_low,
            "relative_value_high": rel_high,
            "valuation_range_low": range_low,
            "valuation_range_mid": range_mid,
            "valuation_range_high": range_high,
            "upside_pct": upside,
            "verdict": verdict,
            "confidence": confidence,
        }

    def _determine_verdict(
        self,
        upside: float,
        dcf_price: Optional[float],
        rel_mid: Optional[float],
        current_price: float,
        dcf_ok: bool,
        rel_ok: bool,
        warnings: list[str],
    ) -> str:
        """Classify as Undervalued / Fairly Valued / Overvalued."""

        # Relative upside for cross-check
        if rel_ok and rel_mid and current_price > 0:
            rel_upside = (rel_mid - current_price) / current_price
        else:
            rel_upside = None

        # Check for DCF-vs-relative divergence
        if dcf_ok and rel_ok and dcf_price and rel_mid:
            divergence = abs(dcf_price - rel_mid) / max(rel_mid, 1)
            if divergence > MIXED_SIGNAL_DIVERGENCE:
                warnings.append(
                    f"DCF and relative values diverge by {divergence:.0%}"
                )

        # Primary verdict from upside
        if upside > UNDERVALUED_THRESHOLD:
            # Check if relative confirms
            if rel_upside is not None and rel_upside > 0:
                return "Undervalued"
            elif rel_upside is not None:
                return "Fairly Valued"  # DCF says up, relative disagrees
            return "Undervalued"
        elif upside < OVERVALUED_THRESHOLD:
            if rel_upside is not None and rel_upside < 0:
                return "Overvalued"
            elif rel_upside is not None:
                return "Fairly Valued"
            return "Overvalued"
        else:
            return "Fairly Valued"

    def _compute_confidence(
        self,
        dcf: dict,
        relative: dict,
        quality: dict,
        warnings: list[str],
    ) -> str:
        """Start at 1.0, apply deductions (negative values), return label."""

        score = 1.0
        ded = CONFIDENCE_DEDUCTIONS  # values are negative, e.g. -0.10

        # Sector average beta (always true in v1)
        score += ded.get("sector_avg_beta", 0)

        # History length
        years = quality.get("years_of_history", 0)
        if years < 3:
            score += ded.get("limited_history_3yr", 0)
        elif years < 5:
            score += ded.get("limited_history_5yr", 0)

        # Terminal value concentration
        tv_pct = dcf.get("terminal_value_pct") or 0
        if tv_pct > TV_CRITICAL_THRESHOLD:
            score += ded.get("tv_above_90pct", 0)
        elif tv_pct > TV_WARNING_THRESHOLD:
            score += ded.get("tv_above_85pct", 0)

        # DCF extreme result
        dcf_price = dcf.get("intrinsic_value_per_share")
        if dcf_price is not None and dcf.get("status") == "success":
            if any("extreme" in w.lower() for w in warnings):
                score += ded.get("dcf_extreme_result", 0)

        # Negative EBITDA or pre-revenue (DCF skipped)
        if dcf.get("status") == "failed":
            dcf_err = dcf.get("_error", "") or ""
            if "EBITDA" in dcf_err or "Pre-revenue" in dcf_err:
                score += ded.get("negative_ebitda", 0)

        # DCF and relative divergence
        implied_prices = relative.get("_implied_prices", [])
        if dcf_price and implied_prices:
            rel_median_val = median(implied_prices)
            if rel_median_val > 0:
                div = abs(dcf_price - rel_median_val) / rel_median_val
                if div > 0.50:
                    score += ded.get("dcf_relative_diverge", 0)

        # Data quality warnings
        data_warnings = quality.get("warnings", [])
        score += len(data_warnings) * ded.get("data_quality_warning", 0)

        # Tax rate anomaly
        if any("tax rate" in w.lower() for w in warnings):
            score += ded.get("anomalous_tax_rate", 0)

        # Clamp
        score = max(score, 0.0)

        # Map to label
        if score >= CONFIDENCE_THRESHOLDS["HIGH"]:
            return "High"
        elif score >= CONFIDENCE_THRESHOLDS["MEDIUM"]:
            return "Medium"
        elif score >= CONFIDENCE_THRESHOLDS["LOW"]:
            return "Low"
        else:
            return "Unreliable"

    def _build_meta(self, fd: dict, warnings: list[str]) -> dict:
        """Build the meta section of the output."""
        quality = fd.get("quality", {})
        data_warnings = quality.get("warnings", [])

        if quality.get("errors"):
            flag = "degraded"
        elif data_warnings:
            flag = "imputed"
        else:
            flag = "clean"

        return {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "model_version": MODEL_VERSION,
            "assumptions": {
                "projection_years": PROJECTION_YEARS,
                "terminal_growth_rate": TERMINAL_GROWTH_RATE,
                "beta_source": "sector_average",
            },
            "warnings": warnings,
            "data_quality_flag": flag,
        }
