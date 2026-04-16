"""
Mock financial data for pipeline testing.

Simulates the output of Engine 1 (Financial Data Engine) written to
context["financial_data"].  Uses Apple Inc. (AAPL) data.

All monetary values are in USD millions unless noted otherwise.
"""

MOCK_FINANCIAL_DATA: dict = {
    # ── META ───────────────────────────────────────────────────────────
    "meta": {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "TECHNOLOGY",
        "industry": "CONSUMER ELECTRONICS",
        "current_price": 260.48,          # USD per share
        "market_cap": 3828515.865,        # USD millions
        "shares_outstanding": 14681.14,   # millions
        "enterprise_value": 3904958.865,  # USD millions
    },

    # ── FINANCIALS (time-series, oldest → newest, USD millions) ────────
    "financials": {
        "years": [2020, 2021, 2022, 2023, 2024, 2025],

        # Income Statement
        "revenue":              [274515.0, 365817.0, 394328.0, 383285.0, 391035.0, 416161.0],
        "gross_profit":         [104956.0, 152836.0, 170782.0, 169148.0, 180683.0, 195201.0],
        "ebit":                 [69964.0,  111852.0, 119437.0, 114301.0, 123216.0, 132729.0],
        "ebitda":               [81020.0,  123136.0, 130541.0, 125820.0, 134661.0, 144427.0],
        "depreciation_amortisation": [11056.0, 11284.0, 11104.0, 11519.0, 11445.0, 11698.0],
        "net_income":           [57411.0,  94680.0,  99803.0,  96995.0,  93736.0,  112010.0],
        "interest_expense":     [2873.0,   2645.0,   2931.0,   3933.0,   None,     None],

        # Balance Sheet
        "total_assets":         [323888.0, 351002.0, 352755.0, 352583.0, 364980.0, 359241.0],
        "current_assets":       [143713.0, 134836.0, 135405.0, 143566.0, 152987.0, 147957.0],
        "current_liabilities":  [105392.0, 125481.0, 153982.0, 145308.0, 176392.0, 165631.0],
        "cash_and_equivalents": [38016.0,  34940.0,  23646.0,  29965.0,  29943.0,  35934.0],
        "total_debt":           [112436.0, 124719.0, 120069.0, 111088.0, 119059.0, 112377.0],
        "total_equity":         [65339.0,  63090.0,  50672.0,  62146.0,  56950.0,  73733.0],
        "net_debt":             [74420.0,  89779.0,  96423.0,  81123.0,  89116.0,  76443.0],
        "net_working_capital":  [38321.0,  9355.0,   -18577.0, -1742.0,  -23405.0, -17674.0],

        # Cash Flow
        "operating_cash_flow":  [80674.0,  104038.0, 122151.0, 110543.0, 118254.0, 111482.0],
        "capital_expenditures": [-7309.0,  -11085.0, -10708.0, -10959.0, -9447.0,  -12715.0],
        "free_cash_flow":       [73365.0,  92953.0,  111443.0, 99584.0,  108807.0, 98767.0],
    },

    # ── DERIVED (pre-computed metrics, decimals) ───────────────────────
    "derived": {
        "ebitda_margin":  [0.2952, 0.3366, 0.3310, 0.3283, 0.3443, 0.3471],
        "effective_tax_rate": [0.1794, 0.1535, 0.1642, 0.1514, 0.2392, 0.1562],
        "revenue_yoy":     [0.3327, 0.0779, -0.0280, 0.0202, 0.0642],
        "revenue_cagr": 0.0869,
        "ebitda_margin_trend": "improving",
    },

    # ── TTM (trailing twelve months, single values, USD millions) ──────
    "ttm": {
        "revenue": 416161.0,
        "ebitda": 144427.0,
        "net_income": 112010.0,
        "free_cash_flow": 98767.0,
        "effective_tax_rate": 0.1562,
        "interest_expense": None,
        "depreciation_amortisation": 11698.0,
        "capital_expenditures": -12715.0,
        "operating_cash_flow": 111482.0,
    },

    # ── QUALITY (validation flags) ─────────────────────────────────────
    "quality": {
        "is_valid": True,
        "is_bank": False,
        "is_reit": False,
        "is_negative_equity": False,
        "years_of_history": 6,
        "warnings": [],
        "errors": [],
    },
}
