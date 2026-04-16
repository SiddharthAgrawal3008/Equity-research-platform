"""
Engine 2 — Valuation Modules

Five sequential computation modules:
    Module 1: Revenue & FCF Forecasting
    Module 2: WACC Computation
    Module 3: DCF Valuation
    Module 4: Relative Valuation
    Module 5: Sensitivity Analysis
"""

from __future__ import annotations

from statistics import median
from typing import Optional

from backend.engines.financial_analysis import safe_divide
from backend.engines.shared_config import (
    RISK_FREE_RATE,
    EQUITY_RISK_PREMIUM,
    TERMINAL_GROWTH_RATE,
    PROJECTION_YEARS,
    US_STATUTORY_TAX_RATE,
    SECTOR_AVG_BETAS,
    SECTOR_AVG_GROWTH_RATES,
    SECTOR_AVG_MULTIPLES,
    DEFAULT_BETA,
    DEFAULT_SECTOR_GROWTH,
    MAX_STARTING_GROWTH,
    MIN_STARTING_GROWTH,
    MAX_TARGET_GROWTH,
    MAX_COST_OF_DEBT,
    WACC_FLOOR,
    WACC_CEILING,
    TV_WARNING_THRESHOLD,
    TV_CRITICAL_THRESHOLD,
    DCF_EXTREME_HIGH,
    DCF_EXTREME_LOW,
    SENSITIVITY_WACC_STEP,
    SENSITIVITY_WACC_POINTS,
    SENSITIVITY_TGR_STEP,
    SENSITIVITY_TGR_POINTS,
)


# ── Helper Utilities ───────────────────────────────────────────────────


def _safe_mean(values: list) -> Optional[float]:
    """Arithmetic mean ignoring None values. Returns None if empty."""
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


def _last_valid(series: list) -> Optional[float]:
    """Return last non-None value from a list, or None."""
    for v in reversed(series):
        if v is not None:
            return v
    return None


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ── Module 1: Revenue & FCF Forecasting ───────────────────────────────


