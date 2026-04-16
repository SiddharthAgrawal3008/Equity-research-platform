"""
========================================================================
SHARED CONTEXT — Central Data Contract
Automated Equity Research & Valuation Intelligence Platform
========================================================================

WHAT THIS FILE IS
-----------------
This file defines the SharedContext object that the Central Orchestrator
instantiates and passes between all engines. Each engine reads from and
writes to its designated namespace. No engine communicates directly with
another — all inter-engine data flows through this object.

EXECUTION ORDER (managed by Orchestrator)
------------------------------------------
  Engine 1  →  writes  context.engine1
  Engine 3  →  reads   context.engine1,  writes context.engine3
  Engine 2  →  reads   context.engine1 + context.engine3
  Engine 4  →  reads   context.engine1
  Engine 5  →  reads   context.engine1 + context.engine2
               + context.engine3 + context.engine4

CONVENTIONS
-----------
  Monetary values  : USD millions (float)
  Percentages      : decimals — 0.25 means 25%, NOT 25
  Time-series      : chronological, OLDEST first → [2020, 2021, 2022 ...]
  Missing data     : None — never substitute 0 for a missing value
  Years list       : always present; all time-series lists align to it by index

DO NOT MODIFY field names or types without:
  1. Updating this file
  2. Bumping the contract version
  3. Notifying ALL engine owners

Contract Version : 1.0
Date             : April 2026
========================================================================
"""

from dataclasses import dataclass, field
from typing import Optional


# ── ENGINE 1 SUB-OBJECTS ─────────────────────────────────────────────────────

@dataclass
class CompanyMeta:
    """
    Static company information.
    Populated by Engine 1. Read by Engine 3 (sector for Z-score branching,
    industry for beta fallback), Engine 2, and Engine 5.
    """
    ticker:       str    # e.g. "AAPL"
    company_name: str    # e.g. "Apple Inc."
    sector:       str    # GICS sector, e.g. "Technology", "Financials"
                         # Critical: Engine 3 uses this for Z-score exclusion logic
    industry:     str    # e.g. "Consumer Electronics"
                         # Used by Engine 3 for industry beta fallback on IPO stocks
    exchange:     str    # e.g. "NASDAQ", "NYSE"
    currency:     str    # Reporting currency, e.g. "USD"

    # Market data — required by Engine 2 for EV bridge (DCF → equity value → price)
    current_price:      float  # USD, latest closing price
    market_cap:         float  # USD millions
    shares_outstanding: float  # millions of diluted shares
    enterprise_value:   float  # USD millions = market_cap + total_debt - cash

    # Business description — consumed by Engine 5 for report narrative
    description: str    # one-paragraph business description


@dataclass
class AnnualFinancials:
    """
    Raw financial statement values — indexed by year (oldest → newest).
    All monetary values in USD millions.
    Populated by Engine 1. Consumed by Engine 3 for health metrics.

    IMPORTANT: Every list must have the same length as `years`.
    Index 0 = oldest year, index -1 = most recent year.
    """
    years: list[int]   # e.g. [2020, 2021, 2022, 2023, 2024]

    # ── Income Statement ──────────────────────────────────────────────────────
    revenue:          list[float]  # Total net revenue / net sales
    gross_profit:     list[float]  # Revenue - COGS
    ebit:             list[float]  # Operating income / EBIT
                                   # Used by Engine 3: interest coverage = EBIT / interest_expense
    ebitda:           list[float]  # EBIT + D&A
                                   # Used by Engine 3: debt_to_ebitda = total_debt / EBITDA
    net_income:       list[float]  # Bottom-line net income
    interest_expense: list[float]  # Always positive (cost of debt)
    cost_of_revenue:           list[float]           # COGS; used for gross_profit cross-check and efficiency metrics
    depreciation_amortisation: list[float]           # D&A; used for FCFF projection and EBITDA cross-check
    pre_tax_income:            list[float]            # EBT; denominator for effective_tax_rate → WACC and NOPAT
    tax_expense:               list[float]            # Numerator for effective_tax_rate → WACC and NOPAT
    research_and_development:  list[Optional[float]] # None if not reported
    selling_general_admin:     list[Optional[float]] # SG&A; None if not separated

    # ── Balance Sheet ─────────────────────────────────────────────────────────
    total_assets:         list[float]           # Used in Altman Z-score (X1, X3, X4)
    current_assets:       list[float]           # Used in current ratio and working capital
    current_liabilities:  list[float]           # Used in current ratio and quick ratio
    cash_and_equivalents: list[float]           # Cash + short-term investments; used in quick ratio
    inventory:            list[Optional[float]] # None for pure service companies
                                                # Subtracted from current assets for quick ratio
    accounts_receivable:  list[float]           # Used for channel stuffing red flag detection
    total_debt:           list[float]           # Short-term + long-term debt
    total_liabilities:    list[float]           # Used in Altman Z-score (X4)
    retained_earnings:    list[float]           # Used in Altman Z-score (X2)
    goodwill:             list[float]           # Monitored for write-down red flag
    market_capitalization: list[float]          # Used in Altman Z-score (X4: mkt equity / total liab)
    long_term_debt:            list[float]           # Separates LT from ST debt; capital structure analysis
    total_equity:              list[float]            # Used for ROE, P/B, D/E, WACC equity weight
    accounts_payable:          list[Optional[float]] # Used for ap_days efficiency metric
    net_debt:                  list[Optional[float]] # total_debt - cash; used in EV bridge
    net_working_capital:       list[Optional[float]] # current_assets - current_liabilities; used in FCFF projection

    # ── Cash Flow Statement ───────────────────────────────────────────────────
    operating_cash_flow: list[float]  # Cash from operations
                                      # Compared to net income for earnings quality red flag
    capex:               list[float]  # Capital expenditure — always NEGATIVE (cash outflow)
    free_cash_flow:      list[Optional[float]] # OCF + capex (capex is negative)
    dividends_paid:      list[Optional[float]] # Always negative; None if no dividends paid
    share_buybacks:      list[Optional[float]] # Always negative; None if no buybacks
    net_debt_issuance:   list[Optional[float]] # Positive = raised debt, negative = repaid


