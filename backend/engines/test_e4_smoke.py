"""
Engine 4 — Focused smoke tests.

Each test isolates one concern: contract shape, graceful degradation, sentiment
scoring, red-flag detection (all 7 categories), theme extraction (all 9 themes),
financial alignment, source coverage, Q&A split, and live-fetcher degradation.

Run: python -m backend.engines.test_e4_smoke
Exits non-zero if any assertion fails.
"""

from __future__ import annotations

import logging
import sys
import traceback

# Silence the expected logger.exception calls from graceful-degradation tests.
logging.disable(logging.CRITICAL)

from backend.engines.engine_4.analysis import (
    _split_prepared_qna,
    _score_block,
    _detect_categories,
    _theme_hits,
    sentiment_scores,
    red_flag_analysis,
    key_themes_analysis,
    build_source_coverage,
    data_quality_flag,
)
from backend.engines.engine_4.helpers import (
    MODEL_VERSION,
    valid_fallback_schema,
    validate_contract,
)
from backend.engines.engine_4.patterns import (
    RED_FLAG_PATTERNS,
    THEME_KEYWORDS,
    VALID_CATEGORIES,
)
from backend.engines.engine_4 import NLPIntelligenceEngine
import backend.engines.engine_4.engine as _engine_mod
import backend.engines.engine_4.fetchers as _fetchers


# ── Test harness ──────────────────────────────────────────────────────
_PASS: list[str] = []
_FAIL: list[tuple[str, str]] = []


def run(name: str, fn):
    try:
        fn()
        _PASS.append(name)
        print(f"  PASS  {name}")
    except AssertionError as e:
        _FAIL.append((name, f"AssertionError: {e}"))
        print(f"  FAIL  {name} — {e}")
    except Exception as e:
        _FAIL.append((name, f"{type(e).__name__}: {e}\n{traceback.format_exc()}"))
        print(f"  ERR   {name} — {type(e).__name__}: {e}")


# ── Helpers for building synthetic docs ───────────────────────────────
def _doc(text: str, doc_type: str = "earnings_transcript",
         date: str = "2025-06-01", period: str = "Q2 2025") -> dict:
    return {
        "doc_type":   doc_type,
        "period":     period,
        "date":       date,
        "source_url": None,
        "word_count": len(text.split()),
        "text":       text,
    }


# ── 1. Contract shape & fallback ──────────────────────────────────────
def test_fallback_schema_is_valid():
    fb = valid_fallback_schema()
    ok, errs = validate_contract(fb)
    assert ok, f"fallback schema invalid: {errs}"
    assert fb["meta"]["model_version"] == MODEL_VERSION
    assert fb["red_flags"]["flags"] == []
    assert fb["source_coverage"]["staleness_flag"] is True


def test_fallback_schema_with_warnings():
    fb = valid_fallback_schema(["boom"])
    assert "boom" in fb["meta"]["warnings"]


def test_validate_contract_detects_missing_section():
    bad = valid_fallback_schema()
    del bad["red_flags"]
    ok, errs = validate_contract(bad)
    assert not ok
    assert any("red_flags" in e for e in errs)


def test_validate_contract_detects_none_list():
    bad = valid_fallback_schema()
    bad["red_flags"]["flags"] = None
    ok, errs = validate_contract(bad)
    assert not ok
    assert any("flags must be []" in e for e in errs)


# ── 2. Graceful degradation ───────────────────────────────────────────
def test_engine_with_no_ticker():
    out = NLPIntelligenceEngine().run({"financial_data": {}})
    ok, errs = validate_contract(out)
    assert ok, errs
    assert out["sentiment"]["status"] == "failed"
    assert any("ticker" in w.lower() for w in out["meta"]["warnings"])


def test_engine_survives_fetcher_exception():
    """If a fetcher raises, engine must still return a valid contract."""
    def bad_fetch(*_a, **_kw):
        raise RuntimeError("simulated fetcher crash")

    orig_t = _engine_mod.fetch_fmp_transcripts
    orig_e = _engine_mod.fetch_edgar_10k
    orig_p = _engine_mod.fetch_fmp_press_releases
    try:
        _engine_mod.fetch_fmp_transcripts    = bad_fetch
        _engine_mod.fetch_edgar_10k          = bad_fetch
        _engine_mod.fetch_fmp_press_releases = bad_fetch
        out = NLPIntelligenceEngine().run(
            {"financial_data": {"meta": {"ticker": "AAPL"}}}
        )
    finally:
        _engine_mod.fetch_fmp_transcripts    = orig_t
        _engine_mod.fetch_edgar_10k          = orig_e
        _engine_mod.fetch_fmp_press_releases = orig_p

    ok, errs = validate_contract(out)
    assert ok, errs
    # All three fetchers exploded → warnings should capture each
    joined = " ".join(out["meta"]["warnings"]).lower()
    assert "transcript" in joined
    assert "edgar" in joined


