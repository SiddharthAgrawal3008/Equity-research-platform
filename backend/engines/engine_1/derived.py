"""
Engine 1 — Derived Metrics (Step 3)
=====================================

Computes margin ratios and trend flags from the standardized AnnualFinancials
and writes them into Engine1Output.margins and Engine1Output.trend_flags.

WHAT THIS MODULE DOES:
    - Computes per-year margin ratios (list[Optional[float]], aligned to years)
    - Computes trend flags via linear regression slope over last 3 non-None values
    - Writes results into the margins and trend_flags dicts on Engine1Output

WHAT THIS MODULE DOES NOT DO:
    - Does not compute growth rates, returns, efficiency, or TTM  (later steps)
    - Does not fetch any data                                      (Step 1)
    - Does not standardize fields                                  (Step 2)
"""

from __future__ import annotations

from typing import List, Optional

from backend.engines.shared_context import Engine1Output


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Return numerator / denominator, or None if either is None or denominator == 0."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _trend(values: list) -> str:
    """
    Fit a linear regression slope over the last 3 non-None values.

    Formula (x = [0, 1, 2]):
        slope = (sum(x*y) - n*mean_x*mean_y) / (sum(x^2) - n*mean_x^2)

    Returns:
        'improving'        — slope >  0.005
        'deteriorating'    — slope < -0.005
        'stable'           — slope in [-0.005, 0.005]
        'insufficient_data'— fewer than 3 non-None values available
    """
    recent = [v for v in values if v is not None][-3:]
    if len(recent) < 3:
        return "insufficient_data"

    n = 3
    x = [0, 1, 2]
    mean_x = sum(x) / n
    mean_y = sum(recent) / n

    numerator   = sum(xi * yi for xi, yi in zip(x, recent)) - n * mean_x * mean_y
    denominator = sum(xi ** 2 for xi in x) - n * mean_x ** 2

    if denominator == 0:
        return "stable"

    slope = numerator / denominator

    if slope > 0.005:
        return "improving"
    if slope < -0.005:
        return "deteriorating"
    return "stable"


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

def compute_derived(output: Engine1Output) -> Engine1Output:
    """
    Compute margins and trend flags and write them into output.margins
    and output.trend_flags. Modifies and returns the same object.

    Args:
        output: A populated Engine1Output from the standardizer (Step 2).
                All AnnualFinancials fields must be present.

    Returns:
        The same Engine1Output with margins and trend_flags populated.
    """
    f = output.financials

    # ── Margins (list[Optional[float]], aligned to years) ────────────────────
    # All divisions guarded by _safe_div — returns None if either input is None
    # or revenue is 0.
    gross_margin  = [_safe_div(gp, rev) for gp, rev in zip(f.gross_profit,             f.revenue)]
    ebit_margin   = [_safe_div(eb, rev) for eb, rev in zip(f.ebit,                      f.revenue)]
    ebitda_margin = [_safe_div(ed, rev) for ed, rev in zip(f.ebitda,                    f.revenue)]
    net_margin    = [_safe_div(ni, rev) for ni, rev in zip(f.net_income,                f.revenue)]
    ebt_margin    = [_safe_div(pt, rev) for pt, rev in zip(f.pre_tax_income,            f.revenue)]
    da_margin     = [_safe_div(da, rev) for da, rev in zip(f.depreciation_amortisation, f.revenue)]
    fcf_margin    = [_safe_div(fc, rev) for fc, rev in zip(f.free_cash_flow,            f.revenue)]

    output.margins = {
        "gross_margin":  gross_margin,
        "ebit_margin":   ebit_margin,
        "ebitda_margin": ebitda_margin,
        "net_margin":    net_margin,
        "fcf_margin":    fcf_margin,
    }

    # ── Growth rates ─────────────────────────────────────────────────────────
    n = len(f.years)

    def yoy(series):
        result = []
        for i in range(n - 1):
            a, b = series[i], series[i + 1]
            if a is None or b is None or a == 0:
                result.append(None)
            else:
                result.append((b - a) / abs(a))
        return result

    revenue_cagr = None
    if f.revenue[0] is not None and f.revenue[-1] is not None and n > 1:
        revenue_cagr = (f.revenue[-1] / f.revenue[0]) ** (1 / (n - 1)) - 1

    output.growth = {
        "revenue_yoy":    yoy(f.revenue),
        "ebitda_yoy":     yoy(f.ebitda),
        "fcf_yoy":        yoy(f.free_cash_flow),
        "net_income_yoy": yoy(f.net_income),
        "revenue_cagr":   revenue_cagr,
    }

    # ── Return metrics ───────────────────────────────────────────────────────
    roe, roa, roic = [], [], []
    for i in range(n):
        roe.append(_safe_div(f.net_income[i], f.total_equity[i]))
        roa.append(_safe_div(f.net_income[i], f.total_assets[i]))
        etr = _safe_div(f.tax_expense[i], f.pre_tax_income[i])
        if etr is None or not (0 < etr < 1):
            etr = 0.25
        nopat = f.ebit[i] * (1 - etr) if f.ebit[i] is not None else None
        ic = None
        if f.total_equity[i] is not None and f.total_debt[i] is not None and f.cash_and_equivalents[i] is not None:
            ic = f.total_equity[i] + f.total_debt[i] - f.cash_and_equivalents[i]
        roic.append(_safe_div(nopat, ic))

    output.returns = {"roe": roe, "roa": roa, "roic": roic}

    # ── Efficiency & leverage ratios ─────────────────────────────────────────
    ar_days, ap_days, inv_days, int_coverage, debt_ebitda = [], [], [], [], []
    for i in range(n):
        ar = _safe_div(f.accounts_receivable[i], f.revenue[i])
        ar_days.append(ar * 365 if ar is not None else None)
        ap = _safe_div(f.accounts_payable[i], f.cost_of_revenue[i])
        ap_days.append(ap * 365 if ap is not None else None)
        inv = _safe_div(f.inventory[i], f.cost_of_revenue[i])
        inv_days.append(inv * 365 if inv is not None else None)
        int_coverage.append(_safe_div(f.ebit[i], f.interest_expense[i]))
        debt_ebitda.append(_safe_div(f.total_debt[i], f.ebitda[i]))

    output.efficiency = {
        "ar_days":           ar_days,
        "ap_days":           ap_days,
        "inventory_days":    inv_days,
        "interest_coverage": int_coverage,
        "debt_to_ebitda":    debt_ebitda,
    }

    # ── Cost structure ────────────────────────────────────────────────────────
    output.cost_structure = {
        "rd_as_pct_revenue":  [_safe_div(f.research_and_development[i], f.revenue[i]) for i in range(n)],
        "sga_as_pct_revenue": [_safe_div(f.selling_general_admin[i],    f.revenue[i]) for i in range(n)],
        "da_as_pct_revenue":  [_safe_div(f.depreciation_amortisation[i], f.revenue[i]) for i in range(n)],
    }

    # ── Trend flags (single strings) ─────────────────────────────────────────
    # revenue_trend uses raw revenue values, not a margin ratio.
    # fcf_margin_trend uses the fcf_margin list computed above.
    output.trend_flags = {
        "gross_margin_trend": _trend(gross_margin),
        "ebit_margin_trend":  _trend(ebit_margin),
        "revenue_trend":      _trend(f.revenue),
        "fcf_margin_trend":   _trend(fcf_margin),
    }

    return output