@dataclass
class Engine1Output:
    """
    The complete output that Engine 1 writes to context.engine1.

    Contains two layers:
      1. Raw financials (AnnualFinancials) — needed by Engine 3 for health metrics
      2. Pre-computed derived metrics (dicts) — flow through to Engine 5 untouched

    Engine 3 reads: meta (sector, industry) + financials (all fields)
    Engine 2 reads: meta + financials + all derived dicts + ttm + quality
    Engine 5 reads: everything
    """
    meta:       CompanyMeta      # Static company info + market data
    financials: AnnualFinancials # Raw financial statement values — indexed by year

    # ── Pre-computed derived metrics ──────────────────────────────────────────
    # These are computed by Engine 1 and flow to Engine 2 / Engine 5 unchanged.
    # Engine 3 does NOT consume these — it derives its own metrics from raw financials.

    margins: dict
    # Keys: gross_margin, ebit_margin, ebitda_margin, net_margin, ebt_margin
    # Values: list[float], decimals, e.g. 0.43 = 43%

    growth: dict
    # Keys: revenue_yoy, net_income_yoy, ebitda_yoy, fcf_yoy (all list[float], len = years-1)
    #       revenue_cagr, net_income_cagr (float, over full history window)

    returns: dict
    # Keys: roe, roa, roic (all list[float], decimals)
    # roe  = net_income / total_equity
    # roa  = net_income / total_assets
    # roic = NOPAT / invested_capital

    efficiency: dict
    # Keys: ar_days, ap_days (list[float])
    #       inv_days (list[Optional[float]] — None for service companies)

    cost_structure: dict
    # Keys: cogs_pct, salaries_pct, da_pct, interest_pct (all list[float], decimals)

    trend_flags: dict
    # Keys: gross_margin_trend, net_margin_trend, revenue_growth_trend, roic_trend
    # Values: "improving" | "deteriorating" | "stable"

    # ── TTM (Trailing Twelve Months) ──────────────────────────────────────────
    # Single float values computed from last 4 quarters.
    # Engine 2 uses these as the most current anchor for valuation projections.
    ttm: dict
    # Keys: revenue, gross_profit, ebit, ebitda, net_income,
    #       depreciation_amortisation, interest_expense, tax_expense,
    #       operating_cash_flow, capital_expenditures, free_cash_flow,
    #       effective_tax_rate
    # All monetary values in USD millions. effective_tax_rate is a decimal.

    # ── Data Quality Flags ────────────────────────────────────────────────────
    # Engine 2 MUST check quality['is_valid'] before running any valuation.
    # If is_valid is False, Engine 2 must raise an error or mark output as UNRELIABLE.
    quality: dict
    # Keys:
    #   is_valid               (bool)       — False = critical data issues found
    #   missing_fields         (list[str])  — field names that are None/missing
    #   warnings               (list[str])  — non-critical, e.g. "R&D not reported"
    #   errors                 (list[str])  — critical, e.g. "Balance sheet does not balance"
    #   net_income_cf_reconciled (bool)     — net income matches CF statement starting point
    #   balance_sheet_balanced (bool)       — assets == liabilities + equity
    #   debt_change_reconciled (bool)       — BS debt change matches financing CF
    #   is_bank                (bool)       — Engine 2 adjusts WACC logic for banks
    #   is_reit                (bool)       — Engine 2 uses FFO instead of FCF
    #   is_negative_equity     (bool)       — P/B and D/E ratios unreliable
    #   years_of_history       (int)        — how many annual periods loaded successfully