def test_engine_empty_documents():
    """No documents at all → sub-sections report 'failed' but contract holds."""
    _patch_all_fetchers([], [], [])
    try:
        out = NLPIntelligenceEngine().run(
            {"financial_data": {"meta": {"ticker": "AAPL"}}}
        )
    finally:
        _restore_fetchers()
    assert out["sentiment"]["status"] == "failed"
    assert out["red_flags"]["status"] == "failed"
    assert out["key_themes"]["status"] == "failed"
    assert out["source_coverage"]["total_documents"] == 0


# ── 3. Sentiment scoring ──────────────────────────────────────────────
def test_sentiment_overwhelmingly_positive():
    pos = _doc(("growth strong excellent record improve confident momentum "
                "beat outperform expansion innovation profitable efficiency "
                "gains positive opportunity upside resilient solid healthy "
                "milestone breakthrough optimistic ") * 5)
    s = sentiment_scores([pos])
    assert s["status"] == "success"
    assert s["overall_score"] is not None and s["overall_score"] > 0.7, (
        f"positive-only text should score >0.7, got {s['overall_score']}"
    )


def test_sentiment_overwhelmingly_negative():
    neg = _doc(("risk uncertainty volatile decline weakness pressure challenge "
                "headwind difficult unfavorable slowdown recession litigation "
                "lawsuit breach impairment layoff warning miss adverse "
                "deteriorate downturn loss disruption ") * 5)
    s = sentiment_scores([neg])
    assert s["status"] == "success"
    assert s["overall_score"] is not None and s["overall_score"] < 0.3, (
        f"negative-only text should score <0.3, got {s['overall_score']}"
    )


def test_sentiment_trend_improving():
    older = _doc("risk uncertainty decline weakness pressure headwind loss " * 3,
                 date="2024-01-01")
    newer = _doc("growth strong record improve momentum success expansion " * 3,
                 date="2025-01-01")
    s = sentiment_scores([older, newer])
    assert s["sentiment_trend"] == "Improving", (
        f"older-negative / newer-positive should be 'Improving', got {s['sentiment_trend']}"
    )


def test_sentiment_trend_deteriorating():
    older = _doc("growth strong record improve momentum success expansion " * 3,
                 date="2024-01-01")
    newer = _doc("risk uncertainty decline weakness pressure headwind loss " * 3,
                 date="2025-01-01")
    s = sentiment_scores([older, newer])
    assert s["sentiment_trend"] == "Deteriorating", (
        f"older-positive / newer-negative should be 'Deteriorating', got {s['sentiment_trend']}"
    )


def test_sentiment_no_documents():
    s = sentiment_scores([])
    assert s["status"] == "failed"
    assert s["overall_score"] is None


# ── 4. Red-flag detection — one test per category ────────────────────
def test_redflags_all_seven_categories_fire():
    """Feed one document that hits every category at least CATEGORY_MIN_HITS times."""
    parts: list[str] = []
    for _cat, patterns in RED_FLAG_PATTERNS.items():
        parts.append(" ".join(list(patterns)[:3] * 2))
    stuffed = _doc("\n".join(parts))
    out = red_flag_analysis([stuffed])
    assert out["status"] == "success"
    detected = set(out["categories_detected"])
    missing = set(VALID_CATEGORIES) - detected
    assert not missing, f"categories did not fire: {missing}"
    assert out["severity"] == "High"


def test_redflags_clean_text():
    clean = _doc("Our products are delightful and customers love them.")
    out = red_flag_analysis([clean])
    assert out["status"] == "success"
    assert out["flags_count"] == 0
    assert out["severity"] is None