def forecast_revenue_and_fcf(fd: dict, warnings: list[str]) -> dict:
    """Project 5-year revenue, EBITDA, and free cash flow to firm.

    Uses mean-reversion growth decay for revenue and EBITDA margins,
    then derives FCFF from NOPAT + D&A + CapEx - delta NWC.
    """
    meta = fd["meta"]
    financials = fd["financials"]
    derived = fd["derived"]
    ttm = fd["ttm"]

    sector = meta.get("sector", "").upper()

    # ── Revenue growth projection ──────────────────────────────────

    revenue_yoy = derived.get("revenue_yoy", [])

    # Step 1: starting growth rate
    if len(revenue_yoy) >= 1:
        g_start = revenue_yoy[-1]
    else:
        g_start = derived.get("revenue_cagr", DEFAULT_SECTOR_GROWTH)

    if g_start is None:
        g_start = DEFAULT_SECTOR_GROWTH
    g_start = _clamp(g_start, MIN_STARTING_GROWTH, MAX_STARTING_GROWTH)

    # Step 2: target growth rate (sector average)
    g_target = SECTOR_AVG_GROWTH_RATES.get(sector, DEFAULT_SECTOR_GROWTH)
    g_target = _clamp(g_target, TERMINAL_GROWTH_RATE, MAX_TARGET_GROWTH)

    # If current growth is below target, don't artificially accelerate
    if g_start < g_target:
        g_target = g_start

    # Step 3: mean-reversion decay  g(t) = g_start + (g_target - g_start) * (t / N)
    projected_growth_rates = []
    for t in range(1, PROJECTION_YEARS + 1):
        g_t = g_start + (g_target - g_start) * (t / PROJECTION_YEARS)
        projected_growth_rates.append(g_t)

    # Step 4: project revenue
    base_revenue = ttm["revenue"]
    projected_revenue = []
    prev_rev = base_revenue
    for g_t in projected_growth_rates:
        rev = prev_rev * (1 + g_t)
        projected_revenue.append(rev)
        prev_rev = rev

    # ── EBITDA margin projection ───────────────────────────────────

    ebitda_margins = derived.get("ebitda_margin", [])
    margin_trend = derived.get("ebitda_margin_trend", "stable")

    margin_start = ebitda_margins[-1] if ebitda_margins else 0.20

    if margin_trend == "improving":
        margin_target = margin_start  # hold at current level
    elif margin_trend == "deteriorating":
        margin_target = _safe_mean(ebitda_margins[-5:]) or margin_start
    else:
        margin_target = _safe_mean(ebitda_margins[-3:]) or margin_start

    projected_margins = []
    projected_ebitda = []
    for t in range(1, PROJECTION_YEARS + 1):
        m_t = margin_start + (margin_target - margin_start) * (t / PROJECTION_YEARS)
        projected_margins.append(m_t)
        projected_ebitda.append(projected_revenue[t - 1] * m_t)

    # ── FCFF projection ────────────────────────────────────────────

    # Tax rate
    tax_rates = derived.get("effective_tax_rate", [])
    tax_rate = tax_rates[-1] if tax_rates and tax_rates[-1] is not None else None
    if tax_rate is None or tax_rate < 0 or tax_rate > 0.5:
        tax_rate = US_STATUTORY_TAX_RATE
        warnings.append("Used statutory tax rate (effective rate unavailable or anomalous)")

    # D&A ratio (avg of last 3 years)
    da_series = financials.get("depreciation_amortisation", [])
    rev_series = financials.get("revenue", [])
    da_ratios = []
    for da_val, rev_val in zip(da_series[-3:], rev_series[-3:]):
        r = safe_divide(da_val, rev_val)
        if r is not None:
            da_ratios.append(r)
    da_ratio = _safe_mean(da_ratios) or 0.03

    # CapEx ratio (avg of last 3 years) — capex values are negative
    capex_series = financials.get("capital_expenditures", [])
    capex_ratios = []
    for capex_val, rev_val in zip(capex_series[-3:], rev_series[-3:]):
        r = safe_divide(capex_val, rev_val)
        if r is not None:
            capex_ratios.append(r)
    capex_ratio = _safe_mean(capex_ratios) or -0.03

    # NWC change ratio (avg of last 3 delta_NWC / delta_revenue)
    nwc_series = financials.get("net_working_capital", [])
    nwc_ratios = []
    for i in range(max(0, len(nwc_series) - 3), len(nwc_series)):
        if i == 0:
            continue
        delta_nwc = nwc_series[i] - nwc_series[i - 1]
        delta_rev = rev_series[i] - rev_series[i - 1]
        r = safe_divide(delta_nwc, delta_rev)
        if r is not None:
            nwc_ratios.append(r)
    nwc_ratio = _safe_mean(nwc_ratios) or 0.0

    projected_fcf = []
    projected_fcf_margins = []
    prev_revenue_for_nwc = base_revenue
    for t in range(PROJECTION_YEARS):
        nopat = projected_ebitda[t] * (1 - tax_rate)
        da = projected_revenue[t] * da_ratio
        capex = projected_revenue[t] * capex_ratio  # negative
        delta_nwc = (projected_revenue[t] - prev_revenue_for_nwc) * nwc_ratio
        fcff = nopat + da + capex - delta_nwc
        projected_fcf.append(fcff)
        fcf_margin = safe_divide(fcff, projected_revenue[t], fallback=0.0)
        projected_fcf_margins.append(fcf_margin)
        prev_revenue_for_nwc = projected_revenue[t]

    return {
        "projected_revenue": projected_revenue,
        "projected_ebitda": projected_ebitda,
        "projected_fcf": projected_fcf,
        "projected_growth_rates": projected_growth_rates,
        "projected_margins": projected_margins,
        "projected_fcf_margins": projected_fcf_margins,
        "tax_rate": tax_rate,
        "da_ratio": da_ratio,
        "capex_ratio": capex_ratio,
        "nwc_ratio": nwc_ratio,
    }


# ── Module 2: WACC Computation ────────────────────────────────────────


