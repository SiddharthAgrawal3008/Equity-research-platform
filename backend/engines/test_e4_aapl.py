"""
Engine 4 — Live test with real AAPL financial_data.
Run: python -m backend.engines.test_e4_aapl
"""

import json
import sys
import time

# ── Build financial_data from the AAPL snapshot ──────────────────────

AAPL_FINANCIAL_DATA = {
    "meta": {
        "ticker":           "AAPL",
        "name":             "Apple Inc",
        "sector":           "TECHNOLOGY",
        "industry":         "CONSUMER ELECTRONICS",
        "exchange":         "NASDAQ",
        "currency":         "USD",
        "price":            263.40,
        "market_cap":       3_915_968.2,   # millions
        "enterprise_value": 3_992_411.2,   # millions
        "shares_outstanding": 14_681.1,    # millions
    },
    "years": [2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,
              2016,2017,2018,2019,2020,2021,2022,2023,2024,2025],
    "revenue":       [19315,24006,32479,42905,65225,108249,156508,170910,
                      182795,233715,215639,229234,265595,260174,274515,
                      365817,394328,383285,391035,416161],
    "gross_profit":  [5598,8154,11145,17222,25684,43818,68662,64304,
                      70537,93626,84263,88186,101839,98392,104956,
                      152836,170782,169148,180683,195201],
    "ebit":          [2453,4407,6895,11740,18385,34205,55763,50291,
                      53867,73248,62828,66412,76143,69313,69964,
                      111852,119437,114301,123216,132729],
    "ebitda":        [2678,4724,7304,12474,19412,36019,59040,57048,
                      61813,84505,73333,76569,87046,81860,81020,
                      123136,130541,125820,134661,144427],
    "net_income":    [1989,3495,4834,8235,14013,25922,41733,37037,
                      39510,53394,45687,48351,59531,55256,57411,
                      94680,99803,96995,93736,112010],
    "interest_expense": [365,599,620,326,155,415,522,136,384,733,
                         1456,2323,3240,3576,2873,2645,2931,3933,3933,3933],
    "total_assets":  [17205,25347,39572,53851,75183,116371,176064,207000,
                      231839,290479,321686,375319,365725,338516,323888,
                      351002,352755,352583,364980,359241],
    "total_debt":    [0,0,0,0,0,0,0,16960,35295,64462,87032,115680,
                      114483,108047,112436,124719,120881,111947,119059,112377],
    "cash":          [6392,9352,11875,5263,11261,9815,10746,14259,13844,
                      21120,20484,20289,25913,48844,38016,34940,23646,
                      29965,29943,35934],
    "retained_earnings": [5607,9101,13845,19538,37169,62841,101289,104256,
                           87152,92284,96364,98330,70400,45898,14966,5562,
                           -3068,-214,-19154,-14264],
    "operating_cash_flow": [2220,5470,9596,10159,18595,37529,50856,53666,
                             59713,81266,65824,63598,77434,69391,80674,
                             104038,122151,110543,118254,111482],
    "capex":         [-657,-735,-1091,-1144,-2005,-4260,-8295,-8165,
                      -9571,-11247,-12734,-12451,-13313,-10495,-7309,
                      -11085,-10708,-10959,-9447,-12715],

    # New fields (last 3 years: 2023, 2024, 2025)
    "cost_of_revenue":    [214137, 210352, 220960],
    "depreciation_amortisation": [11519, 11445, 11698],
    "pretax_income":      [113736, 123485, 132729],
    "tax_expense":        [16741,  29749,  20719],
    "rd_expense":         [29915,  31370,  34550],
    "sga_expense":        [24932,  26097,   8077],
    "long_term_debt":     [95281,  85750,  78328],
    "total_equity":       [62146,  56950,  73733],
    "accounts_payable":   [62611,  68960,  69860],
    "net_debt":           [81982,  89116,  76443],
    "net_working_capital":[-1742, -23405, -17674],
    "free_cash_flow":     [99584, 108807,  98767],
    "dividends_paid":     [-15025, -15234, -15421],
    "share_buybacks":     [None, None, None],
    "net_debt_issuance":  [None, None, None],

    # Quality / validity
    "is_valid":           True,
    "years_of_history":   20,
    "is_bank":            False,
    "is_reit":            False,
    "warnings": [
        "total_debt set to 0.0 for 7 year(s) where API returned null (pre-debt era).",
        "share_buybacks unavailable on Alpha Vantage free tier.",
        "net_debt_issuance unavailable on Alpha Vantage free tier.",
        "depreciation_amortisation computed as ebitda - ebit for 20 year(s).",
        "interest_expense[2024] imputed from prior year.",
        "interest_expense[2025] imputed from prior year.",
    ],
    "errors": [],

    # Derived metrics (computed by E1)
    "gross_margin":    0.4691,
    "ebit_margin":     0.3189,
    "ebitda_margin":   0.3470,
    "net_margin":      0.2692,
    "fcf_margin":      0.2373,

    "revenue_cagr":    0.1754,
    "revenue_yoy":     [-0.0280, 0.0202, 0.0643],
    "fcf_yoy":         [-0.1064, 0.0926, -0.0923],

    "roe":             1.5191,
    "roa":             0.3118,
    "roic":            0.7459,

    "ar_days":         63.99,
    "ap_days":         115.40,
    "inventory_days":  9.45,
    "interest_coverage": 33.75,
    "debt_to_ebitda":  0.78,

    "gross_margin_trend": "improving",
    "ebit_margin_trend":  "improving",
    "revenue_trend":      "improving",
    "fcf_margin_trend":   "deteriorating",
}