def test_redflags_new_vs_prior():
    prior_text = " ".join(list(RED_FLAG_PATTERNS["supply_chain"])[:3] * 2)
    latest_text = " ".join(list(RED_FLAG_PATTERNS["litigation"])[:3] * 2)
    prior  = _doc(prior_text,  date="2024-05-01", period="Q2 2024")
    latest = _doc(latest_text, date="2025-05-01", period="Q2 2025")
    out = red_flag_analysis([prior, latest])
    nvp = out["new_vs_prior"]
    assert nvp is not None
    assert "litigation"   in nvp["new"],        f"new should include litigation: {nvp}"
    assert "supply_chain" in nvp["resolved"],   f"resolved should include supply_chain: {nvp}"


# ── 5. Theme extraction — verify each theme can be detected ──────────
def test_themes_every_theme_can_fire():
    """Build one doc per theme with heavy keyword density; confirm it ranks top."""
    failures: list[str] = []
    for theme, kws in THEME_KEYWORDS.items():
        focused = _doc((" ".join(kws) + " ") * 10)
        out = key_themes_analysis([focused], {})
        if theme not in (out.get("themes") or []):
            failures.append(f"{theme!r} did not rank (got {out.get('themes')})")
    assert not failures, "\n".join(failures)


def test_themes_emerging_and_fading():
    prior  = _doc(("cloud saas platform subscription ") * 5,
                  date="2024-05-01", period="Q2 2024")
    latest = _doc(("artificial intelligence machine learning neural network ") * 5,
                  date="2025-05-01", period="Q2 2025")
    out = key_themes_analysis([prior, latest], {})
    assert "AI / Machine Learning" in out["emerging_themes"], (
        f"emerging should contain AI, got {out['emerging_themes']}"
    )
    assert any("Cloud" in t or "SaaS" in t for t in out["fading_themes"]), (
        f"fading should contain Cloud/SaaS, got {out['fading_themes']}"
    )


def test_themes_no_documents():
    out = key_themes_analysis([], {"derived": {}})
    assert out["status"] == "failed"
    assert out["themes"] == []


# ── 6. Financial alignment ───────────────────────────────────────────
def test_financial_alignment_aligned():
    """Margin theme + improving margin series → Aligned."""
    doc = _doc(("margin expansion operating leverage margin improvement ") * 5)
    fin = {"derived": {"gross_margin": [0.40, 0.42, 0.44, 0.46, 0.48]}}
    out = key_themes_analysis([doc], fin)
    assert out["financial_alignment"] == "Aligned", (
        f"expected Aligned, got {out['financial_alignment']}"
    )


def test_financial_alignment_divergent():
    """Margin theme + declining margin series → Divergent."""
    doc = _doc(("margin expansion operating leverage margin improvement ") * 5)
    fin = {"derived": {"gross_margin": [0.50, 0.48, 0.46, 0.42, 0.38]}}
    out = key_themes_analysis([doc], fin)
    assert out["financial_alignment"] == "Divergent", (
        f"expected Divergent, got {out['financial_alignment']}"
    )


def test_financial_alignment_revenue_divergent():
    """Revenue-growth theme + negative YoY → Divergent."""
    doc = _doc(("revenue growth top-line growth sales growth ") * 5)
    fin = {"derived": {"revenue_yoy": [0.05, -0.08]}}
    out = key_themes_analysis([doc], fin)
    assert out["financial_alignment"] == "Divergent"


# ── 7. Source coverage & staleness ───────────────────────────────────
def test_source_coverage_staleness_flag_true_for_old_docs():
    ancient = _doc("some text", date="2020-01-01")
    sc = build_source_coverage([ancient])
    assert sc["staleness_flag"] is True


def test_source_coverage_counts_by_doc_type():
    docs = [
        _doc("a", doc_type="earnings_transcript", date="2025-06-01"),
        _doc("b", doc_type="earnings_transcript", date="2025-03-01"),
        _doc("c", doc_type="annual_report",        date="2024-11-01"),
        _doc("d", doc_type="press_release",        date="2025-07-01"),
    ]
    sc = build_source_coverage(docs)
    assert sc["earnings_transcripts"] == 2
    assert sc["annual_reports"]       == 1
    assert sc["total_documents"]      == 4


def test_data_quality_flag_tiers():
    assert data_quality_flag(0) == "minimal"
    assert data_quality_flag(1) == "partial"
    assert data_quality_flag(4) == "clean"
    assert data_quality_flag(99) == "clean"


