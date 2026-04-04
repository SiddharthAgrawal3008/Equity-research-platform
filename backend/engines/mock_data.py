# ──────────────────────────────────────────────────────────────
# TEMPORARY FILE — delete when Engine 1 (financial_data.py) is complete.
#
# This module provides mock raw_financials data that mimics the
# output schema of Engine 1.  It allows Engine 2 (and downstream
# engines) to be developed and tested before Engine 1 is wired up.
# When Engine 1 ships, replace the import in every consumer:
#     from backend.engines.mock_data import MOCK_RAW_FINANCIALS
#  →  result = financial_data.run("AAPL")
# ──────────────────────────────────────────────────────────────

MOCK_RAW_FINANCIALS: dict = {
    "ticker": "AAPL",
    "source": "mock",
    "years": [2020, 2021, 2022, 2023, 2024],
    "income_statement": {
        "revenue":       [274515.0, 365817.0, 394328.0, 383285.0, 410500.0],
        "cogs":          [169559.0, 212981.0, 223546.0, 214137.0, 228400.0],
        "gross_profit":  [104956.0, 152836.0, 170782.0, 169148.0, 182100.0],
        "salaries":      [18916.0, 23086.0, 26251.0, 27280.0, 29100.0],
        "rent_overhead": [6180.0, 7100.0, 7800.0, 8100.0, 8500.0],
        "da":            [11056.0, 11284.0, 11104.0, 11519.0, 11800.0],
        "interest":      [2873.0, 2645.0, 2931.0, 3933.0, 3600.0],
        "ebt":           [67091.0, 109207.0, 119437.0, 114025.0, 125000.0],
        "taxes":         [9680.0, 14527.0, 19300.0, 16741.0, 18500.0],
        "net_income":    [57411.0, 94680.0, 100137.0, 97284.0, 106500.0],
    },
    "balance_sheet": {
        "cash":              [38016.0, 34940.0, 23646.0, 29965.0, 32000.0],
        "accounts_rec":      [16120.0, 26278.0, 28184.0, 29508.0, 31000.0],
        "inventory":         [4061.0, 6580.0, 6331.0, 6232.0, 6800.0],
        "ppe":               [36766.0, 39440.0, 42117.0, 43715.0, 45000.0],
        "total_assets":      [323888.0, 351002.0, 352755.0, 352583.0, 365000.0],
        "accounts_pay":      [42296.0, 54763.0, 64115.0, 62611.0, 65000.0],
        "debt":              [112436.0, 124719.0, 120069.0, 111088.0, 105000.0],
        "total_liab":        [258549.0, 287912.0, 302083.0, 290437.0, 285000.0],
        "retained_earnings": [14966.0, 5562.0, -3068.0, 214.0, 5000.0],
        "equity":            [65339.0, 63090.0, 50672.0, 62146.0, 80000.0],
    },
    "cash_flow": {
        "cfo":        [80674.0, 104038.0, 122151.0, 110543.0, 118000.0],
        "capex":      [-7309.0, -11085.0, -10708.0, -10959.0, -11500.0],
        "cfi":        [-4289.0, -14545.0, -22354.0, -3538.0, -8000.0],
        "cff":        [-86820.0, -93353.0, -110749.0, -108488.0, -112000.0],
        "net_change": [-10435.0, -3860.0, -10952.0, -1483.0, -2000.0],
    },
    "market_data": {
        "current_price": 178.72,
        "shares_outstanding": 15460.0,
        "market_cap": 2762611.2,
    },
}
