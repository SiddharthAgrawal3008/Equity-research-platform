"""
Engine 2 — Financial Analysis Engine
=====================================

Receives *raw_financials* (Contract A, produced by Engine 1) and outputs
*analysis_metrics* (Contract B, consumed by Engine 3 — Valuation Engine).

Contract B top-level keys:
    ticker, years, source, margins, growth, returns,
    efficiency, cost_structure, trend_flags
"""

from __future__ import annotations

from typing import Any, List, Optional


# 1.  CONTRACT-A VALIDATOR

class DataContractError(Exception):
    """Raised when raw_financials violates the Contract-A schema."""


_INCOME_FIELDS = [
    "revenue", "cogs", "gross_profit", "salaries", "rent_overhead",
    "da", "interest", "ebt", "taxes", "net_income",
]
_BALANCE_FIELDS = [
    "cash", "accounts_rec", "inventory", "ppe", "total_assets",
    "accounts_pay", "debt", "total_liab", "retained_earnings", "equity",
]
_CASHFLOW_FIELDS = ["cfo", "capex", "cfi", "cff", "net_change"]

MIN_YEARS = 3


def validate_input(data: dict) -> None:
    """Validate that *data* conforms to the Contract-A schema.

    Args:
        data: The raw_financials dict from Engine 1.

    Raises:
        DataContractError: If any required field is missing, has the wrong
            length, or contains None values.
    """
    years = data.get("years")
    if not years or len(years) < MIN_YEARS:
        raise DataContractError(
            f"'years' must contain at least {MIN_YEARS} elements, "
            f"got {len(years) if years else 0}"
        )

    n = len(years)

    def _check_section(section_name: str, required_fields: list[str]) -> None:
        section = data.get(section_name)
        if section is None:
            raise DataContractError(f"Missing section '{section_name}'")
        for field in required_fields:
            arr = section.get(field)
            if arr is None:
                raise DataContractError(
                    f"Missing field '{field}' in '{section_name}'"
                )
            if len(arr) != n:
                raise DataContractError(
                    f"'{section_name}.{field}' has length {len(arr)}, "
                    f"expected {n} (matching years)"
                )
            if any(v is None for v in arr):
                raise DataContractError(
                    f"'{section_name}.{field}' contains None values"
                )

    _check_section("income_statement", _INCOME_FIELDS)
    _check_section("balance_sheet", _BALANCE_FIELDS)
    _check_section("cash_flow", _CASHFLOW_FIELDS)


# 2.  HELPER UTILITIES

def safe_divide(
    numerator: Optional[float],
    denominator: Optional[float],
    fallback: Optional[float] = None,
) -> Optional[float]:
    """Return numerator / denominator, or *fallback* on zero / None inputs.

    Args:
        numerator:   The dividend.
        denominator: The divisor.
        fallback:    Value returned when division is impossible.

    Returns:
        The quotient, or *fallback*.
    """
    if numerator is None or denominator is None or denominator == 0:
        return fallback
    return numerator / denominator


def pct(value: Optional[float]) -> Optional[float]:
    """Round *value* to 4 decimal places; pass-through None.

    Args:
        value: A ratio (e.g. 0.38125).

    Returns:
        The rounded value, or None.
    """
    if value is None:
        return None
    return round(value, 4)


def growth_rate(series: List[float]) -> List[Optional[float]]:
    """Compute year-over-year growth rates for a time series.

    Args:
        series: Ordered numeric values (oldest to newest).

    Returns:
        A list of length len(series) - 1 with each YoY growth rate.
    """
    rates: list[Optional[float]] = []
    for i in range(1, len(series)):
        rate = safe_divide(series[i] - series[i - 1], series[i - 1])
        rates.append(pct(rate))
    return rates


def cagr(series: List[float], n_years: int) -> Optional[float]:
    """Compound annual growth rate from first to last value.

    Args:
        series:  Ordered numeric values (oldest to newest).
        n_years: Number of years between first and last value.

    Returns:
        CAGR as a decimal ratio, or None if it cannot be computed.
    """
    if not series or n_years <= 0 or series[0] <= 0:
        return None
    ratio = safe_divide(series[-1], series[0])
    if ratio is None or ratio <= 0:
        return None
    return pct(ratio ** safe_divide(1, n_years) - 1)


