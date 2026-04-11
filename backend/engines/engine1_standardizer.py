"""
Engine 1 — Standardizer (Step 2)
=================================

Takes the raw dict from fetch_raw() and returns a populated Engine1Output
object from shared_context.py.

WHAT THIS MODULE DOES:
    - Reverses all Alpha Vantage lists from newest-first → oldest-first
    - Extracts the master year index from annualReports["fiscalDateEnding"]
    - Converts every monetary value from absolute dollars → USD millions
    - Handles Alpha Vantage's "None" string for missing values
    - Populates CompanyMeta and AnnualFinancials
    - Returns Engine1Output with derived fields (margins, growth, etc.)
      left as empty dicts — those are computed in later steps.

WHAT THIS MODULE DOES NOT DO:
    - Does not compute margins, growth, or trend flags  (later steps)
    - Does not compute TTM                              (later steps)
    - Does not validate the output                      (later steps)

DATA SOURCE FIELD NOTES:
    Alpha Vantage returns string values for all numbers, including the
    string "None" (not Python None) when a field is not reported.
    _m() handles both Python None and the string "None" correctly.
"""

from __future__ import annotations

from typing import Optional

from backend.engines.financial_data import DataFetchError
from backend.engines.shared_context import (
    AnnualFinancials,
    CompanyMeta,
    Engine1Output,
)


# ---------------------------------------------------------------------------
# Internal Helper
# ---------------------------------------------------------------------------

def _m(value) -> Optional[float]:
    """
    Convert a raw Alpha Vantage monetary value to USD millions.

    Rules:
        Python None   → None   (missing data — never substitute 0)
        string "None" → None   (AV returns this string for unreported fields)
        0 / "0"       → 0.0    (zero is a valid reported value)
        other         → float(value) / 1_000_000
    """
    if value is None or str(value).strip() == "None":
        return None
    return float(value) / 1_000_000


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

