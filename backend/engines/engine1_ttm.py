"""
Engine 1 — TTM Computation (Step 4)
=====================================

Computes Trailing Twelve Month figures from the last 4 quarterly reports
and writes them into Engine1Output.ttm.

WHAT THIS MODULE DOES:
    - Reverses AV quarterly lists from newest-first → oldest-first
    - Takes the last 4 quarters (most recent)
    - Sums monetary fields across those 4 quarters
    - Averages effective_tax_rate across valid quarters
    - Writes all results into output.ttm as a flat dict

WHAT THIS MODULE DOES NOT DO:
    - Does not re-fetch any data            (Step 1)
    - Does not standardize annual fields    (Step 2)
    - Does not compute derived metrics      (Step 3)
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.engines.shared_context import Engine1Output

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal Helper (mirrors engine1_standardizer._m exactly)
# ---------------------------------------------------------------------------

def _m(value) -> Optional[float]:
    """Convert a raw AV monetary string to USD millions. Returns None if missing."""
    if value is None or str(value).strip() == "None":
        return None
    return float(value) / 1_000_000


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

def compute_ttm(output: Engine1Output, raw: dict) -> Engine1Output:
    """
    Compute TTM figures from the last 4 quarterly reports and populate
    output.ttm. Modifies and returns the same object.

    Args:
        output: A populated Engine1Output (after Steps 2 and 3).
        raw:    The dict returned by fetch_raw(). Must contain keys
                quarterly_income and quarterly_cashflow.

    Returns:
        The same Engine1Output with ttm populated as a flat dict.
        On any failure, output.ttm = {"error": "TTM computation failed"}.
    """
    try:
        # ── Reverse AV lists from newest-first → oldest-first ────────────────
        quarterly_income   = list(reversed(raw["quarterly_income"]))
        quarterly_cashflow = list(reversed(raw["quarterly_cashflow"]))

        # ── Take last 4 quarters (most recent) ───────────────────────────────
        q_inc = quarterly_income[-4:]
        q_cf  = quarterly_cashflow[-4:]

        ttm_quarters_included = min(len(q_inc), len(q_cf))

        # Align both lists to the same length in case one has fewer quarters
        q_inc = q_inc[-ttm_quarters_included:]
        q_cf  = q_cf[-ttm_quarters_included:]

        # TTM as-of date: fiscalDateEnding of the most recent quarter
        ttm_as_of_date = quarterly_income[-1]["fiscalDateEnding"] if quarterly_income else None

        # ── Sum fields across quarters ────────────────────────────────────────
        def _sum_field(quarters: list, field: str) -> Optional[float]:
            values = [_m(q.get(field)) for q in quarters]
            if all(v is None for v in values):
                return None
            return sum(v for v in values if v is not None)

        revenue             = _sum_field(q_inc, "totalRevenue")
        ebitda              = _sum_field(q_inc, "ebitda")
        net_income          = _sum_field(q_inc, "netIncome")
        interest_expense    = _sum_field(q_inc, "interestExpense")
        operating_cash_flow = _sum_field(q_cf,  "operatingCashflow")

        # Capex: sum then negate if positive (same sign fix as annual standardizer)
        capex_raw = _sum_field(q_cf, "capitalExpenditures")
        capital_expenditures = (-capex_raw if capex_raw is not None and capex_raw > 0 else capex_raw)

        # FCF: OCF + capex (capex is negative)
        if operating_cash_flow is not None and capital_expenditures is not None:
            free_cash_flow = operating_cash_flow + capital_expenditures
        else:
            free_cash_flow = None

        # ── Effective tax rate: average across valid quarters ─────────────────
        tax_rates = []
        for q in q_inc:
            tax    = _m(q.get("incomeTaxExpense"))
            pretax = _m(q.get("incomeBeforeTax"))
            if pretax is None or pretax == 0 or tax is None:
                continue
            rate = tax / pretax
            if 0 < rate < 1:
                tax_rates.append(rate)

        effective_tax_rate = sum(tax_rates) / len(tax_rates) if tax_rates else None

        # ── Populate output.ttm ───────────────────────────────────────────────
        output.ttm = {
            "revenue":              revenue,
            "ebitda":               ebitda,
            "net_income":           net_income,
            "operating_cash_flow":  operating_cash_flow,
            "capital_expenditures": capital_expenditures,
            "free_cash_flow":       free_cash_flow,
            "interest_expense":     interest_expense,
            "effective_tax_rate":   effective_tax_rate,
            "ttm_quarters_included": ttm_quarters_included,
            "ttm_as_of_date":       ttm_as_of_date,
        }

        logger.info(
            "Engine 1 | compute_ttm | %s | %d quarters | as_of %s",
            output.meta.ticker,
            ttm_quarters_included,
            ttm_as_of_date,
        )

    except Exception as exc:
        logger.error("Engine 1 | compute_ttm | failed: %s", exc)
        output.ttm = {"error": "TTM computation failed"}

    return output