# ── ENGINE 3 OUTPUT ───────────────────────────────────────────────────────────

@dataclass
class Engine3Output:
    """
    Output that Engine 3 writes to context.engine3 after completion.

    CRITICAL DEPENDENCY:
      Engine 2 reads `beta` immediately after Engine 3 finishes.
      The orchestrator must abort if beta is None or out of range (0.0, 5.0).

    Engine 5 reads everything else when building the final report.
    """

    # ── Beta (Engine 2 hard dependency) ───────────────────────────────────────
    beta: float
    # Adjusted beta: 0.67 × raw_beta + 0.33 × 1.0 (Bloomberg adjustment)
    # Used by Engine 2 as the core input to WACC cost of equity (CAPM)

    beta_source: str
    # "calculated"        — computed from 2yr weekly price regression vs ^GSPC
    # "industry_fallback" — used when < MIN_PRICE_HISTORY_YEARS of data available

    # ── Market Risk Metrics ───────────────────────────────────────────────────
    historical_volatility: float
    # Annualised std dev of weekly returns, e.g. 0.28 = 28%

    sharpe_ratio: float
    # Risk-adjusted return: (annualised_return - RISK_FREE_RATE) / historical_volatility
    # Uses shared_config.RISK_FREE_RATE and SHARPE_LOOKBACK_YEARS

    max_drawdown: float
    # Max peak-to-trough decline over DRAWDOWN_LOOKBACK_YEARS window
    # e.g. -0.44 means a 44% peak-to-trough decline

    max_drawdown_start: str   # YYYY-MM — date of peak before largest drawdown
    max_drawdown_end:   str   # YYYY-MM — date of trough at end of largest drawdown

    var_95_daily: float
    # Historical simulation VaR at 95% confidence, 1-day horizon
    # e.g. -0.032 means a 3.2% daily loss at 95% confidence

    # ── Fundamental Health Metrics ────────────────────────────────────────────
    altman_z_score: Optional[float]
    # Z-score value. None if sector is in ZSCORE_EXCLUDED_SECTORS (Financials, Real Estate)
    # or if insufficient data to compute.

    altman_z_zone: Optional[str]
    # "Safe"     — Z-score > ZSCORE_SAFE (2.99)
    # "Grey"     — ZSCORE_DISTRESS (1.81) <= Z-score <= ZSCORE_SAFE (2.99)
    # "Distress" — Z-score < ZSCORE_DISTRESS (1.81)
    # "N/A"      — sector excluded or insufficient data

    interest_coverage: Optional[float]
    # EBIT / interest_expense. None if interest_expense is 0 or missing.

    debt_to_ebitda: Optional[float]
    # total_debt / EBITDA. None if EBITDA <= 0.

    current_ratio: float
    # current_assets / current_liabilities

    quick_ratio: float
    # (current_assets - inventory) / current_liabilities

    # ── Red Flags ─────────────────────────────────────────────────────────────
    red_flags: list[str]
    # List of triggered alert strings. Empty list [] if none triggered.
    # Example entries:
    #   "Receivables growing 2.3x faster than revenue (2022–2024)"
    #   "Operating cash flow below net income in 3 of 5 years"
    #   "Goodwill increased >20% YoY with no disclosed acquisition (2023)"


# ── SHARED CONTEXT (ROOT OBJECT) ─────────────────────────────────────────────

@dataclass
class SharedContext:
    """
    The single object instantiated by the Orchestrator and passed to every engine.

    Each engine writes only to its own namespace.
    Engines must never write to another engine's namespace.

    ORCHESTRATOR VALIDATION CHECKPOINTS:
    ─────────────────────────────────────
    After Engine 1 completes (before Engine 3 starts):
      ✓ context.engine1.financials is not None       → else ABORT
      ✓ context.engine1.meta.sector is not None      → else ABORT (Z-score logic undefined)
      ✓ len(context.engine1.financials.years) >= 3   → else WARN (minimum 3 years required)
      ✓ all revenue values > 0                       → else ABORT (data quality failure)

    After Engine 3 completes (before Engine 2 starts):
      ✓ context.engine3.beta is not None             → else ABORT (Engine 2 needs WACC)
      ✓ 0.0 < context.engine3.beta < 5.0             → else ABORT (beta out of valid range)
      ✓ context.engine3.beta_source in
          ['calculated', 'industry_fallback']         → else ABORT (unknown source)
    """
    ticker:  str

    engine1: Optional[Engine1Output] = None
    engine2: Optional[dict]          = None  # Engine 2 (Valuation) output namespace
    engine3: Optional[Engine3Output] = None
    engine4: Optional[dict]          = None  # Engine 4 (NLP Intelligence) output namespace
    engine5: Optional[dict]          = None  # Engine 5 (Report Generation) output namespace