def average(series: List[Optional[float]]) -> Optional[float]:
    """Arithmetic mean of *series*, ignoring None values.

    Args:
        series: A list of numbers (may contain None).

    Returns:
        The mean, or None if no valid values exist.
    """
    valid = [v for v in series if v is not None]
    if not valid:
        return None
    return pct(sum(valid) / len(valid))


# 3.  METRIC COMPUTATION FUNCTIONS

def compute_margins(data: dict) -> dict:
    """Profitability margins per year (as ratios, not percentages).

    Args:
        data: Contract-A raw_financials dict.

    Returns:
        Dict with keys: gross_margin, net_margin, ebt_margin.
    """
    inc = data["income_statement"]
    n = len(data["years"])

    gross_margin = [
        pct(safe_divide(inc["gross_profit"][i], inc["revenue"][i]))
        for i in range(n)
    ]
    net_margin = [
        pct(safe_divide(inc["net_income"][i], inc["revenue"][i]))
        for i in range(n)
    ]
    ebt_margin = [
        pct(safe_divide(inc["ebt"][i], inc["revenue"][i]))
        for i in range(n)
    ]

    return {
        "gross_margin": gross_margin,
        "net_margin": net_margin,
        "ebt_margin": ebt_margin,
    }


def compute_growth_rates(data: dict) -> dict:
    """Year-over-year and compound growth rates.

    Args:
        data: Contract-A raw_financials dict.

    Returns:
        Dict with keys: revenue_yoy, net_income_yoy, gross_profit_yoy,
        revenue_cagr, net_income_cagr.
    """
    inc = data["income_statement"]
    n_years = len(data["years"]) - 1

    return {
        "revenue_yoy": growth_rate(inc["revenue"]),
        "net_income_yoy": growth_rate(inc["net_income"]),
        "gross_profit_yoy": growth_rate(inc["gross_profit"]),
        "revenue_cagr": cagr(inc["revenue"], n_years),
        "net_income_cagr": cagr(inc["net_income"], n_years),
    }


def compute_return_metrics(data: dict) -> dict:
    """Return on equity, assets, and invested capital.

    Args:
        data: Contract-A raw_financials dict.

    Returns:
        Dict with keys: roe, roa, roic (per year) and
        avg_roe, avg_roa, avg_roic (single floats).
    """
    inc = data["income_statement"]
    bs = data["balance_sheet"]
    n = len(data["years"])

    roe: list[Optional[float]] = []
    roa: list[Optional[float]] = []
    roic: list[Optional[float]] = []

    for i in range(n):
        # ROE = Net Income / Equity
        roe.append(pct(safe_divide(inc["net_income"][i], bs["equity"][i])))

        # ROA = Net Income / Total Assets
        roa.append(pct(safe_divide(inc["net_income"][i], bs["total_assets"][i])))

        # ROIC = NOPAT / Invested Capital
        ebit = inc["ebt"][i] + inc["interest"][i]
        effective_tax_rate = safe_divide(inc["taxes"][i], inc["ebt"][i], fallback=0.0)
        nopat = ebit * (1 - effective_tax_rate)
        invested_capital = bs["equity"][i] + bs["debt"][i]
        roic.append(pct(safe_divide(nopat, invested_capital)))

    return {
        "roe": roe,
        "roa": roa,
        "roic": roic,
        "avg_roe": average(roe),
        "avg_roa": average(roa),
        "avg_roic": average(roic),
    }


def compute_efficiency_ratios(data: dict) -> dict:
    """Working-capital efficiency ratios (in days).

    Args:
        data: Contract-A raw_financials dict.

    Returns:
        Dict with keys: ar_days, inv_days, ap_days (per year).
    """
    inc = data["income_statement"]
    bs = data["balance_sheet"]
    n = len(data["years"])
    days_in_year = 365

    ar_days = [
        pct(safe_divide(bs["accounts_rec"][i], inc["revenue"][i]) * days_in_year)
        if safe_divide(bs["accounts_rec"][i], inc["revenue"][i]) is not None
        else None
        for i in range(n)
    ]
    inv_days = [
        pct(safe_divide(bs["inventory"][i], inc["cogs"][i]) * days_in_year)
        if safe_divide(bs["inventory"][i], inc["cogs"][i]) is not None
        else None
        for i in range(n)
    ]
    ap_days = [
        pct(safe_divide(bs["accounts_pay"][i], inc["cogs"][i]) * days_in_year)
        if safe_divide(bs["accounts_pay"][i], inc["cogs"][i]) is not None
        else None
        for i in range(n)
    ]

    return {
        "ar_days": ar_days,
        "inv_days": inv_days,
        "ap_days": ap_days,
    }