# ── 8. Q&A split heuristic ───────────────────────────────────────────
def test_qna_split_marker_present():
    text = ("Prepared remarks go here. We are confident about growth. "
            "We will now begin the question-and-answer session. "
            "Q: What about margins? A: We see expansion.")
    prepared, qna = _split_prepared_qna(text)
    assert "Prepared remarks go here" in prepared
    assert "What about margins" in qna
    assert "Prepared remarks go here" not in qna


def test_qna_split_no_marker():
    prepared, qna = _split_prepared_qna("Just a monologue with no Q&A section.")
    assert qna == ""
    assert prepared.startswith("Just a monologue")


# ── 9. Guidance marker scoring ───────────────────────────────────────
def test_guidance_tone_positive():
    text = ("Our outlook is strong. We expect record growth and robust momentum. "
            "Guidance is positive with confident expansion and healthy margins.")
    s = _score_block(text)
    assert s["guidance_pos"] > s["guidance_neg"]


def test_guidance_tone_negative():
    text = ("Our outlook is challenging with significant headwinds. "
            "Guidance expects uncertainty, pressure, and declining demand.")
    s = _score_block(text)
    assert s["guidance_neg"] > s["guidance_pos"]


# ── 10. Live fetchers degrade gracefully (no network / no key) ───────
def test_live_fetchers_return_empty_without_network():
    warnings: list[str] = []
    # FMP requires a key; in the sandbox the key is absent or network is blocked.
    t = _fetchers.fetch_fmp_transcripts("AAPL", warnings, limit=2)
    e = _fetchers.fetch_edgar_10k("AAPL", warnings, limit=1)
    p = _fetchers.fetch_fmp_press_releases("AAPL", warnings, limit=2)
    assert isinstance(t, list)
    assert isinstance(e, list)
    assert isinstance(p, list)
    # All three must produce a warning (or empty list silently for press)
    assert any("FMP" in w or "EDGAR" in w for w in warnings), (
        f"expected a degradation warning, got {warnings!r}"
    )


# ── 11. EDGAR diagnostic warnings — map status codes to clear messages ─
def test_edgar_403_emits_actionable_warning():
    """403 → warning must mention both possible causes (UA reject, proxy block)."""
    orig = _fetchers._http_get_json
    _fetchers._http_get_json = lambda *_a, **_kw: (403, None)
    warnings: list[str] = []
    try:
        out = _fetchers.fetch_edgar_10k("AAPL", warnings, limit=1)
    finally:
        _fetchers._http_get_json = orig
    assert out == []
    joined = " ".join(warnings)
    assert "403" in joined, f"403 warning should mention status, got {warnings!r}"
    assert "SEC_USER_AGENT" in joined, (
        f"403 warning should mention SEC_USER_AGENT fix, got {warnings!r}"
    )
    assert "proxy" in joined.lower() or "network" in joined.lower() or "firewall" in joined.lower(), (
        f"403 warning should acknowledge network-block possibility, got {warnings!r}"
    )


def test_edgar_429_emits_ratelimit_warning():
    orig = _fetchers._http_get_json
    _fetchers._http_get_json = lambda *_a, **_kw: (429, None)
    warnings: list[str] = []
    try:
        _fetchers.fetch_edgar_10k("AAPL", warnings, limit=1)
    finally:
        _fetchers._http_get_json = orig
    assert any("429" in w and "rate" in w.lower() for w in warnings), warnings


def test_edgar_no_hits_for_unknown_ticker():
    """Valid empty response → specific 'no hits' warning, not a generic error."""
    orig = _fetchers._http_get_json
    _fetchers._http_get_json = lambda *_a, **_kw: (200, {"hits": {"hits": []}})
    warnings: list[str] = []
    try:
        out = _fetchers.fetch_edgar_10k("ZZZZ", warnings, limit=1)
    finally:
        _fetchers._http_get_json = orig
    assert out == []
    assert any("no 10-K hits" in w for w in warnings), warnings


def test_sec_ua_placeholder_detector():
    assert _fetchers._sec_user_agent_is_placeholder("")
    assert _fetchers._sec_user_agent_is_placeholder("Company name@example.com")
    assert _fetchers._sec_user_agent_is_placeholder("TODO set real UA")
    assert not _fetchers._sec_user_agent_is_placeholder("Annant Research annant@mydomain.io")


# ── Fetcher patch helpers ────────────────────────────────────────────
_orig_fetchers: dict = {}