# ── Run the engine ────────────────────────────────────────────────────

def _bar(value, width: int = 20) -> str:
    if value is None:
        return "·" * width
    filled = round(max(0.0, min(1.0, float(value))) * width)
    return "█" * filled + "░" * (width - filled)


def _pct(v: float) -> str:
    return f"{v * 100:+.1f}%" if isinstance(v, float) else str(v)


def display_results(result: dict) -> None:
    sentiment  = result.get("sentiment", {})
    red_flags  = result.get("red_flags", {})
    key_themes = result.get("key_themes", {})
    coverage   = result.get("source_coverage", {})
    meta       = result.get("meta", {})

    print("\n" + "═" * 65)
    print("  ENGINE 4 — NLP INTELLIGENCE OUTPUT  │  AAPL  │  Apple Inc")
    print("═" * 65)

    # ── Sentiment ─────────────────────────────────────────────────────
    print("\n┌─ SENTIMENT ─────────────────────────────────────────────────┐")
    for label, key in [
        ("Overall",         "overall_score"),
        ("Mgmt Optimism",   "management_optimism"),
        ("Risk Freq",       "risk_word_frequency"),
        ("Uncertainty",     "uncertainty_score"),
        ("Q&A delta",       "qna_vs_prepared_delta"),
    ]:
        val = sentiment.get(key)
        # delta can be negative — normalise to 0-1 for bar display
        bar_val = ((val + 1) / 2) if val is not None else None
        val_str = f"{val:+.4f}" if val is not None else "  N/A  "
        print(f"│  {label:<18} {_bar(bar_val)}  {val_str}")
    print("│")

    trend = sentiment.get("sentiment_trend")
    guidance = sentiment.get("forward_guidance_tone", "N/A")
    print(f"│  Trend direction:         {trend or 'N/A'}")
    print(f"│  Guidance tone:           {guidance}")
    print("└─────────────────────────────────────────────────────────────┘")

    # ── Red Flags ─────────────────────────────────────────────────────
    print("\n┌─ RED FLAGS ─────────────────────────────────────────────────┐")
    severity = red_flags.get("severity", "NONE")
    flags    = red_flags.get("flags", [])
    new_f    = red_flags.get("new_flags", [])
    pers_f   = red_flags.get("persistent_flags", [])
    res_f    = red_flags.get("resolved_flags", [])

    colour = {"HIGH": "⚠", "MEDIUM": "◆", "LOW": "●", "NONE": "✓"}.get(severity, "?")
    print(f"│  Severity: {colour}  {severity}")
    print(f"│  Active flags ({len(flags)}):     {flags or '—'}")
    print(f"│  New this period:           {new_f or '—'}")
    print(f"│  Persistent:                {pers_f or '—'}")
    print(f"│  Resolved:                  {res_f or '—'}")

    # per-category breakdown
    cats = red_flags.get("categories_detected", [])
    if cats:
        print(f"│  Categories:                {cats}")
    nv = red_flags.get("new_vs_prior")
    if nv:
        print(f"│  New vs prior:              {nv}")
    print("└─────────────────────────────────────────────────────────────┘")

    # ── Key Themes ────────────────────────────────────────────────────
    print("\n┌─ KEY THEMES ────────────────────────────────────────────────┐")
    themes        = key_themes.get("themes", [])
    emerging      = key_themes.get("emerging_themes", [])
    fading        = key_themes.get("fading_themes", [])
    fin_alignment = key_themes.get("financial_alignment") or {}
    fin_aligned   = fin_alignment.get("aligned_themes", []) if isinstance(fin_alignment, dict) else []
    fin_conflict  = fin_alignment.get("conflicting_themes", []) if isinstance(fin_alignment, dict) else []

    if themes:
        for t in themes:
            if isinstance(t, dict):
                name  = t.get("theme", t.get("name", "?"))
                score = t.get("score", 0.0) or 0.0
            else:
                name, score = str(t), 0.0
            aligned = " ✓ aligned" if name in fin_aligned else (
                      " ✗ conflict" if name in fin_conflict else "")
            print(f"│  {name:<24} {_bar(score)}  {score:.2f}{aligned}")
    else:
        print("│  (no themes detected — insufficient document corpus)")

    if emerging:
        print(f"│  Emerging:    {emerging}")
    if fading:
        print(f"│  Fading:      {fading}")
    print("└─────────────────────────────────────────────────────────────┘")

    # ── Source Coverage ───────────────────────────────────────────────
    print("\n┌─ SOURCE COVERAGE ───────────────────────────────────────────┐")
    print(f"│  Earnings transcripts:   {coverage.get('earnings_transcripts', 0)}")
    print(f"│  Annual reports (10-K):  {coverage.get('annual_reports', 0)}")
    print(f"│  Press releases:         {coverage.get('press_releases', 0)}")
    print(f"│  Staleness flag:         {coverage.get('staleness_flag', 'N/A')}")
    newest = coverage.get("date_range_end")
    oldest = coverage.get("date_range_start")
    if newest:
        print(f"│  Date range:             {oldest}  →  {newest}")
    print("└─────────────────────────────────────────────────────────────┘")

    # ── Meta ──────────────────────────────────────────────────────────
    print("\n┌─ META ──────────────────────────────────────────────────────┐")
    print(f"│  Model version:    {meta.get('model_version', '?')}")
    print(f"│  NLP approach:     {meta.get('nlp_approach', '?')}")
    print(f"│  Data quality:     {meta.get('data_quality_flag', '?')}")
    print(f"│  Computed at:      {meta.get('computed_at', '?')}")
    warns = meta.get("warnings", [])
    if warns:
        print(f"│  Warnings ({len(warns)}):")
        for w in warns:
            print(f"│    · {w}")
    print("└─────────────────────────────────────────────────────────────┘")

    print("\n── RAW CONTRACT (nlp_insights) ──────────────────────────────")
    print(json.dumps(result, indent=2, default=str))


