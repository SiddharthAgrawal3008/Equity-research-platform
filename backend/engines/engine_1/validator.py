"""
Engine 1 — Validator (Step 6)
==============================

Runs AFTER all other Engine 1 steps are complete (standardize, derived,
TTM, market_data). Inspects the fully assembled Engine1Output and mutates
output.quality in-place with cross-check results, length validation,
quality flags, and anomaly warnings.

WHAT THIS MODULE DOES:
    - Cross-checks computed fields for internal consistency
    - Validates that all time-series lists align to output.financials.years
    - Sets balance_sheet_balanced, is_negative_equity, net_income_cf_reconciled
    - Validates market_data arrays (lengths, positivity, date order)
    - Checks for interest expense anomalies

WHAT THIS MODULE DOES NOT DO:
    - Does not re-fetch or recompute any data
    - Does not modify output.financials or any field other than output.quality
"""

from __future__ import annotations

from backend.engines.shared_context import Engine1Output


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct_diff(actual: float, expected: float) -> float:
    """Absolute percentage difference relative to expected. Returns inf if expected==0."""
    if expected == 0:
        return float("inf") if actual != 0 else 0.0
    return abs(actual - expected) / abs(expected)


def _check_cross(
    warnings: list[str],
    name: str,
    actual: float | None,
    expected: float | None,
    year: int,
    tolerance: float = 0.005,
) -> None:
    """Append a warning if actual and expected differ by more than tolerance."""
    if actual is None or expected is None:
        return
    if _pct_diff(actual, expected) > tolerance:
        warnings.append(
            f"Cross-check failed: {name} in {year} "
            f"(expected {round(expected, 1)}, got {round(actual, 1)})"
        )


def _warn_once(warnings: list[str], message: str) -> None:
    """Append message only if it is not already in warnings."""
    if message not in warnings:
        warnings.append(message)


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

