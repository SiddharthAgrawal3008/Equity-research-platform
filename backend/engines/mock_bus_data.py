# ──────────────────────────────────────────────────────────────
# Mock Bus Data — Engine 3 development and testing
#
# Provides MOCK_FINANCIAL_DATA (the bus format that Engine 1
# publishes) and MOCK_RISK_METRICS (the output Engine 3 produces).
#
# TEMPORARY — replace with real Engine 1 output when available.
# ──────────────────────────────────────────────────────────────

MOCK_FINANCIAL_DATA: dict = {
    "meta": {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "TECHNOLOGY",
        "industry": "Consumer Electronics",
        "market_cap": 3828515.865,
        "currency": "USD",
    },

    "quality": {
        "is_bank": False,
        "is_reit": False,
    },

    "years": [2020, 2021, 2022, 2023, 2024, 2025],

    "financials": {
        # ── Income Statement (USD millions) ────────────────────────
        "revenue":          [274515.0, 365817.0, 394328.0, 383285.0, 391035.0, 416161.0],
        "ebit":             [66288.0,  108949.0, 119437.0, 114301.0, 123216.0, 132729.0],
        "ebitda":           [81020.0,  123136.0, 130541.0, 125820.0, 134661.0, 144427.0],
        "net_income":       [57411.0,  94680.0,  99803.0,  96995.0,  105064.0, 112010.0],
        "interest_expense": [2873.0,   2645.0,   2931.0,   3933.0,   None,     None],

        # ── Balance Sheet (USD millions) ───────────────────────────
        "total_assets":         [323888.0, 351002.0, 352755.0, 352583.0, 364980.0, 359241.0],
        "current_assets":       [143713.0, 134836.0, 135405.0, 143566.0, 152987.0, 147957.0],
        "current_liabilities":  [105392.0, 125481.0, 153982.0, 145308.0, 176392.0, 165631.0],
        "cash_and_equivalents": [38016.0,  34940.0,  23646.0,  29965.0,  30299.0,  35934.0],
        "inventory":            [4061.0,   6580.0,   6331.0,   6232.0,   7286.0,   5718.0],
        "accounts_receivable":  [16120.0,  26278.0,  28184.0,  29508.0,  33410.0,  39777.0],
        "total_debt":           [112436.0, 124719.0, 120069.0, 111088.0, 106629.0, 112377.0],
        "total_liabilities":    [258549.0, 287912.0, 302083.0, 290437.0, 308030.0, 285508.0],
        "total_equity":         [65339.0,  63090.0,  50672.0,  62146.0,  56950.0,  73733.0],
        "retained_earnings":    [14966.0,  5562.0,   -3068.0,  214.0,    -19154.0, -14264.0],
        "goodwill":             [None,     None,     None,     None,     None,     None],
        "net_working_capital":  [38321.0,  9355.0,   -18577.0, -1742.0,  -23405.0, -17674.0],

        # ── Cash Flow (USD millions) ──────────────────────────────
        "operating_cash_flow": [80674.0,  104038.0, 122151.0, 110543.0, 118254.0, 111482.0],
        "free_cash_flow":      [73365.0,  92953.0,  111443.0, 99584.0,  108807.0, 100280.0],
    },

    # ── Market Price Data (for Engine 3) ───────────────────────────────
    # Empty in mock — Engine 3 handles gracefully with sector fallback.
    "market_data": {
        "daily_close": [],
        "daily_dates": [],
        "weekly_close": [],
        "weekly_dates": [],
        "benchmark_daily_close": [],
        "benchmark_daily_dates": [],
        "benchmark_weekly_close": [],
        "benchmark_weekly_dates": [],
        "current_price": 260.48,
        "benchmark_ticker": "^GSPC",
    },
}


MOCK_RISK_METRICS: dict = {
    "beta": {
        "value": 1.18,
        "raw_beta": 1.27,
        "source": "calculated",
        "benchmark": "^GSPC",
        "lookback_years": 2,
        "frequency": "W",
        "r_squared": 0.45,
    },
    "market_risk": {
        "historical_volatility": 0.27,
        "sharpe_ratio": 1.05,
        "max_drawdown": -0.28,
        "max_drawdown_start": "2022-01",
        "max_drawdown_end": "2022-06",
        "var_95_daily": -0.032,
        "annualized_return": 0.18,
    },
    "financial_health": {
        "altman_z_score": 4.2,
        "altman_z_zone": "Safe",
        "interest_coverage": 29.8,
        "debt_to_ebitda": 0.78,
        "current_ratio": 0.89,
        "quick_ratio": 0.86,
        "debt_to_equity": 1.52,
        "cash_to_debt": 0.32,
        "earnings_quality": 1.00,
    },
    "red_flags": [],
    "meta": {
        "computed_at": "2026-04-16T00:00:00Z",
        "config_used": {
            "risk_free_rate": 0.043,
            "beta_lookback": 2,
            "beta_frequency": "W",
            "beta_adjusted": True,
            "benchmark": "^GSPC",
            "var_confidence": 0.95,
            "drawdown_lookback": 5,
            "sharpe_lookback": 2,
        },
        "price_data_start": "2021-04-16",
        "price_data_end": "2026-04-15",
        "warnings": [],
        "financial_years_used": 6,
    },
}