# ── Synthetic AAPL-style documents ───────────────────────────────────
# Mirrors language from real Apple earnings calls / 10-Ks (Q1-Q4 FY2025).

_AAPL_Q1_PREPARED = """
Good afternoon, everyone. We are pleased to report record revenue of $124 billion this quarter,
up 4% year over year, reflecting continued strong demand for our products and services.
Our Services segment achieved an all-time revenue record of $26.3 billion, growing 14% year over year,
demonstrating the strength and resilience of our ecosystem.
iPhone revenue was $69.1 billion, ahead of our expectations.
We are incredibly excited about the opportunities ahead, particularly in artificial intelligence
and machine learning, where Apple Intelligence is already delighting millions of customers.
Our operational discipline drove gross margins to 46.9%, the highest in our history.
We returned $30 billion to shareholders in the quarter through dividends and buybacks.
Looking forward, we remain confident in our long-term growth trajectory across all product categories.
We see strong momentum in emerging markets, particularly India and Southeast Asia.
"""

_AAPL_Q1_QNA = """
Q: Can you speak to iPhone demand trends in China and the competitive environment?
A: We saw some pressure in Greater China, which is a competitive market. However, we remain
   focused on delivering exceptional customer experiences. We are cautious about near-term
   demand signals but optimistic about the long-term opportunity.
Q: What is your outlook on AI monetization and when will it show up in revenue?
A: Apple Intelligence is driving customer satisfaction and upgrade rates. We believe AI will
   be a meaningful driver of Services growth over the next several years.
Q: Could you comment on supply chain risks given geopolitical tensions?
A: We have been diversifying our supply chain and are investing significantly in manufacturing
   capacity outside of China, including India and Vietnam. We feel good about our supply resilience.
"""

