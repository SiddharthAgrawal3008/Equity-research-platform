"""
Shared Configuration — Engines 2 & 3
=====================================

Version: 1.0

Centralised constants for the Automated Equity Research Platform.
Engine 2 (Valuation) and Engine 3 (Risk & Financial Health) import all
market assumptions, model parameters, sector benchmarks, and guard-rail
thresholds from this single file.  No engine should hard-code these
values — they all read from here.

Update cadence
--------------
- Market parameters (Section 1):  quarterly, or when the Fed / Damodaran
  publishes new estimates.
- DCF / sensitivity / Monte Carlo parameters (Sections 2-4):  per model
  revision — only change when the methodology changes.
- Beta / risk parameters (Section 5):  quarterly, aligned with market
  parameter updates.
- Engine 3 thresholds (Section 6):  per model revision.
- Guard rails (Section 7):  per model revision.
- Sector data (Sections 8-10):  semi-annually, sourced from Damodaran's
  updated datasets.
- Valuation stance / confidence scoring (Sections 11-12):  per model
  revision.
"""

# ── 1.  MARKET PARAMETERS ──────────────────────────────────────────────

RISK_FREE_RATE: float = 0.043            # 10-year US Treasury yield (4.3 %)
EQUITY_RISK_PREMIUM: float = 0.055       # Damodaran's implied ERP (5.5 %)
TERMINAL_GROWTH_RATE: float = 0.025      # Long-run GDP growth (2.5 %); must be < WACC
US_STATUTORY_TAX_RATE: float = 0.21      # Federal corporate tax rate (fallback when
                                         # effective tax rate is unavailable or anomalous)

# ── 2.  DCF MODEL PARAMETERS ───────────────────────────────────────────

PROJECTION_YEARS: int = 5                # Explicit forecast horizon
DCF_METHOD: str = "fcff"                 # Free Cash Flow to Firm (primary method)
TERMINAL_METHOD: str = "gordon"          # Gordon Growth Model primary;
                                         # exit_multiple as cross-check

# ── 3.  SENSITIVITY ANALYSIS PARAMETERS ────────────────────────────────

SENSITIVITY_WACC_STEP: float = 0.01      # +/- step size around base WACC
SENSITIVITY_WACC_POINTS: int = 2         # Steps each side → 5-point grid:
                                         # WACC-0.02, WACC-0.01, WACC, WACC+0.01, WACC+0.02
SENSITIVITY_TGR_STEP: float = 0.0075     # +/- step size around terminal growth rate
SENSITIVITY_TGR_POINTS: int = 2          # Steps each side → 5-point grid

# ── 4.  MONTE CARLO PARAMETERS ─────────────────────────────────────────

MONTE_CARLO_ITERATIONS: int = 0          # 0 = skip Monte Carlo in v1; set to 5 000 for v2

# ── 5.  BETA / MARKET RISK PARAMETERS (shared with Engine 3) ──────────

BENCHMARK_TICKER: str = "^GSPC"          # S&P 500 for beta regression
BETA_LOOKBACK_YEARS: int = 2             # Weekly returns over this period
BETA_FREQUENCY: str = "W"               # Weekly frequency
BETA_USE_ADJUSTED: bool = True           # Bloomberg adjustment: 0.67 × raw + 0.33 × 1.0
MIN_PRICE_HISTORY_YEARS: int = 1         # Minimum years for calculated beta;
                                         # else use sector fallback

# ── 6.  ENGINE 3 — FINANCIAL HEALTH THRESHOLDS ────────────────────────

SHARPE_LOOKBACK_YEARS: int = 2
VAR_CONFIDENCE_LEVEL: float = 0.95
DRAWDOWN_LOOKBACK_YEARS: int = 5
ZSCORE_SAFE: float = 2.99               # Altman Z-score: above = safe zone
ZSCORE_DISTRESS: float = 1.81           # Below = distress zone
ZSCORE_EXCLUDED_SECTORS: set[str] = {"Financials", "Real Estate"}
EARNINGS_QUALITY_HIGH_THRESHOLD: float = 5.0    # OCF/NI above this is anomalous

