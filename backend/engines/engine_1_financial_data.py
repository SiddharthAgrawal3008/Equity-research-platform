"""
Engine 1 — Financial Data Engine (Owner: Divyansh)
===================================================

Input:  ticker (from bus)
Output: financial_data (to bus)
"""

from backend.pipeline.base_engine import BaseEngine
from backend.engines.financial_data import fetch_raw
from backend.engines.engine_1.engine1_standardizer import standardize
from backend.engines.engine_1.engine1_derived import compute_derived
from backend.engines.engine_1.engine1_ttm import compute_ttm
from backend.engines.engine_1.engine1_market_data import build_market_data
from backend.engines.engine_1.engine1_validator import validate


def _to_bus(out) -> dict:
    m = out.meta
    f = out.financials
    return {
        "meta": {
            "ticker":             m.ticker,
            "company_name":       m.company_name,
            "sector":             m.sector,
            "industry":           m.industry,
            "exchange":           getattr(m, "exchange", ""),
            "currency":           m.currency,
            "current_price":      m.current_price,
            "market_cap":         m.market_cap,
            "shares_outstanding": m.shares_outstanding,
            "enterprise_value":   m.enterprise_value,
        },
        "quality":    out.quality,
        "years":      f.years,
        "financials": {
            "revenue":                    f.revenue,
            "gross_profit":               f.gross_profit,
            "ebit":                       f.ebit,
            "ebitda":                     f.ebitda,
            "net_income":                 f.net_income,
            "interest_expense":           f.interest_expense,
            "cost_of_revenue":            f.cost_of_revenue,
            "depreciation_amortisation":  f.depreciation_amortisation,
            "pre_tax_income":             f.pre_tax_income,
            "tax_expense":                f.tax_expense,
            "research_and_development":   f.research_and_development,
            "selling_general_admin":      f.selling_general_admin,
            "total_assets":               f.total_assets,
            "current_assets":             f.current_assets,
            "current_liabilities":        f.current_liabilities,
            "cash_and_equivalents":       f.cash_and_equivalents,
            "inventory":                  f.inventory,
            "accounts_receivable":        f.accounts_receivable,
            "total_debt":                 f.total_debt,
            "total_liabilities":          f.total_liabilities,
            "retained_earnings":          f.retained_earnings,
            "goodwill":                   f.goodwill,
            "long_term_debt":             f.long_term_debt,
            "total_equity":               f.total_equity,
            "accounts_payable":           getattr(f, "accounts_payable", None),
            "net_debt":                   f.net_debt,
            "net_working_capital":        f.net_working_capital,
            "operating_cash_flow":        f.operating_cash_flow,
            "capex":                      f.capex,
            "free_cash_flow":             f.free_cash_flow,
            "dividends_paid":             f.dividends_paid,
            "share_buybacks":             f.share_buybacks,
            "net_debt_issuance":          f.net_debt_issuance,
        },
        "ttm":         out.ttm,
        "market_data": out.market_data,
        "margins":     out.margins,
        "growth":      out.growth,
        "returns":     out.returns,
        "efficiency":  out.efficiency,
        "trend_flags": out.trend_flags,
    }


class FinancialDataEngine(BaseEngine):
    name = "engine_1"
    requires = ["ticker"]
    produces = "financial_data"

    def run(self, context: dict) -> dict:
        ticker = context["ticker"]

        raw = fetch_raw(ticker)
        out = standardize(raw)
        out = compute_derived(out)
        out = compute_ttm(out, raw)

        market_data, md_warnings = build_market_data(ticker, out.meta.current_price)
        out.market_data = market_data
        out.quality["warnings"].extend(md_warnings)

        validate(out)

        return _to_bus(out)
