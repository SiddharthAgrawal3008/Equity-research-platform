"""
Mock Bus Data — Complete mock output for every bus key.
=======================================================

Each constant matches the bus key schema defined in the Data Pipeline
Architecture document (Section 7) AND the Engine1Output data contract
(engine1_output_contract.py).

Stub engines return these mocks so the full pipeline works end-to-end
before any real engine is built. When a team member implements their
engine, they replace the stub's return value with real computed data —
but keep updating this mock file so downstream engines can still
develop against it.

Company: AAPL (Apple Inc.) — 6 fiscal years (FY2020–FY2025)
Source:  Divyansh's live Engine 1 output (Alpha Vantage + Finnhub),
         cross-checked with SEC 10-K filings and stockanalysis.com.

CONVENTIONS (matching Engine1Output contract):
    Monetary unit     : USD millions (float)
    Percentages       : Decimals — 0.25 means 25%, NOT 25
    Time-series order : Chronological, OLDEST first: [2020, 2021, ...]
    Missing data      : None — never substitute 0 for a missing value
"""

# ---------------------------------------------------------------------------
# financial_data  (produced by Engine 1 — Owner: Divyansh)
# ---------------------------------------------------------------------------
# Structure mirrors Engine1Output dataclass: meta, financials, derived, ttm, quality
# Represented as a plain dict (matching the pipeline bus pattern on main).

