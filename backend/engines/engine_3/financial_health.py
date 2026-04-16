"""
Engine 3 — Financial Health Module
====================================

Computes fundamental health metrics from financial statement data on the
shared context bus: Altman Z-score, interest coverage, debt/EBITDA,
current ratio, quick ratio, debt/equity, cash/debt, and earnings quality.

This module reads from ``financial_data["financials"]``,
``financial_data["meta"]``, and ``financial_data["quality"]`` — all
populated by Engine 1.  It does NOT call any external API.
"""

from __future__ import annotations

import logging

from backend.engines.shared_config import (
    ZSCORE_DISTRESS,
    ZSCORE_EXCLUDED_SECTORS,
    ZSCORE_SAFE,
)

logger = logging.getLogger(__name__)

_EXCLUDED_SECTORS_UPPER = {s.upper() for s in ZSCORE_EXCLUDED_SECTORS}


def _safe_div(numerator, denominator, fallback=None):
    """Divide safely, returning fallback if denominator is 0 or None."""
    if numerator is None or denominator is None or denominator == 0:
        return fallback
    return numerator / denominator


def _last_valid(series: list, years: list) -> tuple:
    """Return (value, year_index) of the last non-None entry, or (None, None)."""
    for i in range(len(series) - 1, -1, -1):
        if series[i] is not None:
            return series[i], i
    return None, None


