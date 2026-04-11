"""
Engine 1 → Engine 2 Data Contract
===================================
Official Python implementation of the Engine 1 → Engine 2 data contract.
Version 1.0 · April 2026

THIS FILE IS READ-ONLY ONCE CREATED.
- No engine should modify field names, types, or docstrings.
- Any change requires updating the PDF contract AND notifying the Engine 2
  developer before any code is merged.

CONVENTIONS:
    Monetary unit     : USD millions (float)
    Percentages       : Decimals — 0.25 means 25%, NOT 25
    Time-series order : Chronological, OLDEST first: [2020, 2021, 2022 ...]
    Missing data      : Use None — never substitute 0 for a missing value
    Years list        : Always present; all time-series lists align to it by index
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CompanyMeta:
    """Ticker, name, sector, current price, market cap, shares."""

    ticker: str
    """Exchange ticker, e.g. 'AAPL'"""

    current_price: float
    """Latest closing price (USD)"""

    market_cap: float
    """Shares × current price (USD millions)"""

    shares_outstanding: float
    """Diluted shares (millions)"""

    enterprise_value: float
    """market_cap + total_debt - cash (USD millions)"""

    sector: str
    """From yfinance /profile"""

    industry: str
    """From yfinance /profile"""


@dataclass
class IncomeStatement:
    """
    Revenue, EBIT, EBITDA, net income, D&A, interest, tax.
    All fields are time-series lists aligned to Engine1Output.years.
    All monetary values in USD millions.
    """

    revenue: List[float]
    """Net revenue / net sales (USD M)"""

    cost_of_revenue: List[float]
    """COGS (USD M)"""

    gross_profit: List[float]
    """revenue - cost_of_revenue (USD M)"""

    ebit: List[float]
    """Operating income (USD M)"""

    ebitda: List[float]
    """EBIT + D&A (USD M)"""

    depreciation_amortisation: List[float]
    """D&A — used to compute FCF (USD M)"""

    interest_expense: List[float]
    """Always positive (USD M)"""

    pre_tax_income: List[float]
    """EBT (USD M)"""

    tax_expense: List[float]
    """Positive = expense (USD M)"""

    net_income: List[float]
    """Bottom-line net income (USD M)"""

    research_and_development: List[Optional[float]]
    """None if not reported (USD M)"""

    selling_general_admin: List[Optional[float]]
    """SG&A; None if not separated (USD M)"""


@dataclass
class BalanceSheet:
    """
    Assets, liabilities, equity, debt, cash, NWC.
    All fields are time-series lists aligned to Engine1Output.years.
    All monetary values in USD millions.
    """

    cash_and_equivalents: List[float]
    """Cash + short-term investments (USD M)"""

    total_current_assets: List[float]
    """(USD M)"""

    total_assets: List[float]
    """(USD M)"""

    total_current_liabilities: List[float]
    """(USD M)"""

    total_debt: List[float]
    """Short-term + long-term debt (USD M)"""

    long_term_debt: List[float]
    """(USD M)"""

    total_equity: List[float]
    """Shareholders' equity (USD M)"""

    net_debt: List[float]
    """total_debt - cash; computed by Engine 1 (USD M)"""

    net_working_capital: List[float]
    """current_assets - current_liabilities (USD M)"""

    inventory: List[Optional[float]]
    """None for pure service companies (USD M)"""


@dataclass
class CashFlowStatement:
    """
    OCF, capex, FCF, dividends, buybacks, debt issuance.
    All fields are time-series lists aligned to Engine1Output.years.
    All monetary values in USD millions.
    """

    operating_cash_flow: List[float]
    """Cash from operations (USD M)"""

    capital_expenditures: List[float]
    """Always NEGATIVE — cash outflow (USD M)"""

    free_cash_flow: List[float]
    """OCF + capex (capex is negative) (USD M)"""

    net_debt_issuance: List[float]
    """Positive = raised, negative = repaid (USD M)"""

    dividends_paid: List[Optional[float]]
    """Negative; None if no dividends paid (USD M)"""

    share_buybacks: List[Optional[float]]
    """Negative; None if no buybacks (USD M)"""