MOCK_FINANCIAL_DATA: dict = {

    # ── Company Metadata ──────────────────────────────────────────────────
    "meta": {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "TECHNOLOGY",
        "industry": "CONSUMER ELECTRONICS",
        "exchange": "NASDAQ",
        "currency": "USD",
        "current_price": 260.48,
        "market_cap": 3828515.865,           # USD millions
        "shares_outstanding": 14681.14,      # millions
        "enterprise_value": 3904958.865,     # market_cap + total_debt - cash
        "description": (
            "Apple Inc. is an American multinational technology company "
            "that specializes in consumer electronics, computer software, "
            "and online services."
        ),
    },

    # ── Annual Financial Statements ───────────────────────────────────────
    # All lists aligned to years[], oldest first. All monetary values USD M.
    "financials": {
        "years": [2020, 2021, 2022, 2023, 2024, 2025],

        # --- Income Statement ---
        "revenue":              [274515.0, 365817.0, 394328.0, 383285.0, 391035.0, 416161.0],
        "gross_profit":         [104956.0, 152836.0, 170782.0, 169148.0, 180683.0, 195201.0],
        "ebit":                 [69964.0,  111852.0, 119437.0, 114301.0, 123216.0, 132729.0],
        "ebitda":               [81020.0,  123136.0, 130541.0, 125820.0, 134661.0, 144427.0],
        "depreciation_amortisation": [11056.0, 11284.0, 11104.0, 11519.0, 11445.0, 11698.0],
        "net_income":           [57411.0,  94680.0,  99803.0,  96995.0,  93736.0,  112010.0],
        "interest_expense":     [2873.0,   2645.0,   2931.0,   3933.0,   None,     None],

        # --- Balance Sheet ---
        "total_assets":         [323888.0, 351002.0, 352755.0, 352583.0, 364980.0, 359241.0],
        "current_assets":       [143713.0, 134836.0, 135405.0, 143566.0, 152987.0, 147957.0],
        "current_liabilities":  [105392.0, 125481.0, 153982.0, 145308.0, 176392.0, 165631.0],
        "cash_and_equivalents": [38016.0,  34940.0,  23646.0,  29965.0,  29943.0,  35934.0],
        "inventory":            [4061.0,   6580.0,   4946.0,   6331.0,   7286.0,   5718.0],
        "accounts_receivable":  [16120.0,  26278.0,  28184.0,  29508.0,  33410.0,  39777.0],
        "total_debt":           [112436.0, 124719.0, 120069.0, 111088.0, 119059.0, 112377.0],
        "total_liabilities":    [258549.0, 287912.0, 302083.0, 290437.0, 308030.0, 285508.0],
        "total_equity":         [65339.0,  63090.0,  50672.0,  62146.0,  56950.0,  73733.0],
        "retained_earnings":    [14966.0,  5562.0,   -3068.0,  -214.0,   -19154.0, -14264.0],
        "goodwill":             [None,     None,     None,     None,     None,     None],
        "net_debt":             [74420.0,  89779.0,  96423.0,  81123.0,  89116.0,  76443.0],
        "net_working_capital":  [38321.0,  9355.0,   -18577.0, -1742.0,  -23405.0, -17674.0],

        # --- Cash Flow Statement ---
        "operating_cash_flow":  [80674.0,  104038.0, 122151.0, 110543.0, 118254.0, 111482.0],
        "capital_expenditures": [-7309.0,  -11085.0, -10708.0, -10959.0, -9447.0,  -12715.0],
        "free_cash_flow":       [73365.0,  92953.0,  111443.0, 99584.0,  108807.0, 98767.0],
    },

    # ── Pre-computed Derived Metrics ──────────────────────────────────────
    # Computed from the raw financials above. Engine 2 can use these directly
    # or recompute from raw data. Provided here so Engine 2 doesn't have to
    # wait for Divyansh's "later steps" to be implemented.
    "derived": {

        # Margins (decimals, aligned to years)
        "gross_margin":   [0.3824, 0.4177, 0.4331, 0.4413, 0.4622, 0.4690],
        "ebit_margin":    [0.2549, 0.3057, 0.3028, 0.2982, 0.3151, 0.3190],
        "ebitda_margin":  [0.2952, 0.3366, 0.3310, 0.3283, 0.3443, 0.3471],
        "net_margin":     [0.2091, 0.2588, 0.2531, 0.2530, 0.2397, 0.2692],

        # YoY growth rates (decimals, length = len(years) - 1)
        "revenue_yoy":     [0.3327, 0.0779, -0.0280, 0.0202, 0.0642],
        "ebitda_yoy":      [0.5198, 0.0601, -0.0362, 0.0703, 0.0725],
        "net_income_yoy":  [0.6492, 0.0541, -0.0281, -0.0336, 0.1950],
        "fcf_yoy":         [0.2670, 0.1990, -0.1064, 0.0926, -0.0923],

        # Compound growth (single float, over full 5-year window)
        "revenue_cagr": 0.0869,

        # Return metrics (decimals, aligned to years)
        "roe":  [0.8789, 1.5009, 1.9700, 1.5608, 1.6460, 1.5191],
        "roic": [0.3231, 0.5040, 0.5849, 0.5602, 0.5326, 0.6023],

        # Effective tax rate (decimals, aligned to years)
        # Approximated as (EBIT - Net Income) / EBIT for years where
        # precise tax_expense isn't available separately
        "effective_tax_rate": [0.1794, 0.1535, 0.1642, 0.1514, 0.2392, 0.1562],

        # Leverage
        "net_debt_to_ebitda": [0.919, 0.729, 0.739, 0.645, 0.662, 0.529],
        "interest_coverage":  [24.36, 42.29, 40.75, 29.07, None, None],

        # Trend flags
        "gross_margin_trend":      "improving",
        "ebit_margin_trend":       "improving",
        "ebitda_margin_trend":     "improving",
        "net_margin_trend":        "stable",
        "revenue_growth_trend":    "stable",
        "roe_trend":               "stable",
        "roic_trend":              "stable",
        "fcf_trend":               "stable",
    },

    # ── TTM (Trailing Twelve Months) ──────────────────────────────────────
    # For the mock, TTM = most recent fiscal year (FY2025, ending Sep 2025).
    # When Divyansh builds real TTM from quarterly data, these will be
    # more current. All monetary values in USD millions.
    "ttm": {
        "revenue": 416161.0,
        "gross_profit": 195201.0,
        "ebit": 132729.0,
        "ebitda": 144427.0,
        "net_income": 112010.0,
        "depreciation_amortisation": 11698.0,
        "interest_expense": None,
        "operating_cash_flow": 111482.0,
        "capital_expenditures": -12715.0,
        "free_cash_flow": 98767.0,
        "effective_tax_rate": 0.1562,
    },

    # ── Data Quality Flags ────────────────────────────────────────────────
    "quality": {
        "is_valid": True,
        "missing_fields": ["interest_expense_2024", "interest_expense_2025"],
        "warnings": [
            "Interest expense missing for FY2024 and FY2025 — cost of debt "
            "will use last available value (FY2023: $3,933M)"
        ],
        "errors": [],
        "net_income_cf_reconciled": True,
        "balance_sheet_balanced": True,
        "is_bank": False,
        "is_reit": False,
        "is_negative_equity": False,
        "years_of_history": 6,
    },
}


