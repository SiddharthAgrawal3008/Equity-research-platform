"""
Engine 1 — Standardizer (Step 2)
=================================

Takes the raw dict from fetch_raw() and returns a populated Engine1Output
object from shared_context.py.

WHAT THIS MODULE DOES:
    - Reverses all FMP lists from newest-first → oldest-first
    - Extracts the master year index from annual_income["fiscalYear"]
    - Converts every monetary value from absolute dollars → USD millions
    - Populates CompanyMeta and AnnualFinancials
    - Returns Engine1Output with derived fields (margins, growth, etc.)
      left as empty dicts — those are computed in later steps.

WHAT THIS MODULE DOES NOT DO:
    - Does not compute margins, growth, or trend flags  (later steps)
    - Does not compute TTM                              (later steps)
    - Does not validate the output                      (later steps)
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
    Convert a raw FMP monetary value to USD millions.

    Rules:
        None  → None   (missing data — never substitute 0)
        0     → 0.0    (zero is a valid reported value)
        other → float(value) / 1_000_000
    """
    if value is None:
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
             profile, annual_income, annual_balance, annual_cashflow,
             quarterly_income, quarterly_cashflow.

    Returns:
        A populated Engine1Output object. Derived fields (margins, growth,
        returns, efficiency, cost_structure, trend_flags, ttm) are empty
        dicts — they are populated by later steps.

    Raises:
        DataFetchError: If any required FMP field is missing or has an
                        unexpected type, with a message identifying the
                        field that failed.
    """
    try:
        # ── STEP 1 — Extract profile and reverse all statement lists ──────────
        # FMP returns newest-first. Contract requires oldest-first.
        profile         = raw["profile"][0]
        annual_income   = list(reversed(raw["annual_income"]))
        annual_balance  = list(reversed(raw["annual_balance"]))
        annual_cashflow = list(reversed(raw["annual_cashflow"]))

        # ── STEP 2 — Extract master year index ────────────────────────────────
        # All other lists must align to this by index.
        years = [int(row["fiscalYear"]) for row in annual_income]

        # ── STEP 3 — Build CompanyMeta (enterprise_value computed after BS) ───
        current_price = float(profile["price"])
        market_cap    = float(profile["marketCap"]) / 1_000_000  # USD millions
        sector        = profile.get("sector")       or "Unknown"
        company_name  = profile["companyName"]

        # shares_outstanding derived from market cap (already in millions)
        shares_outstanding = market_cap / current_price if current_price else 0.0

        # enterprise_value placeholder — computed after balance sheet is built
        enterprise_value = 0.0

        meta = CompanyMeta(
            ticker             = profile["symbol"],
            company_name       = company_name,
            sector             = sector,
            industry           = profile.get("industry")  or "Unknown",
            exchange           = profile.get("exchange")  or "Unknown",
            currency           = profile.get("currency")  or "USD",
            current_price      = current_price,
            market_cap         = market_cap,
            shares_outstanding = shares_outstanding,
            enterprise_value   = enterprise_value,  # patched in Step 6
            description        = profile.get("description") or "",
        )

        # ── STEP 4 — Build AnnualFinancials ───────────────────────────────────

        # — Income Statement —
        revenue          = [_m(r["revenue"])          for r in annual_income]
        gross_profit     = [_m(r["grossProfit"])      for r in annual_income]
        ebit             = [_m(r["ebit"])              for r in annual_income]
        ebitda           = [_m(r["ebitda"])            for r in annual_income]
        net_income       = [_m(r["netIncome"])         for r in annual_income]
        interest_expense = [_m(r["interestExpense"])   for r in annual_income]

        # — Balance Sheet —
        total_assets         = [_m(r["totalAssets"])             for r in annual_balance]
        current_assets       = [_m(r["totalCurrentAssets"])      for r in annual_balance]
        current_liabilities  = [_m(r["totalCurrentLiabilities"]) for r in annual_balance]
        cash_and_equivalents = [_m(r["cashAndCashEquivalents"])  for r in annual_balance]
        inventory            = [_m(r.get("inventory"))           for r in annual_balance]
        accounts_receivable  = [_m(r["accountsReceivables"])     for r in annual_balance]
        total_debt           = [_m(r["totalDebt"])               for r in annual_balance]
        total_liabilities    = [_m(r["totalLiabilities"])        for r in annual_balance]
        retained_earnings    = [_m(r["retainedEarnings"])        for r in annual_balance]
        goodwill             = [_m(r.get("goodwill"))            for r in annual_balance]

        # FMP does not provide historical market cap in financial statements.
        # Repeat current market_cap across all years — used only for Altman Z-score.
        market_capitalization = [market_cap] * len(years)

        # — Cash Flow Statement —
        # capex values are negative (cash outflow) — preserve sign, do not flip.
        operating_cash_flow = [_m(r["operatingCashFlow"])   for r in annual_cashflow]
        capex               = [_m(r["capitalExpenditure"])  for r in annual_cashflow]

        financials = AnnualFinancials(
            years                = years,
            revenue              = revenue,
            gross_profit         = gross_profit,
            ebit                 = ebit,
            ebitda               = ebitda,
            net_income           = net_income,
            interest_expense     = interest_expense,
            total_assets         = total_assets,
            current_assets       = current_assets,
            current_liabilities  = current_liabilities,
            cash_and_equivalents = cash_and_equivalents,
            inventory            = inventory,
            accounts_receivable  = accounts_receivable,
            total_debt           = total_debt,
            total_liabilities    = total_liabilities,
            retained_earnings    = retained_earnings,
            goodwill             = goodwill,
            market_capitalization = market_capitalization,
            operating_cash_flow  = operating_cash_flow,
            capex                = capex,
        )

        # ── STEP 5 — Patch enterprise_value into CompanyMeta ──────────────────
        latest_total_debt = financials.total_debt[-1] or 0.0
        latest_cash       = financials.cash_and_equivalents[-1] or 0.0
        meta.enterprise_value = market_cap + latest_total_debt - latest_cash

        # ── STEP 6 — Return Engine1Output ─────────────────────────────────────
        # Derived fields (margins, growth, returns, efficiency, cost_structure,
        # trend_flags, ttm) are empty dicts — populated by later steps.
        return Engine1Output(
            meta       = meta,
            financials = financials,
            margins    = {},
            growth     = {},
            returns    = {},
            efficiency = {},
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

    except (KeyError, TypeError) as exc:
        raise DataFetchError(
            f"Engine 1 standardizer failed — missing or invalid field: {exc}. "
            "The FMP response may be incomplete or the field mapping is incorrect."
        ) from exc