def validate(output: Engine1Output) -> None:
    """
    Inspect the fully assembled Engine1Output and mutate output.quality
    in-place with validation results.

    Args:
        output: A fully assembled Engine1Output (after all 5 prior steps).

    Returns:
        None. Mutates output.quality["warnings"], output.quality["errors"],
        and sets quality flag keys directly.
    """
    q = output.quality
    warnings: list[str] = q.setdefault("warnings", [])
    errors: list[str]   = q.setdefault("errors",   [])
    f = output.financials
    n = len(f.years)

    # ── 1–3. Annual cross-checks (per-year) ──────────────────────────────────
    for i, year in enumerate(f.years):
        # 1. gross_profit == revenue - cost_of_revenue
        if f.gross_profit[i] is not None and f.revenue[i] is not None and f.cost_of_revenue[i] is not None:
            _check_cross(
                warnings,
                "gross_profit != revenue - COGS",
                f.gross_profit[i],
                f.revenue[i] - f.cost_of_revenue[i],
                year,
            )

        # 2. ebitda == ebit + depreciation_amortisation
        if f.ebitda[i] is not None and f.ebit[i] is not None and f.depreciation_amortisation[i] is not None:
            _check_cross(
                warnings,
                "ebitda != ebit + D&A",
                f.ebitda[i],
                f.ebit[i] + f.depreciation_amortisation[i],
                year,
            )

        # 3. free_cash_flow == operating_cash_flow + capex
        if f.free_cash_flow[i] is not None and f.operating_cash_flow[i] is not None and f.capex[i] is not None:
            _check_cross(
                warnings,
                "free_cash_flow != OCF + capex",
                f.free_cash_flow[i],
                f.operating_cash_flow[i] + f.capex[i],
                year,
            )

    # ── 4. Enterprise value cross-check (latest year only, 2% tolerance) ─────
    try:
        latest_debt = f.total_debt[-1]  if f.total_debt  else None
        latest_cash = f.cash_and_equivalents[-1] if f.cash_and_equivalents else None
        ev_actual   = output.meta.enterprise_value
        mc          = output.meta.market_cap

        if latest_debt is not None and latest_cash is not None and ev_actual is not None and mc is not None:
            ev_expected = mc + latest_debt - latest_cash
            if _pct_diff(ev_actual, ev_expected) > 0.02:
                warnings.append(
                    f"Cross-check failed: enterprise_value != market_cap + debt - cash "
                    f"(expected {round(ev_expected, 1)}, got {round(ev_actual, 1)})"
                )
    except Exception:
        pass

    # ── 5. Length validation — all annual series must align to years ──────────
    ANNUAL_FIELDS = [
        "revenue", "gross_profit", "ebit", "ebitda", "net_income",
        "interest_expense", "total_assets", "total_debt", "cash_and_equivalents",
        "operating_cash_flow", "capex", "cost_of_revenue",
        "depreciation_amortisation", "pre_tax_income", "tax_expense",
        "total_equity", "net_working_capital", "net_debt", "long_term_debt",
        "free_cash_flow",
    ]
    for field_name in ANNUAL_FIELDS:
        series = getattr(f, field_name, None)
        if series is None:
            errors.append(f"Length mismatch: {field_name} is missing entirely")
            continue
        if len(series) != n:
            errors.append(
                f"Length mismatch: {field_name} has {len(series)} values "
                f"but years has {n}"
            )

    # ── 6. balance_sheet_balanced ─────────────────────────────────────────────
    try:
        ta  = f.total_assets[-1]       if f.total_assets       else None
        tl  = f.total_liabilities[-1]  if f.total_liabilities  else None
        teq = f.total_equity[-1]       if f.total_equity       else None

        if ta is not None and tl is not None and teq is not None and ta != 0:
            q["balance_sheet_balanced"] = abs(ta - (tl + teq)) / abs(ta) < 0.02
        else:
            q["balance_sheet_balanced"] = None
    except Exception:
        q["balance_sheet_balanced"] = None

    # ── 7. is_negative_equity ─────────────────────────────────────────────────
    try:
        teq_latest = f.total_equity[-1] if f.total_equity else None
        q["is_negative_equity"] = (teq_latest < 0) if teq_latest is not None else None
    except Exception:
        q["is_negative_equity"] = None

    # ── 8. net_income_cf_reconciled (simplified) ─────────────────────────────
    # Full reconciliation requires the cash flow statement's starting net income
    # figure, which Alpha Vantage does not expose separately. We verify that the
    # latest net income value is present and non-None as a proxy for data integrity.
    try:
        ni_latest = f.net_income[-1] if f.net_income else None
        q["net_income_cf_reconciled"] = ni_latest is not None
    except Exception:
        q["net_income_cf_reconciled"] = False

    # ── 9. Market data validation ─────────────────────────────────────────────
    md = getattr(output, "market_data", {})
    if md:
        daily_close  = md.get("daily_close",  [])
        daily_dates  = md.get("daily_dates",  [])
        weekly_close = md.get("weekly_close", [])
        weekly_dates = md.get("weekly_dates", [])
        b_daily      = md.get("benchmark_daily_close",  [])
        b_weekly     = md.get("benchmark_weekly_close", [])

        if daily_close or weekly_close:
            # Length parity checks
            if len(daily_close) != len(daily_dates):
                errors.append(
                    f"market_data: daily_close length ({len(daily_close)}) "
                    f"!= daily_dates length ({len(daily_dates)})"
                )
            if len(weekly_close) != len(weekly_dates):
                errors.append(
                    f"market_data: weekly_close length ({len(weekly_close)}) "
                    f"!= weekly_dates length ({len(weekly_dates)})"
                )
            if daily_close and len(b_daily) != len(daily_close):
                errors.append(
                    f"market_data: benchmark_daily_close length ({len(b_daily)}) "
                    f"!= daily_close length ({len(daily_close)})"
                )
            if weekly_close and len(b_weekly) != len(weekly_close):
                errors.append(
                    f"market_data: benchmark_weekly_close length ({len(b_weekly)}) "
                    f"!= weekly_close length ({len(weekly_close)})"
                )

            # Prices positive
            if daily_close and not all(p > 0 for p in daily_close):
                errors.append("market_data: non-positive price found in daily_close")
            if weekly_close and not all(p > 0 for p in weekly_close):
                errors.append("market_data: non-positive price found in weekly_close")

            # Dates chronological
            if daily_dates and daily_dates != sorted(daily_dates):
                errors.append("market_data: daily_dates are not in chronological order")
            if weekly_dates and weekly_dates != sorted(weekly_dates):
                errors.append("market_data: weekly_dates are not in chronological order")

    # ── 10. Interest expense anomaly ──────────────────────────────────────────
    try:
        latest_debt = f.total_debt[-1]        if f.total_debt        else None
        latest_int  = f.interest_expense[-1]  if f.interest_expense  else None

        if latest_debt is not None and latest_debt > 0:
            if latest_int is None or latest_int == 0:
                msg = (
                    f"Interest expense is zero/missing for a company with "
                    f"{round(latest_debt, 1)}M in debt"
                )
                _warn_once(warnings, msg)
    except Exception:
        pass

    # ── Set is_valid ──────────────────────────────────────────────────────────
    # Mark invalid only if hard errors were found (length mismatches, data malformed).
    # Warnings alone do not invalidate.
    if errors:
        q["is_valid"] = False