_AAPL_Q2_PREPARED = """
We delivered revenue of $95.4 billion, growing 5% year over year, continuing our strong performance.
Services revenue of $26.6 billion was another all-time record. We are seeing healthy engagement
across the App Store, Apple Music, iCloud, and AppleCare.
Gross margin expanded to 47.1%, reflecting the favorable mix shift toward high-margin services.
We continue to invest aggressively in research and development, with R&D spending up 7% year over year
as we accelerate innovation in AI, silicon, and health technology.
Our capital return program remains robust — we have returned over $700 billion to shareholders
since the program's inception.
We are excited about the expansion of Apple Intelligence features across our platforms.
Cost discipline remains a priority as we manage operating expenses carefully in this environment.
"""

_AAPL_Q2_QNA = """
Q: Margins have been strong but some investors are concerned about sustainability.
A: We see a durable margin expansion story driven by Services mix. We are disciplined on costs
   but we will not sacrifice investment in innovation. We feel good about where margins are headed.
Q: Are there any regulatory headwinds from the EU Digital Markets Act?
A: We are working constructively with regulators across all jurisdictions. The EU's DMA changes
   require us to implement new interoperability requirements. There is uncertainty around the
   final impact, but we believe we can navigate this. We face potential fines if compliance
   is deemed insufficient.
Q: Can you give more color on the India opportunity?
A: India is a huge opportunity. We opened flagship stores, continue to grow our manufacturing
   presence, and iPhone sales in India grew double digits. We are optimistic and investing.
"""

_AAPL_Q3_PREPARED = """
We are proud to report another record quarter with Services crossing $27 billion for the first time.
Total revenue of $85.8 billion grew 5% year over year. We see continued momentum in wearables
and accessories, with Apple Watch and AirPods delivering strong results.
Margin expansion story intact: gross margin of 46.5% despite ongoing macroeconomic uncertainty.
We remain committed to our capital allocation strategy, returning over $25 billion to shareholders.
Revenue growth is accelerating in international markets, particularly in the Asia-Pacific region.
We are very encouraged by the early traction of Apple Intelligence and the feature roadmap ahead.
"""

_AAPL_Q3_QNA = """
Q: Interest rates and consumer spending — do you see any softness?
A: Consumer spending has been resilient for premium products. We have not seen material demand
   destruction, though we remain cautious about macro headwinds in certain geographies.
Q: Competition in the AI space is intensifying. How does Apple differentiate?
A: Apple Intelligence is built on privacy-first architecture, tight hardware-software integration,
   and on-device processing. These are durable moats that competitors cannot replicate quickly.
Q: Any update on the antitrust situation with the DOJ?
A: We strongly disagree with the characterization of our business in the DOJ lawsuit.
   We believe the App Store benefits consumers and developers. We will vigorously defend ourselves.
   The outcome is uncertain and litigation risk is real.
"""

_AAPL_ANNUAL_10K = """
RISK FACTORS

The following risk factors could materially adversely affect our business, financial condition,
operating results, and prospects.

SUPPLY CHAIN CONCENTRATION: We are dependent on single-source suppliers for certain components.
Any disruption to our supply chain, including component shortages, could adversely affect our
ability to produce and deliver products in sufficient quantities and on a timely basis.
Our reliance on contract manufacturers in Asia creates exposure to geopolitical risks.

COMPETITION: We face intense competition in all our markets. Our competitors include Samsung,
Google, Microsoft, and numerous other global technology companies with substantial resources.
The pace of technological change is rapid and we may not be able to maintain our competitive
advantage.

REGULATORY: We are subject to complex and evolving laws and regulations worldwide including
data privacy, antitrust, and competition law. The EU's Digital Markets Act and investigations
by the DOJ and other regulators could result in significant fines, operational restrictions,
or changes to our business model.

MACROECONOMIC: Global economic conditions, including inflation, interest rates, and foreign
currency fluctuations, may adversely affect consumer demand and our financial results.
Geopolitical tensions, particularly between the US and China, create meaningful uncertainty.

MARGIN PRESSURE: Increasing competition and potential tariff impacts could pressure our
margins. We also face increasing R&D costs as we invest in next-generation technologies.

AI AND MACHINE LEARNING: We have invested and will continue to invest substantial resources
in artificial intelligence and machine learning. Apple Intelligence represents a significant
product enhancement. Cloud computing services supporting AI are increasingly important.
Revenue growth from AI features is expected to accelerate over the medium term.
Margin expansion from high-margin AI-driven services is a key strategic priority.
"""