# ── 7.  GUARD RAILS (Engine 2 sanity checks) ──────────────────────────

MAX_STARTING_GROWTH: float = 0.50       # Cap hyper-growth at 50 %
MIN_STARTING_GROWTH: float = -0.30      # Floor deep decline at -30 %
MAX_TARGET_GROWTH: float = 0.10         # Target growth rate ceiling
MAX_COST_OF_DEBT: float = 0.20          # Cap Rd at 20 %
WACC_FLOOR: float = 0.04
WACC_CEILING: float = 0.25
TV_WARNING_THRESHOLD: float = 0.85      # Flag if terminal value > 85 % of EV
TV_CRITICAL_THRESHOLD: float = 0.90     # Strong warning if > 90 %
DCF_EXTREME_HIGH: float = 10.0          # Flag if implied price > 10× current
DCF_EXTREME_LOW: float = 0.1            # Flag if implied price < 0.1× current

# ── RELATIVE VALUATION GUARD RAILS ─────────────────────────────────────
RELATIVE_DIVERGENCE_MAX: float = 10.0   # Max ratio between highest and lowest implied prices
RELATIVE_EXTREME_UPSIDE: float = 5.0    # Flag if relative-only upside exceeds 500%

# ── 7b. REVERSE DCF PARAMETERS ────────────────────────────────────────

REVERSE_DCF_TOLERANCE: float = 1e-6      # Bisection convergence tolerance (EV diff)
REVERSE_DCF_MAX_ITER: int = 100          # Maximum bisection iterations
REVERSE_DCF_GROWTH_LO: float = -0.30     # Search range lower bound (−30 %)
REVERSE_DCF_GROWTH_HI: float = 0.50      # Search range upper bound (+50 %)
REVERSE_DCF_OPTIMISM_BAND: float = 0.02  # ±2 pp = "In Line" with forward DCF

# ── 8.  SECTOR AVERAGE BETAS ──────────────────────────────────────────
# Source: Damodaran's adjusted sector betas.
# Keys are UPPERCASE, matching Engine 1's meta.sector.

SECTOR_AVG_BETAS: dict[str, float] = {
    "TECHNOLOGY":             1.18,
    "HEALTHCARE":             0.95,
    "FINANCIALS":             1.05,
    "CONSUMER CYCLICAL":      1.15,
    "CONSUMER DEFENSIVE":     0.65,
    "INDUSTRIALS":            1.05,
    "ENERGY":                 1.10,
    "MATERIALS":              1.00,
    "REAL ESTATE":            0.75,
    "UTILITIES":              0.55,
    "COMMUNICATION SERVICES": 1.00,
}

DEFAULT_BETA: float = 1.0

# ── 9.  SECTOR AVERAGE GROWTH RATES ───────────────────────────────────
# Mean-reversion targets for revenue projection.

SECTOR_AVG_GROWTH_RATES: dict[str, float] = {
    "TECHNOLOGY":             0.08,
    "HEALTHCARE":             0.07,
    "FINANCIALS":             0.05,
    "CONSUMER CYCLICAL":      0.06,
    "CONSUMER DEFENSIVE":     0.04,
    "INDUSTRIALS":            0.05,
    "ENERGY":                 0.03,
    "MATERIALS":              0.04,
    "REAL ESTATE":            0.04,
    "UTILITIES":              0.03,
    "COMMUNICATION SERVICES": 0.06,
}

DEFAULT_SECTOR_GROWTH: float = 0.04

# ── 10. SECTOR AVERAGE MULTIPLES ──────────────────────────────────────
# For relative valuation and exit-multiple terminal value.
# Each sector: ev_ebitda (median EV/EBITDA), pe (median P/E), pb (median P/B).

