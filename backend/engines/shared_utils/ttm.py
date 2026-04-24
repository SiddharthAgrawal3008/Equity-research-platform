from __future__ import annotations


def _last_valid(series: list):
    for v in reversed(series or []):
        if v is not None:
            return v
    return None


def synthesise_ttm(financials: dict) -> dict:
    """Best-effort TTM from last valid annual values. Used when Engine 1 has not provided a real TTM block."""
    return {
        "revenue":          _last_valid(financials.get("revenue",          [])),
        "ebitda":           _last_valid(financials.get("ebitda",           [])),
        "net_income":       _last_valid(financials.get("net_income",       [])),
        "interest_expense": _last_valid(financials.get("interest_expense", [])),
    }