# ---------------------------------------------------------------------------
# valuation  (produced by Engine 2 — Owner: Siddharth)
# ---------------------------------------------------------------------------
# This mock will be replaced by real Engine 2 output once built.
# Structure aligned to Engine 2 Output Data Contract v1.0.
MOCK_VALUATION: dict = {
    "dcf": {
        "status": "success",
        "intrinsic_value_per_share": 198.40,
        "enterprise_value": 3150000.0,
        "equity_value": 3073557.0,
        "upside_pct": -0.2384,
        "wacc": 0.092,
        "cost_of_equity": 0.1080,
        "cost_of_debt": 0.035,
        "beta_used": 1.18,
        "risk_free_rate": 0.043,
        "equity_risk_premium": 0.055,
        "debt_weight": 0.029,
        "equity_weight": 0.971,
        "projection_years": 5,
        "projected_revenue": [441333.0, 464703.0, 486119.0, 505564.0, 523060.0],
        "projected_fcf": [106500.0, 113955.0, 121932.0, 130468.0, 139601.0],
        "projected_growth_rates": [0.0605, 0.0529, 0.0461, 0.0400, 0.0346],
        "projected_fcf_margins": [0.2414, 0.2452, 0.2508, 0.2580, 0.2669],
        "terminal_growth_rate": 0.025,
        "terminal_value": 2137500.0,
        "terminal_value_pct": 0.678,
    },
    "relative": {
        "status": "success",
        "peers": [
            {"ticker": "MSFT", "company_name": "Microsoft Corp",
             "market_cap": 3100000.0, "ev_ebitda": 25.1, "pe_ratio": 34.2, "pb_ratio": 12.1},
            {"ticker": "GOOGL", "company_name": "Alphabet Inc",
             "market_cap": 2100000.0, "ev_ebitda": 18.5, "pe_ratio": 24.8, "pb_ratio": 7.2},
            {"ticker": "AMZN", "company_name": "Amazon.com Inc",
             "market_cap": 2000000.0, "ev_ebitda": 20.3, "pe_ratio": 42.1, "pb_ratio": 8.5},
            {"ticker": "META", "company_name": "Meta Platforms Inc",
             "market_cap": 1600000.0, "ev_ebitda": 16.8, "pe_ratio": 26.5, "pb_ratio": 9.3},
        ],
        "num_peers": 4,
        "ev_ebitda_company": 27.04,
        "ev_ebitda_peers_avg": 20.18,
        "ev_ebitda_peers_median": 19.40,
        "ev_ebitda_implied_value": 186.80,
        "pe_company": 34.13,
        "pe_peers_avg": 31.90,
        "pe_peers_median": 30.35,
        "pe_implied_value": 231.50,
        "pb_company": 51.93,
        "pb_peers_median": 8.90,
    },
    "sensitivity": {
        "wacc_range": [0.072, 0.082, 0.092, 0.102, 0.112],
        "growth_range": [0.010, 0.0175, 0.025, 0.0325, 0.040],
        "value_matrix": [
            [245.10, 268.30, 298.00, 338.20, 398.50],
            [218.40, 235.40, 256.50, 283.50, 320.10],
            [196.80, 210.20, 226.40, 246.50, 271.80],
            [179.00, 189.80, 202.60, 218.10, 237.00],
            [164.10, 173.00, 183.30, 195.40, 210.10],
        ],
        "base_case_wacc_idx": 2,
        "base_case_growth_idx": 2,
    },
    "summary": {
        "current_price": 260.48,
        "dcf_value": 198.40,
        "relative_value_low": 186.80,
        "relative_value_high": 231.50,
        "valuation_range_low": 165.0,
        "valuation_range_mid": 198.40,
        "valuation_range_high": 235.0,
        "upside_pct": -0.2384,
        "verdict": "Overvalued",
        "confidence": "Medium",
    },
    "meta": {
        "computed_at": "2026-04-13T00:00:00Z",
        "model_version": "engine2_v1.0_mock",
        "assumptions": {
            "projection_years": 5,
            "terminal_method": "gordon_growth",
            "dcf_method": "fcff",
        },
        "warnings": [],
        "data_quality_flag": "clean",
    },
}