SECTOR_AVG_MULTIPLES: dict[str, dict[str, float]] = {
    "TECHNOLOGY":             {"ev_ebitda": 20.0, "pe": 28.0, "pb": 8.0},
    "HEALTHCARE":             {"ev_ebitda": 15.0, "pe": 22.0, "pb": 4.5},
    "FINANCIALS":             {"ev_ebitda": 10.0, "pe": 13.0, "pb": 1.5},
    "CONSUMER CYCLICAL":      {"ev_ebitda": 14.0, "pe": 20.0, "pb": 4.0},
    "CONSUMER DEFENSIVE":     {"ev_ebitda": 13.0, "pe": 20.0, "pb": 4.0},
    "INDUSTRIALS":            {"ev_ebitda": 13.0, "pe": 19.0, "pb": 3.5},
    "ENERGY":                 {"ev_ebitda":  7.0, "pe": 12.0, "pb": 1.8},
    "MATERIALS":              {"ev_ebitda":  9.0, "pe": 15.0, "pb": 2.5},
    "REAL ESTATE":            {"ev_ebitda": 18.0, "pe": 35.0, "pb": 2.0},
    "UTILITIES":              {"ev_ebitda": 12.0, "pe": 17.0, "pb": 2.0},
    "COMMUNICATION SERVICES": {"ev_ebitda": 12.0, "pe": 18.0, "pb": 3.0},
}

# ── 11. VALUATION STANCE THRESHOLDS ───────────────────────────────────

UNDERVALUED_THRESHOLD: float = 0.15     # > 15 % upside = undervalued
OVERVALUED_THRESHOLD: float = -0.10     # > 10 % downside = overvalued
MIXED_SIGNAL_DIVERGENCE: float = 0.30   # DCF vs relative differ by > 30 % = mixed signals

# ── 12. CONFIDENCE SCORING ────────────────────────────────────────────
# Rule-based deductions (Section 15b of spec).

CONFIDENCE_DEDUCTIONS: dict[str, float] = {
    "sector_avg_beta":      -0.10,
    "limited_history_5yr":  -0.15,
    "limited_history_3yr":  -0.25,
    "tv_above_85pct":       -0.10,
    "tv_above_90pct":       -0.20,
    "dcf_extreme_result":   -0.25,
    "dcf_relative_diverge": -0.15,
    "negative_ebitda":      -0.30,
    "data_quality_warning": -0.05,       # per warning
    "non_standard_company": -0.05,
    "anomalous_tax_rate":   -0.10,
    "monte_carlo_bonus":    +0.05,
}

CONFIDENCE_THRESHOLDS: dict[str, float] = {
    "HIGH":   0.75,
    "MEDIUM": 0.50,
    "LOW":    0.25,
    # Below 0.25 = "UNRELIABLE"
}

# ── 13. ENGINE 4 — NLP INTELLIGENCE PARAMETERS ────────────────────────

FMP_API_KEY: str = ""                    # Paid key injected here when available;
                                         # empty string → E4 falls back to EDGAR only
RISK_WORD_THRESHOLD: float = 0.07        # E4 outputs raw frequency only;
                                         # E5 applies this threshold to flag high risk
NLP_LOOKBACK_QUARTERS: int = 4           # Transcripts analysed for trend detection
STALENESS_DAYS: int = 90                 # Most recent document older than this → staleness_flag

# ── 14. ENGINE 1 — ALPHA VANTAGE API KEY POOL ─────────────────────────
# Rotation pool used by financial_data.py. If ALPHA_VANTAGE_API_KEY is set
# in .env, that key is tried first; these serve as fallback/rotation keys.

AV_API_KEYS = [
    "7S6SYRX0FO4Y629W",
    "4A92Z90SXGQ1VKWY",
    "1UULEYN0S6V9A0ZP",
    "PU3U6SOA0QCW2B0E",
    "HY18XN62PCFE1BCL",
]
