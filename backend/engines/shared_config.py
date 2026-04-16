"""
Shared configuration for the Equity Research Platform valuation engines.

All constants are used by Engine 2 (Valuation) and Engine 3 (Risk).
Sector keys are UPPERCASE strings matching Engine 1's `meta.sector` output.
"""

# ── Core Valuation Parameters ──────────────────────────────────────────

RISK_FREE_RATE = 0.043            # 10-year US Treasury yield proxy
EQUITY_RISK_PREMIUM = 0.055       # long-run ERP estimate
TERMINAL_GROWTH_RATE = 0.025      # perpetuity growth rate
PROJECTION_YEARS = 5
US_STATUTORY_TAX_RATE = 0.21
MONTE_CARLO_ITERATIONS = 0        # disabled in v1

# ── Sector Average Betas ───────────────────────────────────────────────

SECTOR_AVG_BETAS = {
    "TECHNOLOGY": 1.18,
    "HEALTHCARE": 0.95,
    "FINANCIAL_SERVICES": 1.10,
    "CONSUMER_CYCLICAL": 1.15,
    "CONSUMER_DEFENSIVE": 0.70,
    "ENERGY": 1.30,
    "INDUSTRIALS": 1.05,
    "BASIC_MATERIALS": 1.10,
    "REAL_ESTATE": 0.80,
    "UTILITIES": 0.50,
    "COMMUNICATION_SERVICES": 0.95,
}

DEFAULT_BETA = 1.0

# ── Sector Average Growth Rates ────────────────────────────────────────

SECTOR_AVG_GROWTH_RATES = {
    "TECHNOLOGY": 0.08,
    "HEALTHCARE": 0.07,
    "FINANCIAL_SERVICES": 0.05,
    "CONSUMER_CYCLICAL": 0.06,
    "CONSUMER_DEFENSIVE": 0.04,
    "ENERGY": 0.03,
    "INDUSTRIALS": 0.05,
    "BASIC_MATERIALS": 0.04,
    "REAL_ESTATE": 0.04,
    "UTILITIES": 0.03,
    "COMMUNICATION_SERVICES": 0.05,
}

DEFAULT_SECTOR_GROWTH = 0.04

# ── Sector Average Multiples ──────────────────────────────────────────

SECTOR_AVG_MULTIPLES = {
    "TECHNOLOGY":             {"ev_ebitda": 20.0, "pe": 28.0, "pb": 8.0},
    "HEALTHCARE":             {"ev_ebitda": 16.0, "pe": 22.0, "pb": 4.5},
    "FINANCIAL_SERVICES":     {"ev_ebitda": 12.0, "pe": 14.0, "pb": 1.5},
    "CONSUMER_CYCLICAL":      {"ev_ebitda": 14.0, "pe": 20.0, "pb": 4.0},
    "CONSUMER_DEFENSIVE":     {"ev_ebitda": 14.0, "pe": 22.0, "pb": 5.0},
    "ENERGY":                 {"ev_ebitda": 7.0,  "pe": 12.0, "pb": 1.8},
    "INDUSTRIALS":            {"ev_ebitda": 13.0, "pe": 20.0, "pb": 3.5},
    "BASIC_MATERIALS":        {"ev_ebitda": 10.0, "pe": 15.0, "pb": 2.0},
    "REAL_ESTATE":            {"ev_ebitda": 18.0, "pe": 35.0, "pb": 2.0},
    "UTILITIES":              {"ev_ebitda": 12.0, "pe": 18.0, "pb": 1.8},
    "COMMUNICATION_SERVICES": {"ev_ebitda": 12.0, "pe": 18.0, "pb": 3.0},
}

# ── Guard Rails ────────────────────────────────────────────────────────

MAX_STARTING_GROWTH = 0.50
MIN_STARTING_GROWTH = -0.30
MAX_TARGET_GROWTH = 0.10         # sector target capped here
MAX_COST_OF_DEBT = 0.20

WACC_FLOOR = 0.04
WACC_CEILING = 0.25

# ── Terminal Value Thresholds ──────────────────────────────────────────

TV_WARNING_THRESHOLD = 0.85      # TV as % of EV
TV_CRITICAL_THRESHOLD = 0.90

# ── DCF Sanity Checks ─────────────────────────────────────────────────

DCF_EXTREME_HIGH = 10.0          # implied > 10x current price
DCF_EXTREME_LOW = 0.1            # implied < 0.1x current price

# ── Valuation Stance Thresholds ────────────────────────────────────────

UNDERVALUED_THRESHOLD = 0.15     # upside > 15%
OVERVALUED_THRESHOLD = -0.10     # upside < -10%
MIXED_SIGNAL_DIVERGENCE = 0.30   # DCF vs relative disagree > 30%

# ── Confidence Scoring ─────────────────────────────────────────────────

CONFIDENCE_DEDUCTIONS = {
    "sector_avg_beta":       0.10,   # using sector avg, not calculated beta
    "less_than_5yr_history": 0.15,
    "less_than_3yr_history": 0.25,
    "tv_above_85pct":        0.10,
    "tv_above_90pct":        0.20,
    "dcf_extreme_result":    0.25,   # implied > 5x or < 0.2x current
    "dcf_relative_diverge":  0.15,   # DCF and relative diverge > 50%
    "negative_ebitda":       0.30,
    "per_data_warning":      0.05,
    "anomalous_tax_rate":    0.10,
}

CONFIDENCE_THRESHOLDS = {
    "HIGH": 0.75,
    "MEDIUM": 0.50,
    "LOW": 0.25,
}

# ── Sensitivity Grid ──────────────────────────────────────────────────

SENSITIVITY_WACC_STEP = 0.01
SENSITIVITY_WACC_POINTS = 5
SENSITIVITY_TGR_STEP = 0.0075
SENSITIVITY_TGR_POINTS = 5
