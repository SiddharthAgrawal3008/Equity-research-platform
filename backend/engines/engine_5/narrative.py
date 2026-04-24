"""
narrative.py — Text generators for each investment memo section.

All section builders accept a ReportData object and return a plain string.
No I/O, no side-effects — pure text formatting.
"""

from __future__ import annotations
from backend.engines.engine_5.data_extractor import ReportData


# ── Formatting helpers ────────────────────────────────────────────────────────


def _fmt_cap(value: float | None) -> str:
    """Format a USD-millions value with T / B / M suffix.

    Handles the trillion scale that plain _fmt_m misses for large-cap companies.
    Examples:
        3_828_515  → "$3.83 trillion"
        3_500      → "$3.5 billion"
        250        → "$250 million"
    """
    if value is None:
        return "N/A"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f} trillion"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f} billion"
    return f"${value:.0f} million"


def _fmt_m(value: float | None) -> str:
    """Format millions with B / M suffix (no trillion — use _fmt_cap for market cap)."""
    if value is None:
        return "N/A"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}B"
    return f"${value:.0f}M"


def _fmt_pct(value: float | None, decimals: int = 1) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def _fmt_price(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"${value:.2f}"


def _fmt_x(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f}x"


def _fmt_f(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _cagr(start: float | None, end: float | None, years: int) -> float | None:
    if not start or not end or years <= 0 or start <= 0:
        return None
    try:
        return (end / start) ** (1 / years) - 1
    except (ZeroDivisionError, ValueError):
        return None


def _margin(ebitda: float | None, revenue: float | None) -> float | None:
    if ebitda is not None and revenue and revenue > 0:
        return ebitda / revenue
    return None


# ── Section builders ──────────────────────────────────────────────────────────


def business_summary(d: ReportData) -> str:
    """Section 1 — Company overview, size, TTM financials, revenue CAGR."""
    ebitda_margin = _margin(d.ttm_ebitda, d.ttm_revenue)

    rev_series = [v for v in d.revenue if v is not None]
    rev_cagr   = _cagr(rev_series[0], rev_series[-1], len(rev_series) - 1) if len(rev_series) >= 2 else None
    span       = f"{d.years[0]}–{d.years[-1]}" if len(d.years) >= 2 else "N/A"

    # Use _fmt_cap so Apple shows "$3.83 trillion" not "$3,828,516 million"
    lines = [
        f"BUSINESS SUMMARY — {d.company_name} ({d.ticker})",
        "",
        f"Sector: {d.sector}  |  Industry: {d.industry}",
    ]
    if d.market_cap is not None:
        lines.append(f"Market Cap: {_fmt_cap(d.market_cap)}")
    if d.current_price is not None:
        lines.append(f"Current Price: {_fmt_price(d.current_price)}")

    lines += [
        "",
        f"{d.company_name} is a {d.sector.lower()} company in the {d.industry} industry. "
        f"On a trailing-twelve-month basis the company generated revenue of "
        f"{_fmt_m(d.ttm_revenue)}, EBITDA of {_fmt_m(d.ttm_ebitda)} "
        f"({_fmt_pct(ebitda_margin)} margin), and net income of {_fmt_m(d.ttm_net_income)}.",
    ]
    if rev_cagr is not None:
        lines.append(
            f"Over {span}, revenue has compounded at {_fmt_pct(rev_cagr)} per annum."
        )
    return "\n".join(lines)


def financial_performance(d: ReportData) -> str:
    """Section 2 — Historical table, YoY growth, OCF/NI ratio, FCF trend."""
    n   = len(d.years)
    col = 12

    header = f"{'':8}" + "".join(f"{str(y):<{col}}" for y in d.years)
    rows = [
        f"{'Revenue':<8}"  + "".join(f"{_fmt_m(v):<{col}}" for v in d.revenue),
        f"{'EBITDA':<8}"   + "".join(f"{_fmt_m(v):<{col}}" for v in d.ebitda),
        f"{'Margin':<8}"   + "".join(f"{_fmt_pct(_margin(e, r)):<{col}}" for e, r in zip(d.ebitda, d.revenue)),
        f"{'Net Inc':<8}"  + "".join(f"{_fmt_m(v):<{col}}" for v in d.net_income),
        f"{'FCF':<8}"      + "".join(f"{_fmt_m(v):<{col}}" for v in d.fcf),
        f"{'OCF':<8}"      + "".join(f"{_fmt_m(v):<{col}}" for v in d.ocf),
    ]

    lines = ["FINANCIAL PERFORMANCE OVERVIEW", "", header] + rows + [""]

    # YoY revenue growth
    valid_rev = [(y, v) for y, v in zip(d.years, d.revenue) if v is not None]
    if len(valid_rev) >= 2:
        prev, last = valid_rev[-2][1], valid_rev[-1][1]
        if prev and prev > 0:
            yoy = (last - prev) / prev
            lines.append(f"FY{valid_rev[-1][0]} revenue growth: {_fmt_pct(yoy)} YoY.")

    # OCF / Net Income — improved phrasing (Instruction 2, item 2)
    valid_ocf_ni = [
        (o, ni) for o, ni in zip(d.ocf, d.net_income)
        if o is not None and ni and ni > 0
    ]
    if valid_ocf_ni:
        last_ocf, last_ni = valid_ocf_ni[-1]
        ratio = last_ocf / last_ni
        if 0.95 <= ratio <= 1.05:
            ocf_phrase = f"Cash conversion is strong, with operating cash flow of {_fmt_m(last_ocf)} roughly in line with reported net income."
        elif ratio > 1.05:
            excess_pct = (ratio - 1.0) * 100
            ocf_phrase = f"Cash conversion is excellent — operating cash flow of {_fmt_m(last_ocf)} exceeds net income by {excess_pct:.1f}%, indicating high earnings quality."
        else:
            shortfall_pct = (1.0 - ratio) * 100
            ocf_phrase = f"Cash conversion is moderate — operating cash flow of {_fmt_m(last_ocf)} falls {shortfall_pct:.1f}% short of net income, suggesting working capital or accruals require monitoring."
        lines.append(ocf_phrase)

    # FCF trend — dedicated paragraph (Instruction 2, item 3)
    valid_fcf = [(y, v) for y, v in zip(d.years, d.fcf) if v is not None]
    if valid_fcf:
        latest_fcf = valid_fcf[-1][1]
        fcf_yield: float | None = None
        if d.market_cap and d.market_cap > 0:
            # market_cap is in USD millions; latest_fcf also in USD millions
            fcf_yield = latest_fcf / d.market_cap

        if len(valid_fcf) >= 2:
            first_fcf = valid_fcf[0][1]
            last_fcf  = valid_fcf[-1][1]
            if first_fcf and first_fcf > 0:
                fcf_trend = "grown" if last_fcf > first_fcf * 1.05 else (
                    "declined" if last_fcf < first_fcf * 0.95 else "been broadly stable"
                )
                fcf_cagr = _cagr(first_fcf, last_fcf, len(valid_fcf) - 1)
            else:
                fcf_trend = "N/A"
                fcf_cagr  = None
        else:
            fcf_trend = None
            fcf_cagr  = None

        fcf_parts = [f"Free cash flow stood at {_fmt_m(latest_fcf)} in the most recent year"]
        if fcf_yield is not None:
            fcf_parts.append(f"representing a FCF yield of {_fmt_pct(fcf_yield)} on market cap")
        if fcf_trend and fcf_trend != "N/A" and fcf_cagr is not None:
            fcf_parts.append(
                f"FCF has {fcf_trend} over the analysis period at a {_fmt_pct(fcf_cagr)} CAGR"
            )
        lines.append(". ".join(fcf_parts) + ".")

    # EBITDA margin trend
    margins = [_margin(e, r) for e, r in zip(d.ebitda, d.revenue) if e is not None and r and r > 0]
    if len(margins) >= 2:
        delta = margins[-1] - margins[0]
        trend = "expanded" if delta > 0.01 else ("compressed" if delta < -0.01 else "been stable")
        lines.append(
            f"EBITDA margins have {trend} over the period "
            f"({_fmt_pct(margins[0])} → {_fmt_pct(margins[-1])})."
        )
    return "\n".join(lines)


def valuation_range(d: ReportData) -> str:
    """Section 3 — DCF value, range, assumptions, relative multiples."""
    lines = [
        "VALUATION RANGE",
        "",
        f"Current Price:     {_fmt_price(d.current_price)}",
        f"Fair Value Range:  {_fmt_price(d.val_range_low)} – {_fmt_price(d.val_range_high)}  (mid: {_fmt_price(d.val_range_mid)})",
        f"DCF Intrinsic Value: {_fmt_price(d.dcf_value)}",
        f"Implied Upside:    {_fmt_pct(d.val_upside_pct)}",
        f"Verdict: {d.val_verdict or 'N/A'}  |  Confidence: {d.val_confidence or 'N/A'}",
        "",
        "Key DCF Assumptions:",
    ]
    if d.wacc is not None:
        lines.append(f"  WACC:                {_fmt_pct(d.wacc)}")
    if d.terminal_growth_rate is not None:
        lines.append(f"  Terminal Growth Rate: {_fmt_pct(d.terminal_growth_rate)}")

    # Terminal value context — Instruction 2, item 4
    if d.terminal_value_pct is not None:
        tv_pct = d.terminal_value_pct
        if tv_pct > 0.85:
            tv_note = "  ⚠  Terminal Value / EV: {pct} — elevated; sensitivity to WACC and terminal growth is high.".format(pct=_fmt_pct(tv_pct))
        elif 0.60 <= tv_pct <= 0.85:
            tv_note = f"  Terminal Value / EV: {_fmt_pct(tv_pct)} — within the typical range for mature companies (60%–85%)."
        else:
            tv_note = f"  Terminal Value / EV: {_fmt_pct(tv_pct)}"
        lines.append(tv_note)

    lines += [
        "",
        "Relative Valuation (vs Peers):",
        f"  EV/EBITDA  Company: {_fmt_x(d.ev_ebitda_company)}   Peers: {_fmt_x(d.ev_ebitda_peers)}",
        f"  P/E        Company: {_fmt_x(d.pe_company)}   Peers: {_fmt_x(d.pe_peers)}",
        f"  P/B        Company: {_fmt_x(d.pb_company)}   Peers: {_fmt_x(d.pb_peers)}",
    ]

    if d.implied_growth_rate is not None or d.market_implied_stance:
        lines.append("")
        lines.append("Reverse DCF (Market Implied):")
        if d.implied_growth_rate is not None:
            lines.append(f"  Implied Growth Rate: {_fmt_pct(d.implied_growth_rate)}")
        if d.market_implied_stance:
            lines.append(f"  Market Stance:       {d.market_implied_stance}")

    return "\n".join(lines)


def key_risks(d: ReportData) -> str:
    """Section 4 — Market risk, financial health, NLP signals."""
    parts: list[str] = []

    # Market risk sub-block
    if "risk_metrics" in d.available_sections:
        mr_lines = ["MARKET RISK"]
        mr_lines.append(f"  Beta (vs {d.beta_benchmark}):       {_fmt_f(d.beta)}")
        mr_lines.append(f"  Annualized Volatility:    {_fmt_pct(d.volatility)}")
        mr_lines.append(f"  Sharpe Ratio:             {_fmt_f(d.sharpe)}")
        mr_lines.append(f"  Annualized Return:        {_fmt_pct(d.annualized_return)}")
        if d.max_drawdown is not None:
            period = f" ({d.max_drawdown_start} – {d.max_drawdown_end})" if d.max_drawdown_start and d.max_drawdown_end else ""
            mr_lines.append(f"  Max Drawdown:             {_fmt_pct(d.max_drawdown)}{period}")
        mr_lines.append(f"  95% Daily VaR:            {_fmt_pct(d.var_95_daily)}")
        parts.append("\n".join(mr_lines))

        # Financial health sub-block
        fh_lines = [
            "FINANCIAL HEALTH",
            f"  Altman Z-Score:       {_fmt_f(d.altman_z)} ({d.altman_zone or 'N/A'})",
            f"  Interest Coverage:    {_fmt_f(d.interest_coverage)}x",
            f"  Debt / EBITDA:        {_fmt_f(d.debt_to_ebitda)}x",
            f"  Debt / Equity:        {_fmt_f(d.debt_to_equity)}x",
            f"  Current Ratio:        {_fmt_f(d.current_ratio)}x",
            f"  Cash / Total Debt:    {_fmt_pct(d.cash_to_debt)}",
        ]
        if d.financial_red_flags:
            fh_lines.append("  Red Flags:            " + "; ".join(str(f) for f in d.financial_red_flags))

        # Leverage flag at 1.5x D/E — Instruction 2, item 6 (lowered from 2.0)
        if d.debt_to_equity is not None and d.debt_to_equity >= 1.5:
            fh_lines.append(
                f"  Note: D/E of {d.debt_to_equity:.2f}x is above the 1.5x caution threshold — "
                f"leverage warrants monitoring in a rising-rate environment."
            )

        # Premium multiple flag — Instruction 2, item 6
        premium_flags: list[str] = []
        if d.ev_ebitda_company is not None and d.ev_ebitda_peers and d.ev_ebitda_peers > 0:
            premium = (d.ev_ebitda_company - d.ev_ebitda_peers) / d.ev_ebitda_peers
            if premium > 0.20:
                premium_flags.append(
                    f"EV/EBITDA of {_fmt_x(d.ev_ebitda_company)} trades at a "
                    f"{_fmt_pct(premium)} premium to sector median ({_fmt_x(d.ev_ebitda_peers)})"
                )
        if d.pe_company is not None and d.pe_peers and d.pe_peers > 0:
            premium = (d.pe_company - d.pe_peers) / d.pe_peers
            if premium > 0.20:
                premium_flags.append(
                    f"P/E of {_fmt_x(d.pe_company)} trades at a "
                    f"{_fmt_pct(premium)} premium to sector median ({_fmt_x(d.pe_peers)})"
                )
        if premium_flags:
            fh_lines.append(
                "  Valuation Premium: " + "; ".join(premium_flags) + "."
            )

        parts.append("\n".join(fh_lines))

    # NLP sub-block
    if "nlp_insights" in d.available_sections:
        nlp_lines = ["NLP / MANAGEMENT SIGNALS"]
        if d.management_optimism is not None:
            nlp_lines.append(f"  Management Optimism:  {_fmt_f(d.management_optimism)}")
        if d.risk_word_frequency is not None:
            nlp_lines.append(f"  Risk Word Frequency:  {_fmt_pct(d.risk_word_frequency)}")
        if d.uncertainty_score is not None:
            nlp_lines.append(f"  Uncertainty Score:    {_fmt_f(d.uncertainty_score)}")
        if d.forward_guidance_tone:
            nlp_lines.append(f"  Fwd Guidance Tone:    {d.forward_guidance_tone}")
        if d.nlp_flag_severity:
            nlp_lines.append(f"  Red Flag Severity:    {d.nlp_flag_severity}")
        if d.nlp_flags:
            nlp_lines.append("  Red Flags:            " + "; ".join(str(f) for f in d.nlp_flags[:5]))
        if d.nlp_categories:
            nlp_lines.append("  Risk Categories:      " + ", ".join(str(c) for c in d.nlp_categories))
        if d.emerging_themes:
            nlp_lines.append("  Emerging Themes:      " + ", ".join(str(t) for t in d.emerging_themes[:3]))
        if d.fading_themes:
            nlp_lines.append("  Fading Themes:        " + ", ".join(str(t) for t in d.fading_themes[:3]))
        parts.append("\n".join(nlp_lines))

    return "\n\n".join(parts) if parts else "Key risk data unavailable."


def investment_thesis(d: ReportData) -> str:
    """Section 5 — Bull case anchored in valuation, FCF, balance sheet, NLP."""
    lines = ["INVESTMENT THESIS", ""]

    # Core valuation paragraph
    if "valuation" in d.available_sections and d.val_verdict:
        if d.val_verdict == "Undervalued":
            lines.append(
                f"{d.company_name} appears undervalued at {_fmt_price(d.current_price)}, "
                f"versus our blended fair value estimate of {_fmt_price(d.val_range_mid)}, "
                f"implying {_fmt_pct(d.val_upside_pct)} upside"
                + (f" (confidence: {d.val_confidence})" if d.val_confidence else "") + "."
            )
        elif d.val_verdict == "Overvalued":
            lines.append(
                f"{d.company_name} trades at {_fmt_price(d.current_price)}, a premium to our "
                f"blended fair value of {_fmt_price(d.val_range_mid)}, offering limited margin "
                f"of safety at current levels."
            )
        else:
            lines.append(
                f"{d.company_name} trades broadly in line with our blended fair value of "
                f"{_fmt_price(d.val_range_mid)} ({_fmt_price(d.current_price)} current price, "
                f"{_fmt_pct(d.val_upside_pct)} implied move)."
            )
    else:
        lines.append("Valuation data unavailable — qualitative factors inform the thesis only.")

    # FCF strength
    valid_fcf = [v for v in d.fcf if v is not None]
    if valid_fcf:
        lines.append(
            f"Free cash flow generation of {_fmt_m(valid_fcf[-1])} (most recent year) "
            f"provides financial flexibility and supports capital returns."
        )

    # Balance sheet — with extra fundamentals when upside is absent (Instruction 2, item 5)
    if "risk_metrics" in d.available_sections:
        if d.altman_zone:
            zone_desc = {
                "Safe":     "low near-term distress risk",
                "Grey":     "moderate credit risk — warrants monitoring",
                "Distress": "elevated distress risk",
            }.get(d.altman_zone, d.altman_zone.lower())
            ic_str = f", with interest coverage of {_fmt_f(d.interest_coverage)}x" if d.interest_coverage is not None else ""
            lines.append(
                f"Altman Z-Score places the company in the {d.altman_zone} zone{ic_str}, "
                f"indicating {zone_desc}."
            )

        # Interest coverage strength — add when DCF upside is absent (Instruction 2, item 5)
        has_upside = (d.val_upside_pct is not None and d.val_upside_pct > 0
                      and "valuation" in d.available_sections)
        if not has_upside and d.interest_coverage is not None and d.interest_coverage >= 5.0:
            lines.append(
                f"Interest coverage of {_fmt_f(d.interest_coverage)}x provides ample "
                f"debt-servicing capacity and reduces refinancing risk."
            )

        # Earnings quality — add as a strength if high (Instruction 2, item 5)
        if not has_upside and d.earnings_quality is not None and d.earnings_quality >= 0.90:
            lines.append(
                f"Earnings quality ratio of {_fmt_pct(d.earnings_quality)} indicates "
                f"that reported profits are substantially cash-backed."
            )

    # Management tone
    if "nlp_insights" in d.available_sections and d.forward_guidance_tone:
        positive = d.forward_guidance_tone.lower() in ("positive", "optimistic", "constructive")
        lines.append(
            f"Management's forward guidance tone is {d.forward_guidance_tone.lower()}, "
            + ("which lends incremental support to the thesis."
               if positive else "which warrants close monitoring.")
        )

    # Key themes
    if d.nlp_themes:
        lines.append(
            "Key operational themes from management communications: "
            + ", ".join(str(t) for t in d.nlp_themes[:3]) + "."
        )

    return "\n".join(lines)


def bear_case(d: ReportData) -> str:
    """Section 6 — Downside risks: valuation floor, market sensitivity, NLP flags."""
    bullets: list[str] = []

    # Valuation floor
    if "valuation" in d.available_sections and d.val_range_low is not None and d.current_price and d.current_price > 0:
        downside = (d.val_range_low - d.current_price) / d.current_price
        if downside < 0:
            bullets.append(
                f"Floor valuation of {_fmt_price(d.val_range_low)} implies "
                f"{_fmt_pct(downside)} downside from current price in a bear scenario."
            )

    # Market sensitivity
    if "risk_metrics" in d.available_sections:
        if d.beta is not None and d.beta > 1.2:
            bullets.append(
                f"Elevated beta ({d.beta:.2f} vs {d.beta_benchmark}) means a broad market "
                f"correction disproportionately impacts the stock."
            )
        if d.max_drawdown is not None:
            bullets.append(
                f"Historical peak-to-trough drawdown of {_fmt_pct(d.max_drawdown)} illustrates "
                f"material downside risk in adverse market conditions."
            )
        if d.var_95_daily is not None:
            bullets.append(
                f"95% Daily VaR of {_fmt_pct(d.var_95_daily)} — on a $1M position this implies "
                f"a 1-in-20 daily loss exceeding ${abs(d.var_95_daily) * 1_000_000:,.0f}."
            )
        # Leverage flag — lowered to 1.5x per Instruction 2, item 6
        if d.debt_to_ebitda is not None and d.debt_to_ebitda > 3.0:
            bullets.append(
                f"Leverage of {d.debt_to_ebitda:.1f}x Debt/EBITDA leaves limited buffer if "
                f"earnings deteriorate; refinancing risk rises in a higher-rate environment."
            )
        if d.debt_to_equity is not None and d.debt_to_equity >= 1.5:
            bullets.append(
                f"D/E of {d.debt_to_equity:.2f}x is above the caution threshold — any "
                f"deterioration in operating income would amplify the impact on equity holders."
            )

        # Premium multiple risk — Instruction 2, item 6
        if d.ev_ebitda_company is not None and d.ev_ebitda_peers and d.ev_ebitda_peers > 0:
            prem = (d.ev_ebitda_company - d.ev_ebitda_peers) / d.ev_ebitda_peers
            if prem > 0.20:
                bullets.append(
                    f"EV/EBITDA premium of {_fmt_pct(prem)} above sector median "
                    f"({_fmt_x(d.ev_ebitda_company)} vs {_fmt_x(d.ev_ebitda_peers)}) leaves "
                    f"the stock exposed to multiple contraction."
                )

    # NLP signals
    if "nlp_insights" in d.available_sections:
        if d.nlp_flags:
            bullets.append("Management language flags: " + "; ".join(str(f) for f in d.nlp_flags[:3]) + ".")
        if isinstance(d.uncertainty_score, float) and d.uncertainty_score > 0.5:
            bullets.append(
                f"Management uncertainty score ({_fmt_f(d.uncertainty_score)}) is elevated, "
                f"suggesting reduced near-term earnings visibility."
            )

    if not bullets:
        bullets.append(
            "Deterioration in operating performance, competitive displacement, adverse macro "
            "conditions, or margin compression could erode intrinsic value."
        )

    lines = ["BEAR CASE", ""]
    lines += [f"• {b}" for b in bullets]
    return "\n".join(lines)


def summary_line(d: ReportData) -> str:
    """One-line memo header for the report summary field."""
    parts = [d.company_name]
    if d.current_price:
        parts.append(f"@ {_fmt_price(d.current_price)}")
    if "valuation" in d.available_sections and d.val_verdict:
        parts.append(f"| {d.val_verdict}")
    if d.val_range_mid:
        parts.append(f"| DCF {_fmt_price(d.dcf_value)}")
    if d.val_upside_pct is not None:
        parts.append(f"({_fmt_pct(d.val_upside_pct)} upside)")
    if d.val_confidence:
        parts.append(f"| Confidence: {d.val_confidence}")
    if d.ttm_revenue:
        parts.append(f"| TTM Rev: {_fmt_m(d.ttm_revenue)}")
    return " ".join(parts)