def compute_wacc(fd: dict, warnings: list[str]) -> dict:
    """Compute weighted average cost of capital (WACC).

    Uses CAPM for cost of equity with sector-average beta,
    and interest_expense / total_debt for cost of debt.
    """
    meta = fd["meta"]
    financials = fd["financials"]
    derived = fd["derived"]
    quality = fd["quality"]

    sector = meta.get("sector", "").upper()
    is_bank = quality.get("is_bank", False)

    # ── Cost of Equity (CAPM) ──────────────────────────────────────

    beta = SECTOR_AVG_BETAS.get(sector, DEFAULT_BETA)
    beta_source = "sector_average"

    re = RISK_FREE_RATE + beta * EQUITY_RISK_PREMIUM
    if re < RISK_FREE_RATE:
        re = RISK_FREE_RATE + 0.01

    # ── Cost of Debt ───────────────────────────────────────────────

    total_debt_latest = financials.get("total_debt", [0])[-1] or 0

    if total_debt_latest == 0 or is_bank:
        rd = 0.0
        weight_debt = 0.0
    else:
        # Find last non-None interest expense from the series
        interest_series = financials.get("interest_expense", [])
        last_interest = _last_valid(interest_series)

        if last_interest is None or last_interest <= 0:
            rd = 0.0
            warnings.append("No valid interest expense found; cost of debt set to 0")
        else:
            rd = safe_divide(last_interest, total_debt_latest, fallback=0.0)
            if rd > MAX_COST_OF_DEBT:
                warnings.append(
                    f"Cost of debt {rd:.2%} exceeds cap; clamped to {MAX_COST_OF_DEBT:.0%}"
                )
                rd = MAX_COST_OF_DEBT

    # ── Capital Structure ──────────────────────────────────────────

    market_cap = meta.get("market_cap", 0) or 0

    if is_bank or total_debt_latest == 0:
        weight_equity = 1.0
        weight_debt = 0.0
    else:
        v = market_cap + total_debt_latest
        if v > 0:
            weight_equity = market_cap / v
            weight_debt = total_debt_latest / v
        else:
            weight_equity = 1.0
            weight_debt = 0.0

    # ── Tax Rate ───────────────────────────────────────────────────

    tax_rates = derived.get("effective_tax_rate", [])
    tax_rate = tax_rates[-1] if tax_rates and tax_rates[-1] is not None else None
    if tax_rate is None or tax_rate < 0 or tax_rate > 0.5:
        tax_rate = US_STATUTORY_TAX_RATE

    # ── Final WACC ─────────────────────────────────────────────────

    if is_bank:
        wacc = re
        warnings.append("Bank detected: WACC = cost of equity (ignoring debt component)")
    else:
        wacc = weight_equity * re + weight_debt * rd * (1 - tax_rate)

    # Guard: WACC must exceed terminal growth rate
    if wacc <= TERMINAL_GROWTH_RATE:
        wacc = TERMINAL_GROWTH_RATE + 0.01
        warnings.append("WACC floored to terminal growth rate + 1%")

    wacc = _clamp(wacc, WACC_FLOOR, WACC_CEILING)

    return {
        "wacc": wacc,
        "cost_of_equity": re,
        "cost_of_debt": rd,
        "beta_used": beta,
        "beta_source": beta_source,
        "risk_free_rate": RISK_FREE_RATE,
        "equity_risk_premium": EQUITY_RISK_PREMIUM,
        "debt_weight": weight_debt,
        "equity_weight": weight_equity,
        "tax_rate": tax_rate,
    }


# ── Module 3: DCF Valuation ───────────────────────────────────────────


