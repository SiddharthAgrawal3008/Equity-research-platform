"""
data_extractor.py — Flatten and normalize bus data for Engine 5.

Reads the four upstream bus keys and returns a single ReportData
dataclass so the narrative and PDF builders never touch raw bus dicts.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ReportData:
    # ── Identity ──────────────────────────────────────────────────────
    ticker:        str        = "N/A"
    company_name:  str        = "N/A"
    sector:        str        = "N/A"
    industry:      str        = "N/A"
    market_cap:    float|None = None
    current_price: float|None = None

    # ── Time-series (aligned with years list) ─────────────────────────
    years:      list = field(default_factory=list)
    revenue:    list = field(default_factory=list)
    ebitda:     list = field(default_factory=list)
    net_income: list = field(default_factory=list)
    fcf:        list = field(default_factory=list)
    ocf:        list = field(default_factory=list)

    # ── TTM ───────────────────────────────────────────────────────────
    ttm_revenue:    float|None = None
    ttm_ebitda:     float|None = None
    ttm_net_income: float|None = None

    # ── Valuation summary ─────────────────────────────────────────────
    dcf_value:      float|None = None
    val_range_low:  float|None = None
    val_range_mid:  float|None = None
    val_range_high: float|None = None
    val_verdict:    str|None   = None
    val_confidence: str|None   = None
    val_upside_pct: float|None = None

    # ── DCF assumptions ───────────────────────────────────────────────
    wacc:                float|None = None
    terminal_growth_rate: float|None = None
    terminal_value_pct:   float|None = None

    # ── Relative valuation ────────────────────────────────────────────
    ev_ebitda_company: float|None = None
    ev_ebitda_peers:   float|None = None
    pe_company:        float|None = None
    pe_peers:          float|None = None
    pb_company:        float|None = None
    pb_peers:          float|None = None

    # ── Reverse DCF ───────────────────────────────────────────────────
    implied_growth_rate:   float|None = None
    market_implied_stance: str|None   = None

    # ── Market risk ───────────────────────────────────────────────────
    beta:              float|None = None
    beta_benchmark:    str        = "S&P 500"
    volatility:        float|None = None
    sharpe:            float|None = None
    max_drawdown:      float|None = None
    max_drawdown_start: str|None  = None
    max_drawdown_end:   str|None  = None
    var_95_daily:      float|None = None
    annualized_return: float|None = None

    # ── Financial health ──────────────────────────────────────────────
    altman_z:           float|None = None
    altman_zone:        str|None   = None
    interest_coverage:  float|None = None
    debt_to_ebitda:     float|None = None
    debt_to_equity:     float|None = None
    current_ratio:      float|None = None
    cash_to_debt:       float|None = None
    earnings_quality:   float|None = None
    financial_red_flags: list      = field(default_factory=list)

    # ── NLP ───────────────────────────────────────────────────────────
    management_optimism:   float|None = None
    risk_word_frequency:   float|None = None
    uncertainty_score:     float|None = None
    forward_guidance_tone: str|None   = None
    nlp_flags:             list       = field(default_factory=list)
    nlp_flag_severity:     str|None   = None
    nlp_categories:        list       = field(default_factory=list)
    emerging_themes:       list       = field(default_factory=list)
    fading_themes:         list       = field(default_factory=list)
    nlp_themes:            list       = field(default_factory=list)

    # ── Pipeline state ────────────────────────────────────────────────
    available_sections: list = field(default_factory=list)


def extract(context: dict, available_sections: list[str]) -> ReportData:
    """Build a ReportData from the shared pipeline context."""
    fd   = context.get("financial_data") or {}
    val  = context.get("valuation")      or {}
    risk = context.get("risk_metrics")   or {}
    nlp  = context.get("nlp_insights")   or {}

    meta        = fd.get("meta")        or {}
    ttm         = fd.get("ttm")         or {}
    financials  = fd.get("financials")  or {}
    market_data = fd.get("market_data") or {}
    years       = list(fd.get("years")  or [])

    val_sum     = val.get("summary")     or {}
    dcf         = val.get("dcf")         or {}
    relative    = val.get("relative")    or {}
    rev_dcf     = val.get("reverse_dcf") or {}

    beta_d  = risk.get("beta")             or {}
    mkt     = risk.get("market_risk")      or {}
    fh      = risk.get("financial_health") or {}
    risk_rf = risk.get("red_flags")        or []

    nlp_sent   = nlp.get("sentiment")  or {}
    nlp_rf     = nlp.get("red_flags")  or {}
    nlp_themes = nlp.get("key_themes") or {}

    n = len(years)
    def _pad(lst: list) -> list:
        lst = list(lst or [])
        return lst + [None] * max(0, n - len(lst))

    return ReportData(
        ticker        = meta.get("ticker") or "N/A",
        company_name  = meta.get("company_name") or meta.get("ticker") or "N/A",
        sector        = meta.get("sector")   or "N/A",
        industry      = meta.get("industry") or "N/A",
        market_cap    = meta.get("market_cap"),
        current_price = (market_data.get("current_price")
                         or val_sum.get("current_price")),

        years      = years,
        revenue    = _pad(financials.get("revenue")           or []),
        ebitda     = _pad(financials.get("ebitda")            or []),
        net_income = _pad(financials.get("net_income")        or []),
        fcf        = _pad(financials.get("free_cash_flow")    or []),
        ocf        = _pad(financials.get("operating_cash_flow") or []),

        ttm_revenue    = ttm.get("revenue"),
        ttm_ebitda     = ttm.get("ebitda"),
        ttm_net_income = ttm.get("net_income"),

        dcf_value      = val_sum.get("dcf_value"),
        val_range_low  = val_sum.get("valuation_range_low"),
        val_range_mid  = val_sum.get("valuation_range_mid"),
        val_range_high = val_sum.get("valuation_range_high"),
        val_verdict    = val_sum.get("verdict"),
        val_confidence = val_sum.get("confidence"),
        val_upside_pct = val_sum.get("upside_pct"),

        wacc                 = dcf.get("wacc"),
        terminal_growth_rate = dcf.get("terminal_growth_rate"),
        terminal_value_pct   = dcf.get("terminal_value_pct"),

        ev_ebitda_company = relative.get("ev_ebitda_company"),
        ev_ebitda_peers   = relative.get("ev_ebitda_peers_median"),
        pe_company        = relative.get("pe_company"),
        pe_peers          = relative.get("pe_peers_median"),
        pb_company        = relative.get("pb_company"),
        pb_peers          = relative.get("pb_peers_median"),

        implied_growth_rate   = rev_dcf.get("implied_growth_rate"),
        market_implied_stance = rev_dcf.get("market_implied_stance"),

        beta               = beta_d.get("value"),
        beta_benchmark     = beta_d.get("benchmark") or "S&P 500",
        volatility         = mkt.get("historical_volatility"),
        sharpe             = mkt.get("sharpe_ratio"),
        max_drawdown       = mkt.get("max_drawdown"),
        max_drawdown_start = mkt.get("max_drawdown_start"),
        max_drawdown_end   = mkt.get("max_drawdown_end"),
        var_95_daily       = mkt.get("var_95_daily"),
        annualized_return  = mkt.get("annualized_return"),

        altman_z            = fh.get("altman_z_score"),
        altman_zone         = fh.get("altman_z_zone"),
        interest_coverage   = fh.get("interest_coverage"),
        debt_to_ebitda      = fh.get("debt_to_ebitda"),
        debt_to_equity      = fh.get("debt_to_equity"),
        current_ratio       = fh.get("current_ratio"),
        cash_to_debt        = fh.get("cash_to_debt"),
        earnings_quality    = fh.get("earnings_quality"),
        financial_red_flags = list(risk_rf) if isinstance(risk_rf, list) else [],

        management_optimism   = nlp_sent.get("management_optimism"),
        risk_word_frequency   = nlp_sent.get("risk_word_frequency"),
        uncertainty_score     = nlp_sent.get("uncertainty_score"),
        forward_guidance_tone = nlp_sent.get("forward_guidance_tone"),
        nlp_flags             = list(nlp_rf.get("flags")              or []),
        nlp_flag_severity     = nlp_rf.get("severity"),
        nlp_categories        = list(nlp_rf.get("categories_detected") or []),
        emerging_themes       = list(nlp_themes.get("emerging_themes") or []),
        fading_themes         = list(nlp_themes.get("fading_themes")   or []),
        nlp_themes            = list(nlp_themes.get("themes")          or []),

        available_sections = list(available_sections),
    )