def _patch_all_fetchers(transcripts, annual, press):
    _orig_fetchers["t"] = _engine_mod.fetch_fmp_transcripts
    _orig_fetchers["e"] = _engine_mod.fetch_edgar_10k
    _orig_fetchers["p"] = _engine_mod.fetch_fmp_press_releases
    _engine_mod.fetch_fmp_transcripts    = lambda *_a, **_kw: list(transcripts)
    _engine_mod.fetch_edgar_10k          = lambda *_a, **_kw: list(annual)
    _engine_mod.fetch_fmp_press_releases = lambda *_a, **_kw: list(press)


def _restore_fetchers():
    _engine_mod.fetch_fmp_transcripts    = _orig_fetchers["t"]
    _engine_mod.fetch_edgar_10k          = _orig_fetchers["e"]
    _engine_mod.fetch_fmp_press_releases = _orig_fetchers["p"]


# ── Runner ────────────────────────────────────────────────────────────
TESTS = [
    # contract + fallback
    ("fallback_schema_is_valid",            test_fallback_schema_is_valid),
    ("fallback_schema_with_warnings",       test_fallback_schema_with_warnings),
    ("validate_contract_detects_missing",   test_validate_contract_detects_missing_section),
    ("validate_contract_detects_none_list", test_validate_contract_detects_none_list),
    # graceful degradation
    ("engine_with_no_ticker",               test_engine_with_no_ticker),
    ("engine_survives_fetcher_exception",   test_engine_survives_fetcher_exception),
    ("engine_empty_documents",              test_engine_empty_documents),
    # sentiment
    ("sentiment_overwhelmingly_positive",   test_sentiment_overwhelmingly_positive),
    ("sentiment_overwhelmingly_negative",   test_sentiment_overwhelmingly_negative),
    ("sentiment_trend_improving",           test_sentiment_trend_improving),
    ("sentiment_trend_deteriorating",       test_sentiment_trend_deteriorating),
    ("sentiment_no_documents",              test_sentiment_no_documents),
    # red flags
    ("redflags_all_seven_categories_fire",  test_redflags_all_seven_categories_fire),
    ("redflags_clean_text",                 test_redflags_clean_text),
    ("redflags_new_vs_prior",               test_redflags_new_vs_prior),
    # themes
    ("themes_every_theme_can_fire",         test_themes_every_theme_can_fire),
    ("themes_emerging_and_fading",          test_themes_emerging_and_fading),
    ("themes_no_documents",                 test_themes_no_documents),
    # financial alignment
    ("financial_alignment_aligned",         test_financial_alignment_aligned),
    ("financial_alignment_divergent",       test_financial_alignment_divergent),
    ("financial_alignment_revenue_diverge", test_financial_alignment_revenue_divergent),
    # source coverage
    ("source_coverage_staleness",           test_source_coverage_staleness_flag_true_for_old_docs),
    ("source_coverage_counts_by_type",      test_source_coverage_counts_by_doc_type),
    ("data_quality_flag_tiers",             test_data_quality_flag_tiers),
    # Q&A split
    ("qna_split_marker_present",            test_qna_split_marker_present),
    ("qna_split_no_marker",                 test_qna_split_no_marker),
    # guidance
    ("guidance_tone_positive",              test_guidance_tone_positive),
    ("guidance_tone_negative",              test_guidance_tone_negative),
    # live fetchers
    ("live_fetchers_degrade_gracefully",    test_live_fetchers_return_empty_without_network),
    # EDGAR diagnostic warnings
    ("edgar_403_emits_actionable_warning",  test_edgar_403_emits_actionable_warning),
    ("edgar_429_emits_ratelimit_warning",   test_edgar_429_emits_ratelimit_warning),
    ("edgar_no_hits_for_unknown_ticker",    test_edgar_no_hits_for_unknown_ticker),
    ("sec_ua_placeholder_detector",         test_sec_ua_placeholder_detector),
]


if __name__ == "__main__":
    print("=" * 65)
    print(f"  Engine 4 — Smoke test suite  ({len(TESTS)} tests)")
    print("=" * 65)
    for name, fn in TESTS:
        run(name, fn)

    print("\n" + "=" * 65)
    print(f"  Passed: {len(_PASS)} / {len(TESTS)}   |   Failed: {len(_FAIL)}")
    print("=" * 65)
    if _FAIL:
        print("\nFailures:")
        for name, msg in _FAIL:
            print(f"\n--- {name} ---\n{msg}")
        sys.exit(1)
    sys.exit(0)