def compute_dcf(
    forecasts: dict,
    wacc_result: dict,
    fd: dict,
    warnings: list[str],
) -> dict:
    """Discount projected FCFs and terminal value to derive intrinsic value.

    Uses Gordon Growth Model for terminal value with exit-multiple
    cross-check. Falls back to exit multiple if TGR >= WACC.
    """
    meta = fd["meta"]
    financials = fd["financials"]
    sector = meta.get("sector", "").upper()

    wacc = wacc_result["wacc"]
    fcf_list = forecasts["projected_fcf"]
    ebitda_list = forecasts["projected_ebitda"]

    current_price = meta.get("current_price", 0)
    shares = meta.get("shares_outstanding", 1)
    net_debt = financials.get("net_debt", [0])[-1] or 0

    # ── Terminal Value — Gordon Growth (primary) ───────────────────

    terminal_fcff = fcf_list[-1] * (1 + TERMINAL_GROWTH_RATE)
    use_gordon = wacc > TERMINAL_GROWTH_RATE

    if use_gordon:
        terminal_value = terminal_fcff / (wacc - TERMINAL_GROWTH_RATE)
    else:
        terminal_value = None
        warnings.append("Gordon Growth undefined (TGR >= WACC); using exit multiple only")

    # ── Terminal Value — Exit Multiple (cross-check) ───────────────

    sector_multiples = SECTOR_AVG_MULTIPLES.get(sector, {})
    exit_ev_ebitda = sector_multiples.get("ev_ebitda", 15.0)
    terminal_value_exit = ebitda_list[-1] * exit_ev_ebitda

    if terminal_value is not None:
        # Cross-check: warn if Gordon and exit multiple differ > 50%
        tv_diff = abs(terminal_value - terminal_value_exit) / max(
            abs(terminal_value_exit), 1
        )
        if tv_diff > 0.50:
            warnings.append(
                f"Gordon Growth TV and exit multiple TV differ by {tv_diff:.0%}"
            )
    else:
        terminal_value = terminal_value_exit

    # ── Discounting ────────────────────────────────────────────────

    pv_fcf = []
    for t in range(1, PROJECTION_YEARS + 1):
        df = 1 / (1 + wacc) ** t
        pv_fcf.append(fcf_list[t - 1] * df)

    df_terminal = 1 / (1 + wacc) ** PROJECTION_YEARS
    pv_terminal = terminal_value * df_terminal

    enterprise_value = sum(pv_fcf) + pv_terminal

    # ── EV Bridge ──────────────────────────────────────────────────

    equity_value = enterprise_value - net_debt
    implied_share_price = safe_divide(equity_value, shares, fallback=0.0)
    upside = safe_divide(implied_share_price - current_price, current_price, fallback=0.0)

    # ── Sanity Checks ──────────────────────────────────────────────

    terminal_pct = safe_divide(pv_terminal, enterprise_value, fallback=0.0) if enterprise_value > 0 else 0.0

    if terminal_pct > TV_CRITICAL_THRESHOLD:
        warnings.append(
            f"Terminal value is {terminal_pct:.0%} of EV (critical threshold)"
        )
    elif terminal_pct > TV_WARNING_THRESHOLD:
        warnings.append(f"Terminal value is {terminal_pct:.0%} of EV (high)")

    price_ratio = safe_divide(implied_share_price, current_price, fallback=1.0) if current_price > 0 else 1.0
    if price_ratio > DCF_EXTREME_HIGH or price_ratio < DCF_EXTREME_LOW:
        warnings.append(
            f"DCF implied price is {price_ratio:.1f}x current price (extreme)"
        )

    if equity_value < 0:
        warnings.append("DCF produces negative equity value")

    return {
        "status": "success",
        "intrinsic_value_per_share": implied_share_price,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "upside_pct": upside,
        "wacc": wacc,
        "cost_of_equity": wacc_result["cost_of_equity"],
        "cost_of_debt": wacc_result["cost_of_debt"],
        "beta_used": wacc_result["beta_used"],
        "risk_free_rate": wacc_result["risk_free_rate"],
        "equity_risk_premium": wacc_result["equity_risk_premium"],
        "debt_weight": wacc_result["debt_weight"],
        "equity_weight": wacc_result["equity_weight"],
        "projection_years": PROJECTION_YEARS,
        "projected_revenue": forecasts["projected_revenue"],
        "projected_fcf": fcf_list,
        "projected_growth_rates": forecasts["projected_growth_rates"],
        "projected_fcf_margins": forecasts["projected_fcf_margins"],
        "terminal_growth_rate": TERMINAL_GROWTH_RATE,
        "terminal_value": terminal_value,
        "terminal_value_pct": terminal_pct,
    }


# ── Module 4: Relative Valuation ──────────────────────────────────────


def compute_relative(fd: dict, warnings: list[str]) -> dict:
    """Compare company multiples against sector medians.

    Computes EV/EBITDA, P/E, and P/B implied share prices from
    sector-average multiples in shared_config.
    """
    meta = fd["meta"]
    financials = fd["financials"]
    ttm = fd["ttm"]

    sector = meta.get("sector", "").upper()
    current_price = meta.get("current_price", 0)
    shares = meta.get("shares_outstanding", 1)
    ev = meta.get("enterprise_value", 0)
    net_debt = financials.get("net_debt", [0])[-1] or 0

    sector_multiples = SECTOR_AVG_MULTIPLES.get(sector)
    if sector_multiples is None:
        warnings.append(f"No sector multiples for '{sector}'; relative valuation skipped")
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
        }

    implied_prices = []

    # ── EV/EBITDA ──────────────────────────────────────────────────

    ttm_ebitda = ttm.get("ebitda", 0) or 0
    if ttm_ebitda > 0 and ev > 0:
        ev_ebitda_company = ev / ttm_ebitda
        ev_ebitda_median = sector_multiples["ev_ebitda"]
        implied_ev = ev_ebitda_median * ttm_ebitda
        implied_equity = implied_ev - net_debt
        ev_ebitda_implied = safe_divide(implied_equity, shares, fallback=None)
        if ev_ebitda_implied is not None and ev_ebitda_implied > 0:
            implied_prices.append(ev_ebitda_implied)
    else:
        ev_ebitda_company = None
        ev_ebitda_median = sector_multiples.get("ev_ebitda")
        ev_ebitda_implied = None
        if ttm_ebitda <= 0:
            warnings.append("Negative/zero EBITDA: EV/EBITDA skipped")

    # ── P/E ────────────────────────────────────────────────────────

    ttm_net_income = ttm.get("net_income", 0) or 0
    if ttm_net_income > 0 and shares > 0:
        eps = ttm_net_income / shares
        pe_company = current_price / eps if eps > 0 else None
        pe_median = sector_multiples["pe"]
        pe_implied = eps * pe_median
        if pe_implied > 0:
            implied_prices.append(pe_implied)
    else:
        pe_company = None
        pe_median = sector_multiples.get("pe")
        pe_implied = None
        if ttm_net_income <= 0:
            warnings.append("Negative/zero net income: P/E skipped")

    # ── P/B ────────────────────────────────────────────────────────

    total_equity_latest = financials.get("total_equity", [0])[-1] or 0
    if total_equity_latest > 0 and shares > 0:
        bvps = total_equity_latest / shares
        pb_company = current_price / bvps if bvps > 0 else None
        pb_median = sector_multiples["pb"]
        pb_implied_price = bvps * pb_median
        if pb_implied_price > 0:
            implied_prices.append(pb_implied_price)
    else:
        pb_company = None
        pb_median = sector_multiples.get("pb")
        pb_implied_price = None
        if total_equity_latest <= 0:
            warnings.append("Negative/zero equity: P/B skipped")

    # ── Summary ────────────────────────────────────────────────────

    status = "success" if len(implied_prices) >= 2 else "partial" if implied_prices else "failed"

    return {
        "status": status,
        "peers": [],  # no real peers in v1; uses sector averages
        "num_peers": 0,
        "ev_ebitda_company": ev_ebitda_company,
        "ev_ebitda_peers_median": ev_ebitda_median,
        "ev_ebitda_implied_value": ev_ebitda_implied,
        "pe_company": pe_company,
        "pe_peers_median": pe_median,
        "pe_implied_value": pe_implied,
        "pb_company": pb_company,
        "pb_peers_median": pb_median,
        "pb_implied_value": pb_implied_price if total_equity_latest > 0 else None,
        "_implied_prices": implied_prices,  # internal, used by summary builder
    }