def standardize(raw: dict) -> Engine1Output:
    """
    Transform the raw dict from fetch_raw() into a populated Engine1Output.

    Args:
        raw: The dict returned by fetch_raw(). Must contain keys:
             overview, annual_income, annual_balance, annual_cashflow,
             quarterly_income, quarterly_cashflow, current_price.

    Returns:
        A populated Engine1Output object. Derived fields (margins, growth,
        returns, efficiency, cost_structure, trend_flags, ttm) are empty
        dicts — they are populated by later steps.

    Raises:
        DataFetchError: If any required Alpha Vantage field is missing or
                        has an unexpected type, with a message identifying
                        the field that failed.
    """
    try:
        # ── STEP 1 — Extract overview and reverse all statement lists ─────────
        # Alpha Vantage returns newest-first. Contract requires oldest-first.
        # overview is a flat dict (not a list — unlike the old FMP profile).
        overview        = raw["overview"]
        annual_income   = list(reversed(raw["annual_income"]))
        annual_balance  = list(reversed(raw["annual_balance"]))
        annual_cashflow = list(reversed(raw["annual_cashflow"]))

        # ── STEP 2 — Extract master year index ────────────────────────────────
        # AV uses "fiscalDateEnding" as "YYYY-MM-DD" — extract the year integer.
        # All other lists must align to this by index.
        years = [int(row["fiscalDateEnding"][:4]) for row in annual_income]

        # ── STEP 3 — Build CompanyMeta ────────────────────────────────────────
        # current_price comes from Finnhub, stored as a top-level key in raw.
        # market_cap and shares_outstanding come from AV OVERVIEW.
        current_price      = float(raw["current_price"])
        market_cap         = float(overview["MarketCapitalization"]) / 1_000_000
        shares_outstanding = float(overview["SharesOutstanding"]) / 1_000_000
        sector             = overview.get("Sector")      or "Unknown"
        company_name       = overview["Name"]

        meta = CompanyMeta(
            ticker             = overview["Symbol"],
            company_name       = company_name,
            sector             = sector,
            industry           = overview.get("Industry")    or "Unknown",
            exchange           = overview.get("Exchange")    or "Unknown",
            currency           = overview.get("Currency")    or "USD",
            current_price      = current_price,
            market_cap         = market_cap,
            shares_outstanding = shares_outstanding,
            enterprise_value   = 0.0,   # patched in Step 5 after balance sheet
            description        = overview.get("Description") or "",
        )

        # ── STEP 4 — Build AnnualFinancials ───────────────────────────────────

        # — Income Statement —
        # AV field: "totalRevenue"   (not "revenue")
        revenue          = [_m(r["totalRevenue"])      for r in annual_income]
        gross_profit     = [_m(r["grossProfit"])       for r in annual_income]
        ebit             = [_m(r["ebit"])               for r in annual_income]
        ebitda           = [_m(r["ebitda"])             for r in annual_income]
        net_income       = [_m(r["netIncome"])          for r in annual_income]
        interest_expense = [_m(r["interestExpense"])    for r in annual_income]

        # — Balance Sheet —
        # AV field: "cashAndCashEquivalentsAtCarryingValue" (not "cashAndCashEquivalents")
        # AV field: "currentNetReceivables"                 (not "accountsReceivables")
        # AV field: "shortLongTermDebtTotal"                (not "totalDebt")
        total_assets         = [_m(r["totalAssets"])                          for r in annual_balance]
        current_assets       = [_m(r["totalCurrentAssets"])                   for r in annual_balance]
        current_liabilities  = [_m(r["totalCurrentLiabilities"])              for r in annual_balance]
        cash_and_equivalents = [_m(r["cashAndCashEquivalentsAtCarryingValue"]) for r in annual_balance]
        inventory            = [_m(r.get("inventory"))                        for r in annual_balance]
        accounts_receivable  = [_m(r["currentNetReceivables"])                for r in annual_balance]
        total_debt           = [_m(r["shortLongTermDebtTotal"])               for r in annual_balance]
        total_liabilities    = [_m(r["totalLiabilities"])                     for r in annual_balance]
        retained_earnings    = [_m(r["retainedEarnings"])                     for r in annual_balance]
        goodwill             = [_m(r.get("goodwill"))                         for r in annual_balance]

        # AV does not provide historical market cap in financial statements.
        # Repeat current market_cap across all years — used only for Altman Z-score.
        market_capitalization = [market_cap] * len(years)

        # — Cash Flow Statement —
        # AV field: "operatingCashflow"   (lowercase 'f' — not "operatingCashFlow")
        # AV field: "capitalExpenditures" (plural — not "capitalExpenditure")
        # AV returns capex as a POSITIVE number. Contract requires NEGATIVE (cash outflow).
        operating_cash_flow = [_m(r["operatingCashflow"]) for r in annual_cashflow]
        capex_raw           = [_m(r["capitalExpenditures"]) for r in annual_cashflow]
        capex               = [(-x if x is not None else None) for x in capex_raw]

        financials = AnnualFinancials(
            years                 = years,
            revenue               = revenue,
            gross_profit          = gross_profit,
            ebit                  = ebit,
            ebitda                = ebitda,
            net_income            = net_income,
            interest_expense      = interest_expense,
            total_assets          = total_assets,
            current_assets        = current_assets,
            current_liabilities   = current_liabilities,
            cash_and_equivalents  = cash_and_equivalents,
            inventory             = inventory,
            accounts_receivable   = accounts_receivable,
            total_debt            = total_debt,
            total_liabilities     = total_liabilities,
            retained_earnings     = retained_earnings,
            goodwill              = goodwill,
            market_capitalization = market_capitalization,
            operating_cash_flow   = operating_cash_flow,
            capex                 = capex,
        )

        # ── STEP 5 — Patch enterprise_value into CompanyMeta ──────────────────
        latest_total_debt     = financials.total_debt[-1] or 0.0
        latest_cash           = financials.cash_and_equivalents[-1] or 0.0
        meta.enterprise_value = market_cap + latest_total_debt - latest_cash

        # ── STEP 6 — Return Engine1Output ─────────────────────────────────────
        # Derived fields (margins, growth, returns, efficiency, cost_structure,
        # trend_flags, ttm) are empty dicts — populated by later steps.
        return Engine1Output(
            meta           = meta,
            financials     = financials,
            margins        = {},
            growth         = {},
            returns        = {},
            efficiency     = {},
            cost_structure = {},
            trend_flags    = {},
            ttm            = {},
            quality        = {
                "is_valid":                  True,
                "missing_fields":            [],
                "warnings":                  [],
                "errors":                    [],
                "net_income_cf_reconciled":  False,
                "balance_sheet_balanced":    False,
                "debt_change_reconciled":    False,
                "is_bank":                   sector in ("Financials", "Banks"),
                "is_reit":                   "REIT" in company_name.upper(),
                "is_negative_equity":        False,
                "years_of_history":          len(years),
            },
        )

    except (KeyError, TypeError, ValueError) as exc:
        raise DataFetchError(
            f"Engine 1 standardizer failed — missing or invalid field: {exc}. "
            "The Alpha Vantage response may be incomplete or the field mapping "
            "is incorrect."
        ) from exc