def compute_financial_health(financial_data: dict) -> dict:
    """Compute fundamental health metrics from financial statement data.

    Args:
        financial_data: The full financial_data dict from the context bus.
                        Reads financials, meta, and quality sub-objects.

    Returns:
        Dict with financial_health metrics, financial_years_used, and
        warnings list.
    """
    financials = financial_data["financials"]
    meta = financial_data["meta"]
    quality = financial_data.get("quality", {})
    years = financial_data.get("years", [])

    sector = meta.get("sector", "").upper()
    market_cap = meta.get("market_cap", 0) or 0
    is_bank = quality.get("is_bank", False)
    is_reit = quality.get("is_reit", False)

    warnings: list[str] = []

    # Latest year index (last element of each list)
    n = len(years) if years else 0
    if n == 0:
        logger.warning("No financial years available")
        warnings.append("No financial years available — all metrics unavailable")
        return {
            "financial_health": {
                "altman_z_score": None,
                "altman_z_zone": "N/A",
                "interest_coverage": None,
                "debt_to_ebitda": None,
                "current_ratio": None,
                "quick_ratio": None,
                "debt_to_equity": None,
                "cash_to_debt": None,
                "earnings_quality": None,
            },
            "financial_years_used": 0,
            "warnings": warnings,
        }

    latest = n - 1

    # ── B. Altman Z-Score ─────────────────────────────────────────────
    altman_z_score = None
    altman_z_zone = "N/A"

    skip_zscore = (
        sector in _EXCLUDED_SECTORS_UPPER
        or is_bank
        or is_reit
    )

    if not skip_zscore:
        try:
            total_assets = financials["total_assets"][latest]
            total_liab = financials["total_liabilities"][latest]
            net_wc = financials["net_working_capital"][latest]
            retained = financials["retained_earnings"][latest]
            ebit = financials["ebit"][latest]
            revenue = financials["revenue"][latest]

            if not total_assets or not total_liab:
                raise ValueError("total_assets or total_liabilities is zero/None")

            x1 = _safe_div(net_wc, total_assets, 0)
            x2 = _safe_div(retained, total_assets, 0)
            x3 = _safe_div(ebit, total_assets, 0)
            x4 = _safe_div(market_cap, total_liab, 0)
            x5 = _safe_div(revenue, total_assets, 0)

            altman_z_score = round(
                1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5,
                4,
            )

            if altman_z_score > ZSCORE_SAFE:
                altman_z_zone = "Safe"
            elif altman_z_score < ZSCORE_DISTRESS:
                altman_z_zone = "Distress"
            else:
                altman_z_zone = "Grey"

        except Exception as exc:
            logger.warning("Altman Z-score computation failed: %s", exc)
            warnings.append(f"Altman Z-score computation failed: {exc}")
    else:
        reason = (
            "bank" if is_bank
            else "REIT" if is_reit
            else f"excluded sector ({sector})"
        )
        logger.info("Altman Z-score skipped: %s", reason)

    # ── C. Interest Coverage ──────────────────────────────────────────
    interest_coverage = None
    try:
        interest_series = financials["interest_expense"]
        interest_val, interest_idx = _last_valid(interest_series, years)
        if interest_val is None or interest_val == 0:
            warnings.append("No interest expense data available")
        else:
            ebit_for_coverage = financials["ebit"][interest_idx]
            interest_coverage = round(
                _safe_div(ebit_for_coverage, interest_val, 0), 4
            )
            if interest_idx != latest:
                warnings.append(
                    f"Interest coverage uses FY{years[interest_idx]} data "
                    f"(latest with interest expense)"
                )
    except Exception as exc:
        logger.warning("Interest coverage computation failed: %s", exc)
        warnings.append(f"Interest coverage computation failed: {exc}")

    # ── D. Debt/EBITDA ────────────────────────────────────────────────
    debt_to_ebitda = None
    try:
        ebitda_latest = financials["ebitda"][latest]
        debt_latest = financials["total_debt"][latest]
        if ebitda_latest is None or ebitda_latest <= 0:
            warnings.append(
                "EBITDA is non-positive — debt/EBITDA not meaningful"
            )
        else:
            debt_to_ebitda = round(_safe_div(debt_latest, ebitda_latest), 4)
    except Exception as exc:
        logger.warning("Debt/EBITDA computation failed: %s", exc)
        warnings.append(f"Debt/EBITDA computation failed: {exc}")

    # ── E. Current Ratio ──────────────────────────────────────────────
    current_ratio = None
    try:
        ca = financials["current_assets"][latest]
        cl = financials["current_liabilities"][latest]
        current_ratio = round(_safe_div(ca, cl), 4) if cl else None
    except Exception as exc:
        logger.warning("Current ratio computation failed: %s", exc)
        warnings.append(f"Current ratio computation failed: {exc}")

    # ── F. Quick Ratio ────────────────────────────────────────────────
    quick_ratio = None
    try:
        ca = financials["current_assets"][latest]
        cl = financials["current_liabilities"][latest]
        inv = financials["inventory"][latest]
        if inv is None:
            inv = 0
            warnings.append(
                "Inventory data missing — quick ratio approximate"
            )
        if cl:
            quick_ratio = round(_safe_div(ca - inv, cl), 4)
    except Exception as exc:
        logger.warning("Quick ratio computation failed: %s", exc)
        warnings.append(f"Quick ratio computation failed: {exc}")

    # ── G. Debt/Equity ────────────────────────────────────────────────
    debt_to_equity = None
    try:
        equity = financials["total_equity"][latest]
        debt = financials["total_debt"][latest]
        if equity is None or equity <= 0:
            warnings.append("Negative or zero equity — debt/equity not meaningful")
        else:
            debt_to_equity = round(_safe_div(debt, equity), 4)
    except Exception as exc:
        logger.warning("Debt/equity computation failed: %s", exc)
        warnings.append(f"Debt/equity computation failed: {exc}")

    # ── H. Cash/Debt ──────────────────────────────────────────────────
    cash_to_debt = None
    try:
        cash = financials["cash_and_equivalents"][latest]
        debt = financials["total_debt"][latest]
        if debt is None or debt == 0:
            pass  # No debt — not an error, just N/A
        else:
            cash_to_debt = round(_safe_div(cash, debt), 4)
    except Exception as exc:
        logger.warning("Cash/debt computation failed: %s", exc)
        warnings.append(f"Cash/debt computation failed: {exc}")

    # ── I. Earnings Quality ───────────────────────────────────────────
    earnings_quality = None
    try:
        ocf = financials["operating_cash_flow"][latest]
        ni = financials["net_income"][latest]
        if ni is None or ni <= 0:
            warnings.append(
                "Net income is non-positive — earnings quality ratio "
                "not meaningful"
            )
        else:
            earnings_quality = round(_safe_div(ocf, ni), 4)
    except Exception as exc:
        logger.warning("Earnings quality computation failed: %s", exc)
        warnings.append(f"Earnings quality computation failed: {exc}")

    logger.info(
        "Financial health computed: Z=%.2f (%s), ICR=%.2f, D/EBITDA=%.2f, "
        "CR=%.2f, QR=%.2f, D/E=%.2f, C/D=%.2f, EQ=%.2f",
        altman_z_score or 0,
        altman_z_zone,
        interest_coverage or 0,
        debt_to_ebitda or 0,
        current_ratio or 0,
        quick_ratio or 0,
        debt_to_equity or 0,
        cash_to_debt or 0,
        earnings_quality or 0,
    )

    return {
        "financial_health": {
            "altman_z_score": altman_z_score,
            "altman_z_zone": altman_z_zone,
            "interest_coverage": interest_coverage,
            "debt_to_ebitda": debt_to_ebitda,
            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "debt_to_equity": debt_to_equity,
            "cash_to_debt": cash_to_debt,
            "earnings_quality": earnings_quality,
        },
        "financial_years_used": n,
        "warnings": warnings,
    }