# ── Module 5: Sensitivity Analysis ────────────────────────────────────


def compute_sensitivity(
    forecasts: dict,
    wacc_val: float,
    fd: dict,
    warnings: list[str],
) -> dict:
    """Build 5x5 WACC x terminal-growth-rate implied share price matrix.

    Re-discounts the same projected FCFs with varying WACC and TGR
    combinations. Does NOT re-forecast cash flows.
    """
    meta = fd["meta"]
    financials = fd["financials"]

    shares = meta.get("shares_outstanding", 1)
    net_debt = financials.get("net_debt", [0])[-1] or 0
    fcf_list = forecasts["projected_fcf"]
    ebitda_last = forecasts["projected_ebitda"][-1]
    sector = meta.get("sector", "").upper()

    # Build ranges centered on base case
    # SENSITIVITY_*_POINTS = steps each side (e.g. 2 → 5-point grid)
    half_w = SENSITIVITY_WACC_POINTS
    half_g = SENSITIVITY_TGR_POINTS
    total_w = 2 * half_w + 1
    total_g = 2 * half_g + 1

    wacc_range = [
        wacc_val + (i - half_w) * SENSITIVITY_WACC_STEP
        for i in range(total_w)
    ]
    tgr_range = [
        TERMINAL_GROWTH_RATE + (i - half_g) * SENSITIVITY_TGR_STEP
        for i in range(total_g)
    ]

    # Exit multiple fallback
    sector_multiples = SECTOR_AVG_MULTIPLES.get(sector, {})
    exit_ev_ebitda = sector_multiples.get("ev_ebitda", 15.0)

    value_matrix: list[list[Optional[float]]] = []

    for w in wacc_range:
        row: list[Optional[float]] = []
        for g in tgr_range:
            if g >= w:
                row.append(None)
                continue

            # Terminal value
            terminal_fcff = fcf_list[-1] * (1 + g)
            tv = terminal_fcff / (w - g)

            # Discount
            pv_fcf_sum = 0.0
            for t in range(1, PROJECTION_YEARS + 1):
                df = 1 / (1 + w) ** t
                pv_fcf_sum += fcf_list[t - 1] * df

            df_terminal = 1 / (1 + w) ** PROJECTION_YEARS
            pv_tv = tv * df_terminal

            ev = pv_fcf_sum + pv_tv
            equity = ev - net_debt
            price = safe_divide(equity, shares, fallback=0.0)
            row.append(price)
        value_matrix.append(row)

    return {
        "wacc_range": wacc_range,
        "growth_range": tgr_range,
        "value_matrix": value_matrix,
        "base_case_wacc_idx": half_w,
        "base_case_growth_idx": half_g,
    }
