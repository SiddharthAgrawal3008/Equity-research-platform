"""
Mock Bus Data — Complete mock output for every bus key.
=======================================================

Each constant matches the bus key schema defined in the Data Pipeline
Architecture document (Section 7). Stub engines return these mocks so
the full pipeline works end-to-end before any real engine is built.

When a team member implements their engine, they replace the stub's
return value with real computed data — but keep updating this mock file
so downstream engines can still develop against it.

Company: AAPL (Apple Inc.) — 5 years (2020–2024)
"""

# ---------------------------------------------------------------------------
# financial_data  (produced by Engine 1 — Owner: Divyansh)
# ---------------------------------------------------------------------------
MOCK_FINANCIAL_DATA: dict = {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "income_statement": {
        "revenue": [274515.0, 365817.0, 394328.0, 383285.0, 410500.0],
        "net_income": [57411.0, 94680.0, 100137.0, 97284.0, 106500.0],
        "ebitda": [77344.0, 120233.0, 130541.0, 125820.0, 136800.0],
        "operating_income": [66288.0, 108949.0, 119437.0, 114301.0, 125000.0],
        "gross_profit": [104956.0, 152836.0, 170782.0, 169148.0, 182100.0],
        "interest_expense": [2873.0, 2645.0, 2931.0, 3933.0, 3600.0],
    },
    "balance_sheet": {
        "total_assets": [323888.0, 351002.0, 352755.0, 352583.0, 365000.0],
        "total_debt": [112436.0, 124719.0, 120069.0, 111088.0, 105000.0],
        "total_liabilities": [258549.0, 287912.0, 302083.0, 290437.0, 285000.0],
        "equity": [65339.0, 63090.0, 50672.0, 62146.0, 80000.0],
        "cash": [38016.0, 34940.0, 23646.0, 29965.0, 32000.0],
    },
    "cash_flow": {
        "operating_cf": [80674.0, 104038.0, 122151.0, 110543.0, 118000.0],
        "capex": [-7309.0, -11085.0, -10708.0, -10959.0, -11500.0],
        "free_cash_flow": [73365.0, 92953.0, 111443.0, 99584.0, 106500.0],
    },
    "ratios": {
        "roe": [0.879, 1.501, 1.976, 1.565, 1.331],
        "roic": [0.323, 0.504, 0.587, 0.562, 0.576],
        "gross_margin": [0.382, 0.418, 0.433, 0.441, 0.443],
        "net_margin": [0.209, 0.259, 0.254, 0.254, 0.259],
        "debt_to_equity": [1.721, 1.977, 2.369, 1.788, 1.313],
    },
    "market_data": {
        "current_price": 178.72,
        "market_cap": 2762611.2,
        "shares_outstanding": 15460.0,
        "historical_prices": [
            132.69, 177.57, 129.93, 192.53, 178.72,
        ],
    },
}

# ---------------------------------------------------------------------------
# valuation  (produced by Engine 2 — Owner: Siddharth)
# ---------------------------------------------------------------------------
MOCK_VALUATION: dict = {
    "dcf": {
        "wacc": 0.092,
        "terminal_growth": 0.025,
        "intrinsic_value": 198.40,
        "upside_pct": 0.11,
        "projected_fcf": [106500.0, 113955.0, 121932.0, 130468.0, 139601.0],
        "sensitivity_table": {
            "growth_rates": [0.02, 0.025, 0.03],
            "wacc_rates": [0.08, 0.092, 0.10],
            "values": [
                [225.10, 210.30, 198.00],
                [212.40, 198.40, 186.50],
                [200.80, 188.20, 177.00],
            ],
        },
    },
    "relative": {
        "ev_ebitda": {"company": 22.1, "peers_avg": 19.5},
        "pe_ratio": {"company": 28.3, "peers_avg": 25.1},
        "pb_ratio": {"company": 34.5, "peers_avg": 12.8},
        "peers": ["MSFT", "GOOGL", "AMZN", "META"],
    },
    "valuation_range": {"low": 165.0, "mid": 198.40, "high": 235.0},
}

# ---------------------------------------------------------------------------
# risk_metrics  (produced by Engine 3 — Owner: Siddharth)
# ---------------------------------------------------------------------------
MOCK_RISK_METRICS: dict = {
    "market_risk": {
        "beta": 1.18,
        "volatility_annual": 0.27,
        "sharpe_ratio": 1.05,
        "max_drawdown": -0.28,
        "var_95": -0.032,
    },
    "financial_health": {
        "altman_z_score": 4.2,
        "interest_coverage": 29.8,
        "debt_to_ebitda": 1.1,
        "current_ratio": 1.07,
    },
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
    "recommendation": "BUY",
    "target_price": 198.40,
    "sections": {
        "business_summary": (
            "Apple Inc. designs, manufactures, and markets smartphones, "
            "personal computers, tablets, wearables, and accessories worldwide. "
            "The company also operates a growing services segment."
        ),
        "financial_performance": (
            "Revenue CAGR of ~10.6% over 5 years with stable margins. "
            "Free cash flow generation remains strong at ~$106B TTM."
        ),
        "valuation_range": (
            "DCF intrinsic value of $198.40 implies ~11% upside from current "
            "price of $178.72. Bear case: $165, Bull case: $235."
        ),
        "key_risks": (
            "Smartphone market saturation, regulatory headwinds in EU and China, "
            "supply chain concentration in Asia."
        ),
        "investment_thesis": (
            "Strong ecosystem moat, expanding services revenue, disciplined "
            "capital allocation, and reasonable valuation support a BUY rating."
        ),
        "bear_case": (
            "iPhone growth stalls, services growth decelerates, macro headwinds "
            "compress multiples. Downside to $165."
        ),
    },
    "generated_at": "2026-04-13T00:00:00Z",
}