@dataclass
class DerivedMetrics:
    """
    Pre-computed margins, growth rates, ratios, and trend flags.
    Computed by Engine 1 so Engine 2 does not need to re-derive them.

    Margin / ratio fields align to Engine1Output.years.
    YoY growth fields have length = len(years) - 1.
    Trend fields are strings: 'improving' | 'deteriorating' | 'stable'.
    """

    # --- Margins (decimal, aligned to years) ---
    gross_margin: List[float]
    """gross_profit / revenue"""

    ebit_margin: List[float]
    """ebit / revenue"""

    ebitda_margin: List[float]
    """ebitda / revenue"""

    net_margin: List[float]
    """net_income / revenue"""

    # --- Growth rates (decimal, length = len(years) - 1) ---
    revenue_yoy: List[float]
    """Year-over-year revenue growth (decimal)"""

    ebitda_yoy: List[float]
    """Year-over-year EBITDA growth (decimal)"""

    fcf_yoy: List[float]
    """Year-over-year FCF growth (decimal)"""

    # --- Compound growth (single float) ---
    revenue_cagr: float
    """Compound annual growth rate over full history window (decimal)"""

    # --- Return metrics (decimal, aligned to years) ---
    roe: List[float]
    """net_income / total_equity"""

    roic: List[float]
    """NOPAT / invested_capital"""

    # --- Other ratios (decimal, aligned to years) ---
    effective_tax_rate: List[float]
    """tax_expense / pre_tax_income"""

    net_debt_to_ebitda: List[float]
    """Leverage ratio"""

    interest_coverage: List[float]
    """EBIT / interest_expense"""

    # --- Trend flags ---
    gross_margin_trend: str
    """'improving' | 'deteriorating' | 'stable'"""

    ebit_margin_trend: str
    """'improving' | 'deteriorating' | 'stable'"""

    ebitda_margin_trend: str
    """'improving' | 'deteriorating' | 'stable'"""

    net_margin_trend: str
    """'improving' | 'deteriorating' | 'stable'"""

    revenue_growth_trend: str
    """'improving' | 'deteriorating' | 'stable'"""

    roe_trend: str
    """'improving' | 'deteriorating' | 'stable'"""

    roic_trend: str
    """'improving' | 'deteriorating' | 'stable'"""

    fcf_trend: str
    """'improving' | 'deteriorating' | 'stable'"""


@dataclass
class TTMData:
    """
    Trailing Twelve Months figures — single values, not lists.
    Computed by summing (or averaging) the last 4 reported quarters.
    All monetary values in USD millions.
    """

    revenue: float
    """Sum of last 4 quarters (USD M)"""

    ebitda: float
    """Sum of last 4 quarters (USD M)"""

    net_income: float
    """Sum of last 4 quarters (USD M)"""

    operating_cash_flow: float
    """Sum of last 4 quarters (USD M)"""

    capital_expenditures: float
    """Sum of last 4 quarters — negative (USD M)"""

    free_cash_flow: float
    """OCF + capex (USD M)"""

    effective_tax_rate: float
    """Average of last 4 quarters (decimal)"""

    interest_expense: float
    """Sum of last 4 quarters (USD M)"""


@dataclass
class DataQualityFlags:
    """
    Validation results, warnings, errors, and company-type flags.

    Engine 2 MUST check is_valid before running any calculations.
    If is_valid is False, Engine 2 must raise an error or mark its
    output as UNRELIABLE.
    """

    is_valid: bool
    """False = critical data issues found; Engine 2 must not proceed."""

    missing_fields: List[str]
    """Field names that are None when they should not be."""

    warnings: List[str]
    """Non-critical issues, e.g. 'R&D not reported'."""

    errors: List[str]
    """Critical issues, e.g. 'Balance sheet does not balance'."""

    net_income_cf_reconciled: bool
    """Net income matches cash flow statement starting point."""

    balance_sheet_balanced: bool
    """Assets == Liabilities + Equity"""

    is_bank: bool
    """Engine 2 adjusts WACC logic for banks."""

    is_reit: bool
    """Engine 2 uses FFO instead of FCF for REITs."""

    is_negative_equity: bool
    """P/B and D/E ratios are unreliable when equity is negative."""

    years_of_history: int
    """How many annual periods were loaded successfully."""


@dataclass
class Engine1Output:
    """
    Top-level output object produced by Engine 1.

    This is the single object passed from Engine 1 to all downstream engines.
    Engine 2 receives this object and MUST call quality.is_valid before use.

    Usage (Engine 2 example):
        data: Engine1Output = orchestrator.get_engine1_output()
        if not data.quality.is_valid:
            raise ValueError(data.quality.errors)
        revenue_history = data.income_statement.revenue   # list, oldest first
        ttm_revenue     = data.ttm.revenue                # single float
        net_debt        = data.balance_sheet.net_debt[-1] # most recent year
    """

    years: List[int]
    """
    Fiscal year integers, OLDEST first: [2020, 2021, 2022, ...].
    All time-series lists in sub-objects align to this by index.
    """

    meta: CompanyMeta
    """Ticker, name, sector, current price, market cap, shares."""

    income_statement: IncomeStatement
    """Revenue, EBIT, EBITDA, net income, D&A, interest, tax."""

    balance_sheet: BalanceSheet
    """Assets, liabilities, equity, debt, cash, NWC."""

    cash_flow: CashFlowStatement
    """OCF, capex, FCF, dividends, buybacks, debt issuance."""

    derived: DerivedMetrics
    """Pre-computed margins, growth rates, ratios, trend flags."""

    ttm: TTMData
    """Trailing Twelve Months figures for all key line items."""

    quality: DataQualityFlags
    """Validation results, warnings, errors, company type flags."""