# ---------------------------------------------------------------------------
# risk_metrics  (produced by Engine 3 — Owner: Siddharth)
# ---------------------------------------------------------------------------
MOCK_RISK_METRICS: dict = {
    "market_risk": {
        "beta": 1.18,
        "beta_source": "calculated",
        "volatility_annual": 0.27,
        "sharpe_ratio": 1.05,
        "max_drawdown": -0.28,
        "max_drawdown_start": "2022-01",
        "max_drawdown_end": "2022-06",
        "var_95": -0.032,
    },
    "financial_health": {
        "altman_z_score": 4.2,
        "altman_z_zone": "Safe",
        "interest_coverage": 29.8,
        "debt_to_ebitda": 0.78,
        "current_ratio": 0.89,
        "quick_ratio": 0.86,
    },
    "red_flags": [],
}


# ---------------------------------------------------------------------------
# nlp_insights  (produced by Engine 4 — Owner: Annant)
# ---------------------------------------------------------------------------
MOCK_NLP_INSIGHTS: dict = {
    "sentiment": {
        "overall_score": 0.62,
        "management_optimism": 0.71,
        "risk_word_frequency": 0.04,
    },
    "red_flags": [
        "Increasing mention of supply chain risk",
        "Declining forward guidance language",
    ],
    "key_themes": ["AI investment", "Services growth", "Capital returns"],
    "source_coverage": {
        "earnings_transcripts": 4,
        "annual_reports": 2,
    },
}


# ---------------------------------------------------------------------------
# report  (produced by Engine 5 — Owner: Naman)
# ---------------------------------------------------------------------------
MOCK_REPORT: dict = {
    "title": "Equity Research Report — Apple Inc. (AAPL)",
    "recommendation": "HOLD",
    "target_price": 198.40,
    "sections": {
        "business_summary": (
            "Apple Inc. designs, manufactures, and markets smartphones, "
            "personal computers, tablets, wearables, and accessories worldwide. "
            "The company also operates a growing services segment."
        ),
        "financial_performance": (
            "Revenue CAGR of ~8.7% over 5 years with stable margins. "
            "Free cash flow generation remains strong at ~$99B TTM."
        ),
        "valuation_range": (
            "DCF intrinsic value of $198.40 implies ~24% downside from current "
            "price of $260.48. Relative valuation range: $187-$232."
        ),
        "key_risks": (
            "Smartphone market saturation, regulatory headwinds in EU and China, "
            "supply chain concentration in Asia."
        ),
        "investment_thesis": (
            "Strong ecosystem moat and expanding services revenue, but current "
            "valuation appears stretched relative to DCF fair value."
        ),
    },
    "generated_at": "2026-04-16T00:00:00Z",
}