def compute_cost_structure(data: dict) -> dict:
    """Cost items as a share of revenue (ratios per year).

    Args:
        data: Contract-A raw_financials dict.

    Returns:
        Dict with keys: cogs_pct_revenue, salaries_pct_revenue,
        da_pct_revenue, interest_pct_revenue.
    """
    inc = data["income_statement"]
    n = len(data["years"])

    return {
        "cogs_pct_revenue": [
            pct(safe_divide(inc["cogs"][i], inc["revenue"][i]))
            for i in range(n)
        ],
        "salaries_pct_revenue": [
            pct(safe_divide(inc["salaries"][i], inc["revenue"][i]))
            for i in range(n)
        ],
        "da_pct_revenue": [
            pct(safe_divide(inc["da"][i], inc["revenue"][i]))
            for i in range(n)
        ],
        "interest_pct_revenue": [
            pct(safe_divide(inc["interest"][i], inc["revenue"][i]))
            for i in range(n)
        ],
    }


def compute_trend_flags(
    margins: dict,
    growth: dict,
    returns: dict,
) -> dict:
    """Classify each metric trend as improving, stable, or deteriorating.

    Compares the average of the last 2 values to the average of the first 2.
    A delta above *threshold* is improving; below negative threshold is
    deteriorating; otherwise stable.

    Args:
        margins: Output of compute_margins.
        growth:  Output of compute_growth_rates.
        returns: Output of compute_return_metrics.

    Returns:
        Dict with keys: gross_margin_trend, net_margin_trend,
        revenue_growth_trend, roe_trend, roic_trend.
    """
    threshold = 0.01

    def _classify(series: list[Optional[float]]) -> str:
        """Compare first-2 avg to last-2 avg."""
        valid = [v for v in series if v is not None]
        if len(valid) < 4:
            return "insufficient_data"

        first_two_avg = sum(valid[:2]) / 2
        last_two_avg = sum(valid[-2:]) / 2
        delta = last_two_avg - first_two_avg

        if delta > threshold:
            return "improving"
        if delta < -threshold:
            return "deteriorating"
        return "stable"

    return {
        "gross_margin_trend": _classify(margins["gross_margin"]),
        "net_margin_trend": _classify(margins["net_margin"]),
        "revenue_growth_trend": _classify(growth["revenue_yoy"]),
        "roe_trend": _classify(returns["roe"]),
        "roic_trend": _classify(returns["roic"]),
    }


# 4.  MAIN ENTRY POINT

def run(raw_financials: dict) -> dict:
    """Execute the full financial-analysis pipeline.

    **Contract B** - the returned dict has these top-level keys:
        ticker, years, source, margins, growth, returns,
        efficiency, cost_structure, trend_flags

    This is the schema that Engine 3 (Valuation Engine) will consume.

    Args:
        raw_financials: A Contract-A dict produced by Engine 1.

    Returns:
        An analysis_metrics dict (Contract B).

    Raises:
        DataContractError: If *raw_financials* fails validation.
    """
    validate_input(raw_financials)

    margins = compute_margins(raw_financials)
    growth = compute_growth_rates(raw_financials)
    returns = compute_return_metrics(raw_financials)
    efficiency = compute_efficiency_ratios(raw_financials)
    cost_structure = compute_cost_structure(raw_financials)
    trend_flags = compute_trend_flags(margins, growth, returns)

    return {
        "ticker": raw_financials["ticker"],
        "years": raw_financials["years"],
        "source": raw_financials["source"],
        "margins": margins,
        "growth": growth,
        "returns": returns,
        "efficiency": efficiency,
        "cost_structure": cost_structure,
        "trend_flags": trend_flags,
    }


# 5.  LOCAL TEST BLOCK

if __name__ == "__main__":
    import json
    from backend.engines.mock_data import MOCK_RAW_FINANCIALS

    result = run(MOCK_RAW_FINANCIALS)
    print(json.dumps(result, indent=2))