def _make_transcript(quarter: str, year: int, date: str, prepared: str, qa: str) -> dict:
    """Build a document dict matching the engine's internal schema."""
    full = prepared + "\nQ&A SESSION\n" + qa
    return {
        "doc_type":   "earnings_transcript",
        "period":     f"Q{quarter} {year}",
        "date":       date,
        "source_url": None,
        "word_count": len(full.split()),
        "text":       full,
        "quarter":    quarter,
        "year":       year,
    }


def _make_annual(period: str, date: str, text: str) -> dict:
    return {
        "doc_type":   "annual_report",
        "period":     period,
        "date":       date,
        "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AAPL",
        "word_count": len(text.split()),
        "text":       text,
    }


_SYNTHETIC_DOCS = [
    _make_transcript("1", 2025, "2025-01-30", _AAPL_Q1_PREPARED, _AAPL_Q1_QNA),
    _make_transcript("2", 2025, "2025-05-01", _AAPL_Q2_PREPARED, _AAPL_Q2_QNA),
    _make_transcript("3", 2025, "2025-08-01", _AAPL_Q3_PREPARED, _AAPL_Q3_QNA),
    _make_annual("FY2024", "2024-11-01", _AAPL_ANNUAL_10K),
]


if __name__ == "__main__":
    sys.path.insert(0, "/home/user/Equity-research-platform")

    import backend.engines.engine_4_nlp as _e4
    import backend.engines.engine_4.engine as _e4_engine
    from backend.engines.engine_4_nlp import NLPIntelligenceEngine, validate_contract

    # ── Mode 1: Network run (real fetchers, will degrade gracefully) ──
    print("=" * 65)
    print("MODE 1: LIVE RUN (real fetchers — graceful degradation)")
    print("=" * 65)
    engine = NLPIntelligenceEngine()
    context = {"financial_data": AAPL_FINANCIAL_DATA}
    t0 = time.perf_counter()
    result_live = engine.run(context)
    elapsed_live = (time.perf_counter() - t0) * 1000
    ok_live, _ = validate_contract(result_live)
    print(f"  Contract: {'PASS ✓' if ok_live else 'FAIL ✗'}  |  "
          f"docs fetched: {result_live['source_coverage']['total_documents']}  |  "
          f"warnings: {result_live['meta']['warnings']}")

    # ── Mode 2: Injected synthetic AAPL transcripts ───────────────────
    print("\n" + "=" * 65)
    print("MODE 2: SYNTHETIC AAPL TRANSCRIPTS INJECTED (full pipeline)")
    print("=" * 65)

    # Monkey-patch the fetch functions to return synthetic docs.
    def _fake_transcripts(ticker, warnings, limit=4):
        return [d for d in _SYNTHETIC_DOCS if d["doc_type"] == "earnings_transcript"][:limit]

    def _fake_10k(ticker, warnings, limit=2):
        return [d for d in _SYNTHETIC_DOCS if d["doc_type"] == "annual_report"][:limit]

    def _fake_press(ticker, warnings, limit=4):
        return []

    # Patch in the module where the names are looked up at call time.
    _e4_engine.fetch_fmp_transcripts    = _fake_transcripts
    _e4_engine.fetch_edgar_10k          = _fake_10k
    _e4_engine.fetch_fmp_press_releases = _fake_press

    context2 = {"financial_data": AAPL_FINANCIAL_DATA}
    t1 = time.perf_counter()
    result = engine.run(context2)
    elapsed_ms = (time.perf_counter() - t1) * 1000

    ok, errs = validate_contract(result)
    display_results(result)

    print(f"\n{'═' * 65}")
    print(f"  Contract validation: {'PASS ✓' if ok else 'FAIL ✗'}")
    if errs:
        for e in errs:
            print(f"    - {e}")
    print(f"  Run time: {elapsed_ms:.1f} ms  (live mode: {elapsed_live:.0f} ms)")
    print("═" * 65)
