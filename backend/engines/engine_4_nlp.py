"""
Engine 4 — NLP Intelligence Engine (Owner: Annant)
===================================================

Input:  financial_data (from bus) + external transcripts (FMP, SEC EDGAR)
Output: nlp_insights (to bus) — 34-field contract

Responsibilities:
    - Sentiment analysis on earnings calls and annual reports
    - Risk word frequency (raw — E5 applies the > 0.07 threshold, not E4)
    - Tone shift detection across the last 4 quarters
    - Topic modeling and emerging/fading theme tracking
    - Management optimism scoring (prepared remarks only)
    - Red flag identification across 7 category classes
    - Financial alignment cross-check vs E1 derived metrics

Guarantees (all non-negotiable):
    - run() NEVER raises — all failures caught internally
    - list-typed fields are always [] (never None)
    - Sub-components fail independently (one can fail, others continue)
    - E4 does NOT import E2 or E3
    - E4 does NOT apply the risk-word threshold (E5's job)

Build is staged in phases. Current phase: 5 (themes + financial_alignment).
"""

from __future__ import annotations

import datetime
import json
import logging
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

from backend.engines.shared_config import (
    FMP_API_KEY,
    NLP_LOOKBACK_QUARTERS,
    STALENESS_DAYS,
)
from backend.pipeline.base_engine import BaseEngine

logger = logging.getLogger(__name__)


# ── Module constants ─────────────────────────────────────────────────

MODEL_VERSION = "1.0.0"

VALID_CATEGORIES = [
    "supply_chain",
    "guidance_decline",
    "litigation",
    "margin_pressure",
    "competition",
    "regulatory",
    "macro_exposure",
]

# HTTP settings shared by every external fetch in this engine.
_HTTP_TIMEOUT_S: float = 5.0
_HTTP_USER_AGENT: str = (
    "Equity-Research-Platform/1.0 (engine_4_nlp; contact: team@example.com)"
)

# Base URLs (kept as constants so tests can patch them.)
_FMP_BASE = "https://financialmodelingprep.com/api/v3"
_EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"


# ── Helpers ──────────────────────────────────────────────────────────

def _now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def valid_fallback_schema(warnings: list[str] | None = None) -> dict:
    """Return the full 34-field nlp_insights contract populated with safe defaults.

    Called whenever E4 cannot complete its work — guarantees E5 always receives
    a schema-valid dict. All list fields are empty lists (never None);
    scalar fields use None where data is unavailable.

    Args:
        warnings: Optional warnings to include in meta.warnings. A default
                  warning is prepended when no warnings are supplied.

    Returns:
        A dict matching the nlp_insights bus key contract.
    """
    warn_list: list[str] = list(warnings) if warnings else []
    if not warn_list:
        warn_list = ["Engine 4 failed — NLP section unavailable"]

    return {
        "sentiment": {
            "status": "failed",
            "overall_score": None,
            "management_optimism": None,
            "risk_word_frequency": None,
            "uncertainty_score": None,
            "forward_guidance_tone": None,
            "sentiment_trend": None,
            "qna_vs_prepared_delta": None,
        },
        "red_flags": {
            "status": "failed",
            "flags": [],
            "flags_count": 0,
            "severity": None,
            "categories_detected": [],
            "new_vs_prior": None,
        },
        "key_themes": {
            "status": "failed",
            "themes": [],
            "theme_scores": None,
            "emerging_themes": [],
            "fading_themes": [],
            "financial_alignment": None,
        },
        "source_coverage": {
            "status": "failed",
            "earnings_transcripts": 0,
            "annual_reports": 0,
            "total_documents": 0,
            "date_range_start": None,
            "date_range_end": None,
            "most_recent_quarter": None,
            "staleness_flag": True,
            "sources_list": [],
        },
        "meta": {
            "computed_at": _now_iso(),
            "model_version": MODEL_VERSION,
            "nlp_approach": "none",
            "warnings": warn_list,
            "data_quality_flag": "minimal",
            "assumptions": {},
        },
    }


# ── Word lists (rule-based sentiment) ────────────────────────────────
# Finance-domain lexicons. Intentionally concise; expand as needed without
# changing the scoring logic. Single-word entries only — multi-word phrases
# are matched separately via substring search on lowercased text.

POSITIVE_WORDS: set[str] = {
    "growth", "strong", "excellent", "record", "improve", "improved",
    "improving", "confident", "confidence", "momentum", "success", "successful",
    "robust", "accelerate", "accelerating", "beat", "outperform", "outperformed",
    "expansion", "expand", "innovation", "leadership", "advantage", "profitable",
    "profitability", "efficient", "efficiency", "exceeded", "gain", "gains",
    "positive", "opportunity", "opportunities", "upside", "resilient", "solid",
    "healthy", "achievement", "milestone", "breakthrough", "optimistic",
}

RISK_WORDS: set[str] = {
    "risk", "risks", "uncertainty", "uncertainties", "volatile", "volatility",
    "decline", "declining", "declined", "weakness", "weaken", "weakening",
    "pressure", "challenge", "challenges", "challenging", "headwind",
    "headwinds", "difficult", "difficulty", "unfavorable", "slowdown",
    "recession", "litigation", "investigation", "lawsuit", "breach",
    "impairment", "restructuring", "layoff", "layoffs", "warning", "shortfall",
    "miss", "missed", "adverse", "deteriorate", "deteriorating", "downturn",
    "loss", "losses", "disrupt", "disruption", "shortage", "shortages",
}

HEDGING_WORDS: set[str] = {
    "may", "might", "could", "possibly", "potentially", "approximately",
    "somewhat", "uncertain", "likely", "estimate", "estimates", "assume",
    "assumption", "believe", "anticipate", "anticipated", "roughly",
    "contingent", "approximate", "perhaps", "expected", "expects",
    "projected", "intend", "intends", "seek",
}

# Markers used to split prepared remarks from Q&A in earnings call transcripts.
# Case-insensitive substring match on the transcript body.
_QNA_MARKERS: tuple[str, ...] = (
    "question-and-answer session",
    "question and answer session",
    "we will now begin the question",
    "open the call for questions",
    "our first question comes",
    "move to the q&a",
    "begin our q&a",
)

# Markers that indicate forward guidance remarks. Presence of positive /
# negative modifiers nearby drives the forward_guidance_tone classification.
_GUIDANCE_MARKERS: tuple[str, ...] = (
    "guidance", "outlook", "expect", "we anticipate", "fiscal year",
    "next quarter", "full year", "forward",
)


# ── Text processing primitives ───────────────────────────────────────

_TOKEN_RE = re.compile(r"[a-zA-Z]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokens. Punctuation and numbers stripped."""
    if not text:
        return []
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]


def _count_in(tokens: list[str], vocab: set[str]) -> int:
    """Count the number of tokens that appear in vocab."""
    if not tokens:
        return 0
    return sum(1 for t in tokens if t in vocab)


def _split_prepared_qna(text: str) -> tuple[str, str]:
    """Split transcript into (prepared_remarks, qna) using heuristic markers.

    If no marker is found the entire text is treated as prepared remarks
    and the Q&A half is empty.
    """
    if not text:
        return ("", "")
    lower = text.lower()
    split_at: int | None = None
    for marker in _QNA_MARKERS:
        idx = lower.find(marker)
        if idx != -1 and (split_at is None or idx < split_at):
            split_at = idx
    if split_at is None:
        return (text, "")
    return (text[:split_at], text[split_at:])


def _score_block(text: str) -> dict[str, float | int]:
    """Return raw counts + length for a single text block.

    Keys: tokens, positive, risk, hedge, guidance_neg, guidance_pos.
    Derived ratios are computed at the aggregate level in _sentiment_scores.
    """
    tokens = _tokenize(text)
    total = len(tokens)
    if total == 0:
        return {
            "tokens": 0, "positive": 0, "risk": 0, "hedge": 0,
            "guidance_neg": 0, "guidance_pos": 0,
        }

    lower = text.lower()
    guidance_neg = 0
    guidance_pos = 0
    for marker in _GUIDANCE_MARKERS:
        idx = lower.find(marker)
        while idx != -1:
            window = lower[max(0, idx - 60): idx + 60]
            window_tokens = _tokenize(window)
            guidance_neg += _count_in(window_tokens, RISK_WORDS)
            guidance_pos += _count_in(window_tokens, POSITIVE_WORDS)
            idx = lower.find(marker, idx + 1)

    return {
        "tokens": total,
        "positive": _count_in(tokens, POSITIVE_WORDS),
        "risk": _count_in(tokens, RISK_WORDS),
        "hedge": _count_in(tokens, HEDGING_WORDS),
        "guidance_neg": guidance_neg,
        "guidance_pos": guidance_pos,
    }


def _sentiment_from_counts(pos: int, risk: int, tokens: int) -> float | None:
    """Compute a 0..1 sentiment score from positive/risk/token counts.

    Formula: (pos - risk) scaled against total tokens with a soft sigmoid,
    then clipped to [0, 1]. 0.5 is neutral.
    """
    if tokens <= 0:
        return None
    raw = (pos - risk) / tokens
    # Map [-0.05, +0.05] roughly to [0, 1] with 0 mapping to 0.5.
    scaled = 0.5 + raw * 10
    return max(0.0, min(1.0, scaled))


# ── Sentiment analysis ───────────────────────────────────────────────

def _classify_guidance_tone(
    guidance_pos: int, guidance_neg: int,
) -> str | None:
    """Classify forward_guidance_tone from positive/negative counts near
    guidance markers. Returns None when no guidance language is found."""
    total = guidance_pos + guidance_neg
    if total == 0:
        return "Absent"
    ratio = (guidance_pos - guidance_neg) / total
    if ratio > 0.2:
        return "Positive"
    if ratio < -0.2:
        return "Cautious"
    return "Neutral"


def _compute_sentiment_trend(
    per_doc_scores: list[tuple[str, float]],
) -> str | None:
    """Compare recent-half average vs older-half average of per-document
    sentiment scores. Returns one of Improving/Stable/Deteriorating, or
    None when fewer than 2 scored documents are available.

    per_doc_scores: list of (date_iso, overall_score) oldest-first.
    """
    scored = [s for _, s in per_doc_scores if s is not None]
    if len(scored) < 2:
        return None
    mid = len(scored) // 2
    older = scored[:mid] if mid else [scored[0]]
    recent = scored[mid:]
    if not older or not recent:
        return None
    delta = (sum(recent) / len(recent)) - (sum(older) / len(older))
    if delta > 0.05:
        return "Improving"
    if delta < -0.05:
        return "Deteriorating"
    return "Stable"


def _sentiment_scores(documents: list[dict]) -> dict:
    """Compute the sentiment sub-object from all available documents.

    Earnings transcripts drive overall_score, risk_word_frequency, and
    trend. management_optimism and qna_vs_prepared_delta use prepared-
    vs-Q&A splits. If no scorable text exists, returns a "failed" block
    with null scalars.
    """
    texts = [d for d in documents if d.get("text")]
    if not texts:
        return {
            "status": "failed",
            "overall_score": None,
            "management_optimism": None,
            "risk_word_frequency": None,
            "uncertainty_score": None,
            "forward_guidance_tone": None,
            "sentiment_trend": None,
            "qna_vs_prepared_delta": None,
        }

    # Aggregate across all documents.
    totals = {"tokens": 0, "positive": 0, "risk": 0, "hedge": 0,
              "guidance_neg": 0, "guidance_pos": 0}
    prepared_totals = {"tokens": 0, "positive": 0, "risk": 0}
    qna_totals = {"tokens": 0, "positive": 0, "risk": 0}
    per_doc_scores: list[tuple[str, float]] = []

    for doc in texts:
        scores = _score_block(doc["text"])
        for k, v in scores.items():
            totals[k] += v

        # Prepared / Q&A split is meaningful only on transcripts.
        if doc.get("doc_type") == "earnings_transcript":
            prepared, qna = _split_prepared_qna(doc["text"])
            p_scores = _score_block(prepared)
            q_scores = _score_block(qna)
            for k in ("tokens", "positive", "risk"):
                prepared_totals[k] += p_scores[k]
                qna_totals[k] += q_scores[k]

        doc_score = _sentiment_from_counts(
            scores["positive"], scores["risk"], scores["tokens"],
        )
        if doc_score is not None:
            per_doc_scores.append((doc.get("date") or "", doc_score))

    overall = _sentiment_from_counts(
        totals["positive"], totals["risk"], totals["tokens"],
    )
    management = _sentiment_from_counts(
        prepared_totals["positive"], prepared_totals["risk"],
        prepared_totals["tokens"],
    )
    qna_score = _sentiment_from_counts(
        qna_totals["positive"], qna_totals["risk"], qna_totals["tokens"],
    )

    risk_freq = (
        totals["risk"] / totals["tokens"] if totals["tokens"] else None
    )
    uncertainty = (
        totals["hedge"] / totals["tokens"] if totals["tokens"] else None
    )
    guidance_tone = _classify_guidance_tone(
        totals["guidance_pos"], totals["guidance_neg"],
    )

    delta = None
    if management is not None and qna_score is not None:
        delta = round(management - qna_score, 4)

    per_doc_scores.sort(key=lambda t: t[0])
    trend = _compute_sentiment_trend(per_doc_scores)

    status = "success" if totals["tokens"] > 0 else "failed"

    return {
        "status": status,
        "overall_score": round(overall, 4) if overall is not None else None,
        "management_optimism": (
            round(management, 4) if management is not None else None
        ),
        "risk_word_frequency": (
            round(risk_freq, 4) if risk_freq is not None else None
        ),
        "uncertainty_score": (
            round(uncertainty, 4) if uncertainty is not None else None
        ),
        "forward_guidance_tone": guidance_tone,
        "sentiment_trend": trend,
        "qna_vs_prepared_delta": delta,
    }


# ── Red flag detection ───────────────────────────────────────────────
# Each category maps to a tuple of substring patterns matched case-
# insensitively against the full document text. Patterns are deliberately
# short to catch inflections without over-fitting.

_RED_FLAG_PATTERNS: dict[str, tuple[str, ...]] = {
    "supply_chain": (
        "supply chain", "disruption", "shortage", "bottleneck",
        "logistics", "inventory build", "component shortage",
    ),
    "guidance_decline": (
        "lower guidance", "reducing outlook", "revised downward",
        "cut guidance", "withdrew guidance", "lowering guidance",
        "below guidance", "reduced forecast", "guided lower",
    ),
    "litigation": (
        "lawsuit", "litigation", "plaintiff", "class action",
        "settlement", "fine", "penalty", "regulatory action",
        "consent decree", "subpoena",
    ),
    "margin_pressure": (
        "margin pressure", "cost inflation", "input cost",
        "pricing pressure", "margin compression",
        "gross margin decline", "gross margin decrease", "cost pressure",
    ),
    "competition": (
        "competitive pressure", "market share loss",
        "losing share", "new entrant", "competitor", "price war",
        "increased competition",
    ),
    "regulatory": (
        "regulatory", "compliance risk", "new regulation",
        "regulatory scrutiny", "sec inquiry", "policy change",
        "antitrust",
    ),
    "macro_exposure": (
        "inflation", "recession", "interest rate", "currency headwind",
        "fx headwind", "economic slowdown", "geopolitical",
        "commodity price",
    ),
}

# Human-readable flag phrases by category (category -> display template).
_FLAG_TEMPLATES: dict[str, str] = {
    "supply_chain":     "Supply chain disruption language detected",
    "guidance_decline": "Guidance reduction language detected",
    "litigation":       "Litigation / regulatory action exposure",
    "margin_pressure":  "Margin pressure / cost inflation concerns",
    "competition":      "Competitive pressure or market share loss",
    "regulatory":       "Regulatory / compliance risk mentions",
    "macro_exposure":   "Macro headwind exposure (inflation, FX, rates)",
}

# Category hit threshold per document — prevents single incidental mentions
# from flipping a flag.
_CATEGORY_MIN_HITS: int = 2


def _detect_categories(text: str) -> dict[str, int]:
    """Return a dict of {category: hit_count} for the document.

    A hit = one occurrence of any pattern in that category.
    """
    if not text:
        return {cat: 0 for cat in VALID_CATEGORIES}
    lower = text.lower()
    out: dict[str, int] = {}
    for category, patterns in _RED_FLAG_PATTERNS.items():
        count = 0
        for pat in patterns:
            # overlapping occurrences are fine — count each independently
            start = 0
            while True:
                idx = lower.find(pat, start)
                if idx == -1:
                    break
                count += 1
                start = idx + len(pat)
        out[category] = count
    return out


def _severity_from_flag_count(n: int) -> str | None:
    if n == 0:
        return None
    if n >= 4:
        return "High"
    if n >= 2:
        return "Medium"
    return "Low"


def _red_flag_analysis(documents: list[dict]) -> dict:
    """Analyze all documents for red flag category hits.

    Compares the most recent transcript's categories against the union
    of categories in older transcripts to populate `new_vs_prior`.
    Categories firing only in the latest period are "new"; those
    firing in older periods but not the latest are "resolved"; those
    firing in both are "persistent". When only one period is available,
    `new_vs_prior` is None.
    """
    transcripts = [
        d for d in documents if d.get("doc_type") == "earnings_transcript"
    ]
    scorable = [d for d in documents if d.get("text")]

    if not scorable:
        return {
            "status": "failed",
            "flags": [],
            "flags_count": 0,
            "severity": None,
            "categories_detected": [],
            "new_vs_prior": None,
        }

    # Overall category tally across all documents.
    totals: dict[str, int] = {cat: 0 for cat in VALID_CATEGORIES}
    for d in scorable:
        for cat, hits in _detect_categories(d["text"]).items():
            totals[cat] += hits

    detected = [
        cat for cat, n in totals.items() if n >= _CATEGORY_MIN_HITS
    ]

    flags = [
        _FLAG_TEMPLATES[cat] for cat in detected if cat in _FLAG_TEMPLATES
    ][:10]

    # new_vs_prior uses transcripts sorted oldest-first.
    new_vs_prior: dict | None = None
    if len(transcripts) >= 2:
        by_date = sorted(transcripts, key=lambda d: d.get("date") or "")
        latest = by_date[-1]
        prior = by_date[:-1]

        latest_cats = {
            cat for cat, hits in _detect_categories(latest["text"]).items()
            if hits >= _CATEGORY_MIN_HITS
        }
        prior_cats: set[str] = set()
        for d in prior:
            for cat, hits in _detect_categories(d["text"]).items():
                if hits >= _CATEGORY_MIN_HITS:
                    prior_cats.add(cat)

        new_vs_prior = {
            "new":        sorted(latest_cats - prior_cats),
            "resolved":   sorted(prior_cats - latest_cats),
            "persistent": sorted(latest_cats & prior_cats),
        }

    return {
        "status": "success",
        "flags": flags,
        "flags_count": len(flags),
        "severity": _severity_from_flag_count(len(flags)),
        "categories_detected": detected,
        "new_vs_prior": new_vs_prior,
    }


# ── Theme extraction + financial alignment ──────────────────────────
# Theme candidates with keyword anchors. The scoring model counts
# keyword hits per theme per document, normalizes to hit-rate per 1000
# tokens, and returns the top 3-5 themes by aggregate rate.

_THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "AI / Machine Learning": (
        "artificial intelligence", "machine learning", "generative",
        " ai ", " ai,", " ai.", " llm", "large language model",
        "neural network",
    ),
    "Cloud / SaaS": (
        "cloud", "saas", "software as a service", "platform",
        "infrastructure as a service", " paas",
    ),
    "Services / Recurring Revenue": (
        "services revenue", "subscription", "recurring revenue",
        "annual recurring", "arr",
    ),
    "International Expansion": (
        "international", "overseas", "global market", "emerging market",
        " china", " europe", " india", " japan",
    ),
    "Capital Returns": (
        "dividend", "buyback", "share repurchase", "return capital",
        "capital return",
    ),
    "Margin Expansion": (
        "margin expansion", "operating leverage", "margin improvement",
        "gross margin expansion",
    ),
    "Revenue Growth": (
        "revenue growth", "top-line growth", "topline", "top line growth",
        "sales growth",
    ),
    "Product Innovation": (
        "innovation", "new product", "product launch", "r&d investment",
        "research and development", "product pipeline",
    ),
    "Cost Discipline / Efficiency": (
        "cost discipline", "cost efficiency", "productivity",
        "cost reduction", "operating efficiency", "restructuring savings",
    ),
}


def _theme_hits(text: str) -> dict[str, int]:
    """Count keyword hits per theme in a single document."""
    if not text:
        return {theme: 0 for theme in _THEME_KEYWORDS}
    lower = text.lower()
    out: dict[str, int] = {}
    for theme, keywords in _THEME_KEYWORDS.items():
        count = 0
        for kw in keywords:
            start = 0
            while True:
                idx = lower.find(kw, start)
                if idx == -1:
                    break
                count += 1
                start = idx + len(kw)
        out[theme] = count
    return out


def _rank_themes(
    theme_rates: dict[str, float], top_n: int = 5,
) -> tuple[list[str], dict[str, float]]:
    """Return (themes_list, scaled_scores) for the top_n themes by rate.

    Scores are scaled relative to the top theme (top = 1.0).
    """
    ranked = sorted(
        [(theme, rate) for theme, rate in theme_rates.items() if rate > 0],
        key=lambda t: t[1],
        reverse=True,
    )[:top_n]
    if not ranked:
        return [], {}
    top = ranked[0][1] or 1.0
    themes = [t for t, _ in ranked]
    scores = {t: round(r / top, 4) for t, r in ranked}
    return themes, scores


def _is_declining(series: list) -> bool:
    """Return True when a numeric series trends down in its latest half."""
    vals = [v for v in (series or []) if isinstance(v, (int, float))]
    if len(vals) < 3:
        return False
    mid = len(vals) // 2
    older = sum(vals[:mid]) / mid
    recent = sum(vals[mid:]) / (len(vals) - mid)
    return recent < older * 0.98  # 2% tolerance


def _financial_alignment(
    themes: list[str], financial_data: dict,
) -> str | None:
    """Cross-check extracted themes against E1 financial data.

    Returns "Divergent" when a theme claim contradicts the numbers
    (e.g. talks margin expansion but gross_margin is declining),
    "Aligned" when metrics support the themes, and None when the
    required E1 derived metrics are unavailable.
    """
    if not themes:
        return None

    # Pull derived metrics (main bus layout uses "derived", prompt uses
    # "derived_metrics" — support both).
    derived = (
        financial_data.get("derived")
        or financial_data.get("derived_metrics")
        or {}
    )
    if not derived:
        return None

    gm_series = derived.get("gross_margin")
    revenue_yoy = derived.get("revenue_yoy")

    # Normalize revenue_yoy to a single latest number if it's a list.
    latest_yoy = None
    if isinstance(revenue_yoy, list):
        for v in reversed(revenue_yoy):
            if isinstance(v, (int, float)):
                latest_yoy = v
                break
    elif isinstance(revenue_yoy, (int, float)):
        latest_yoy = revenue_yoy

    divergences: list[str] = []
    aligned_any = False

    talks_margin = any("margin" in t.lower() for t in themes)
    if talks_margin and isinstance(gm_series, list) and gm_series:
        if _is_declining(gm_series):
            divergences.append("margin_expansion_vs_declining_gm")
        else:
            aligned_any = True

    talks_revenue_growth = any(
        "revenue growth" in t.lower() or "top-line" in t.lower()
        or "topline" in t.lower() or "sales growth" in t.lower()
        for t in themes
    )
    if talks_revenue_growth and latest_yoy is not None:
        if latest_yoy < 0:
            divergences.append("revenue_growth_vs_declining_yoy")
        else:
            aligned_any = True

    if divergences:
        return "Divergent"
    if aligned_any:
        return "Aligned"
    # No checkable themes → we can't say, return None rather than fabricate.
    return None


def _key_themes_analysis(
    documents: list[dict], financial_data: dict,
) -> dict:
    """Extract top themes across all documents + detect emerging/fading
    themes across transcript periods.

    Emerging: themes with score > 0 in the most recent transcript and
              score == 0 in all prior transcripts.
    Fading:   themes with score > 0 in prior transcripts but 0 in the
              most recent one.
    """
    scorable = [d for d in documents if d.get("text")]
    if not scorable:
        return {
            "status": "failed",
            "themes": [],
            "theme_scores": None,
            "emerging_themes": [],
            "fading_themes": [],
            "financial_alignment": None,
        }

    # Aggregate rate across all documents: total hits / total tokens * 1000.
    total_tokens = 0
    theme_hits_total: dict[str, int] = {theme: 0 for theme in _THEME_KEYWORDS}
    for d in scorable:
        tokens = len(_tokenize(d["text"]))
        total_tokens += tokens
        hits = _theme_hits(d["text"])
        for theme, n in hits.items():
            theme_hits_total[theme] += n

    if total_tokens <= 0:
        return {
            "status": "failed",
            "themes": [],
            "theme_scores": None,
            "emerging_themes": [],
            "fading_themes": [],
            "financial_alignment": None,
        }

    rates = {
        theme: (hits / total_tokens) * 1000.0
        for theme, hits in theme_hits_total.items()
    }
    themes, theme_scores = _rank_themes(rates, top_n=5)

    # Emerging / fading themes — only computed on transcripts with >= 2 periods.
    emerging: list[str] = []
    fading: list[str] = []
    transcripts = sorted(
        [d for d in scorable if d.get("doc_type") == "earnings_transcript"],
        key=lambda d: d.get("date") or "",
    )
    if len(transcripts) >= 2:
        latest = transcripts[-1]
        prior = transcripts[:-1]
        latest_hits = _theme_hits(latest["text"])
        prior_union: dict[str, int] = {theme: 0 for theme in _THEME_KEYWORDS}
        for d in prior:
            for theme, n in _theme_hits(d["text"]).items():
                prior_union[theme] += n

        for theme in _THEME_KEYWORDS:
            if latest_hits[theme] > 0 and prior_union[theme] == 0:
                emerging.append(theme)
            elif latest_hits[theme] == 0 and prior_union[theme] > 0:
                fading.append(theme)

    alignment = _financial_alignment(themes, financial_data)

    return {
        "status": "success",
        "themes": themes,
        "theme_scores": theme_scores if theme_scores else None,
        "emerging_themes": emerging,
        "fading_themes": fading,
        "financial_alignment": alignment,
    }


# ── External fetchers ────────────────────────────────────────────────

def _http_get(url: str, timeout: float = _HTTP_TIMEOUT_S) -> str | None:
    """Perform a single HTTP GET and return text body, or None on failure.

    All errors are swallowed (network, HTTP, timeout) — callers handle None.
    """
    req = urllib.request.Request(url, headers={"User-Agent": _HTTP_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, OSError) as exc:
        logger.debug("HTTP GET failed for %s: %s", url, exc)
        return None


def _http_get_json(url: str, timeout: float = _HTTP_TIMEOUT_S):
    """Fetch a URL and parse the body as JSON. Returns None on any failure."""
    raw = _http_get(url, timeout=timeout)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _fetch_with_retry(url: str, retries: int = 1) -> str | None:
    """HTTP GET with `retries` additional attempts on timeout failure."""
    result = _http_get(url)
    attempts = 0
    while result is None and attempts < retries:
        attempts += 1
        result = _http_get(url)
    return result


def _fmp_enabled() -> bool:
    """Return True when a real-looking FMP API key is configured."""
    key = (FMP_API_KEY or "").strip()
    if not key:
        return False
    # Placeholder sentinels used in the public repo.
    return key.upper() not in {"YOUR_FMP_API_KEY_HERE", "REPLACE_ME", "TODO"}


def _fetch_fmp_transcripts(
    ticker: str, warnings: list[str], limit: int = 8,
) -> list[dict]:
    """Fetch up to `limit` earnings call transcripts from FMP.

    Returns a list of normalized document dicts. Each contains:
        doc_type, period, date, source_url, word_count, text, quarter, year.

    On any failure (missing key, network, malformed response) returns []
    and appends a warning describing the degraded mode.
    """
    if not _fmp_enabled():
        warnings.append("FMP_API_KEY not configured — skipping earnings transcripts")
        return []

    url = (
        f"{_FMP_BASE}/earning_call_transcript/"
        f"{urllib.parse.quote(ticker)}"
        f"?apikey={urllib.parse.quote(FMP_API_KEY)}&limit={int(limit)}"
    )
    # Retry once on timeout per spec.
    raw = _fetch_with_retry(url, retries=1)
    if raw is None:
        warnings.append("FMP transcript fetch failed — proceeding without transcripts")
        return []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        warnings.append("FMP transcript response was not JSON")
        return []

    if not isinstance(payload, list):
        return []

    out: list[dict] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        text = item.get("content") or ""
        if not isinstance(text, str) or not text.strip():
            continue
        quarter = item.get("quarter")
        year = item.get("year")
        date_str = item.get("date") or ""
        iso_date = _coerce_iso_date(date_str)
        period = f"Q{quarter} {year}" if quarter and year else (iso_date or "unknown")
        out.append({
            "doc_type": "earnings_transcript",
            "period": period,
            "date": iso_date,
            "source_url": None,  # FMP doesn't publish a canonical URL
            "word_count": len(text.split()),
            "text": text,
            "quarter": quarter,
            "year": year,
        })
    # Oldest first so trend comparisons are straightforward.
    out.sort(key=lambda d: d["date"] or "")
    return out


def _fetch_fmp_press_releases(
    ticker: str, warnings: list[str], limit: int = 4,
) -> list[dict]:
    """Fetch press releases from FMP. Silent on failure (supplementary source)."""
    if not _fmp_enabled():
        return []
    url = (
        f"{_FMP_BASE}/press-releases/"
        f"{urllib.parse.quote(ticker)}"
        f"?apikey={urllib.parse.quote(FMP_API_KEY)}&limit={int(limit)}"
    )
    payload = _http_get_json(url)
    if not isinstance(payload, list):
        return []

    out: list[dict] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("content") or ""
        if not isinstance(text, str) or not text.strip():
            continue
        iso_date = _coerce_iso_date(item.get("date") or "")
        out.append({
            "doc_type": "press_release",
            "period": iso_date or "unknown",
            "date": iso_date,
            "source_url": item.get("url"),
            "word_count": len(text.split()),
            "text": text,
        })
    out.sort(key=lambda d: d["date"] or "")
    return out


def _fetch_edgar_10k(
    ticker: str, warnings: list[str], limit: int = 2,
) -> list[dict]:
    """Search SEC EDGAR full-text search for recent 10-K filings.

    Returns up to `limit` annual_report documents. The engine records
    the filing metadata and URL but does not parse the 10-K body text
    here — full text extraction would require additional dependencies
    and is out of scope for Phase 2.
    """
    query = urllib.parse.quote(f'"{ticker}" "management discussion"')
    url = f"{_EDGAR_SEARCH}?q={query}&forms=10-K"
    payload = _http_get_json(url)
    if not isinstance(payload, dict):
        warnings.append("EDGAR search unavailable — no annual reports fetched")
        return []

    hits = (payload.get("hits") or {}).get("hits") or []
    out: list[dict] = []
    for hit in hits[:limit]:
        if not isinstance(hit, dict):
            continue
        src = hit.get("_source") or {}
        iso_date = _coerce_iso_date(src.get("file_date") or "")
        # EDGAR returns a _id like "0000320193-24-000123:aapl-20240928.htm".
        accession = (hit.get("_id") or "").split(":")[0]
        doc_url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar?"
            f"action=getcompany&CIK={urllib.parse.quote(ticker)}&type=10-K"
            if not accession else
            f"https://www.sec.gov/Archives/edgar/data/?accession={accession}"
        )
        period = f"FY{iso_date[:4]}" if iso_date else "unknown"
        # Use EDGAR snippet text as a weak proxy for MD&A body — real body
        # extraction is deferred to a later upgrade.
        snippet_text = " ".join(
            s for s in (hit.get("highlight") or {}).get("text", [])
            if isinstance(s, str)
        )
        out.append({
            "doc_type": "annual_report",
            "period": period,
            "date": iso_date,
            "source_url": doc_url,
            "word_count": len(snippet_text.split()),
            "text": snippet_text,
        })
    out.sort(key=lambda d: d["date"] or "")
    return out


def _coerce_iso_date(raw: str) -> str:
    """Normalize a date string into ISO 8601 (YYYY-MM-DD). Returns "" on failure."""
    if not raw or not isinstance(raw, str):
        return ""
    # Fast path — already ISO.
    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%Y/%m/%d", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


# ── Source coverage ──────────────────────────────────────────────────

def _data_quality_flag(transcript_count: int) -> str:
    if transcript_count >= 4:
        return "clean"
    if transcript_count >= 1:
        return "partial"
    return "minimal"


def _build_source_coverage(documents: list[dict]) -> dict:
    """Assemble the source_coverage section of the contract.

    Args:
        documents: All fetched documents (transcripts + annual reports +
                   press releases). Each must have doc_type, date, period,
                   word_count, source_url keys.

    Returns:
        A dict matching the source_coverage schema section.
    """
    if not documents:
        return {
            "status": "partial",
            "earnings_transcripts": 0,
            "annual_reports": 0,
            "total_documents": 0,
            "date_range_start": None,
            "date_range_end": None,
            "most_recent_quarter": None,
            "staleness_flag": True,
            "sources_list": [],
        }

    transcripts = [d for d in documents if d.get("doc_type") == "earnings_transcript"]
    annual = [d for d in documents if d.get("doc_type") == "annual_report"]

    dated = [d for d in documents if d.get("date")]
    dated.sort(key=lambda d: d["date"])
    start = dated[0]["date"] if dated else None
    end = dated[-1]["date"] if dated else None

    # Staleness is computed against the most recent document across all types.
    staleness_flag = True
    if end:
        try:
            most_recent = datetime.date.fromisoformat(end[:10])
            age_days = (datetime.date.today() - most_recent).days
            staleness_flag = age_days > STALENESS_DAYS
        except ValueError:
            staleness_flag = True

    most_recent_quarter = None
    if transcripts:
        most_recent_quarter = max(
            transcripts, key=lambda d: d.get("date") or ""
        ).get("period")

    sources_list = [
        {
            "doc_type": d.get("doc_type"),
            "period": d.get("period"),
            "date": d.get("date") or "",
            "source_url": d.get("source_url"),
            "word_count": int(d.get("word_count") or 0),
        }
        for d in documents
    ]

    return {
        "status": "success",
        "earnings_transcripts": len(transcripts),
        "annual_reports": len(annual),
        "total_documents": len(documents),
        "date_range_start": start,
        "date_range_end": end,
        "most_recent_quarter": most_recent_quarter,
        "staleness_flag": staleness_flag,
        "sources_list": sources_list,
    }


# ── Contract validator (used by tests) ───────────────────────────────

_REQUIRED_SHAPE: dict[str, list[str]] = {
    "sentiment": [
        "status", "overall_score", "management_optimism",
        "risk_word_frequency", "uncertainty_score",
        "forward_guidance_tone", "sentiment_trend",
        "qna_vs_prepared_delta",
    ],
    "red_flags": [
        "status", "flags", "flags_count", "severity",
        "categories_detected", "new_vs_prior",
    ],
    "key_themes": [
        "status", "themes", "theme_scores",
        "emerging_themes", "fading_themes", "financial_alignment",
    ],
    "source_coverage": [
        "status", "earnings_transcripts", "annual_reports",
        "total_documents", "date_range_start", "date_range_end",
        "most_recent_quarter", "staleness_flag", "sources_list",
    ],
    "meta": [
        "computed_at", "model_version", "nlp_approach",
        "warnings", "data_quality_flag", "assumptions",
    ],
}

_LIST_FIELDS: set[tuple[str, str]] = {
    ("red_flags", "flags"),
    ("red_flags", "categories_detected"),
    ("key_themes", "themes"),
    ("key_themes", "emerging_themes"),
    ("key_themes", "fading_themes"),
    ("source_coverage", "sources_list"),
    ("meta", "warnings"),
}


def validate_contract(output: dict) -> tuple[bool, list[str]]:
    """Verify that an nlp_insights dict matches the 34-field contract.

    Checks that all required sub-objects and fields are present and that
    fields typed as list are [] not None.

    Args:
        output: The nlp_insights dict to validate.

    Returns:
        (is_valid, errors) tuple. `errors` is empty when is_valid is True.
    """
    errors: list[str] = []

    for section, fields in _REQUIRED_SHAPE.items():
        if section not in output:
            errors.append(f"Missing section: {section}")
            continue
        sub = output[section]
        if not isinstance(sub, dict):
            errors.append(f"{section} is not a dict")
            continue
        for field in fields:
            if field not in sub:
                errors.append(f"Missing field: {section}.{field}")

    for section, field in _LIST_FIELDS:
        val = output.get(section, {}).get(field)
        if val is None:
            errors.append(f"{section}.{field} must be [] not None")

    return (len(errors) == 0, errors)


# ── Engine class ─────────────────────────────────────────────────────

class NLPIntelligenceEngine(BaseEngine):
    """Engine 4 — reads financial_data, writes nlp_insights.

    Phase 1: returns a schema-valid empty fallback so downstream engines
    can integrate. Real fetching and NLP scoring land in later phases.
    """

    name = "engine_4"
    requires = ["financial_data"]
    produces = "nlp_insights"

    def run(self, context: dict) -> dict:
        try:
            financial_data = context.get("financial_data") or {}
            meta = financial_data.get("meta") or {}
            ticker = meta.get("ticker") or financial_data.get("ticker")

            if not ticker:
                return valid_fallback_schema(
                    ["No ticker available in financial_data — NLP analysis skipped"]
                )

            # Warnings accumulated across sub-components.
            warnings: list[str] = list(
                (financial_data.get("quality") or {}).get("warnings") or []
            )

            # --- Fetch documents (Phase 2) ---
            try:
                transcripts = _fetch_fmp_transcripts(
                    ticker, warnings, limit=NLP_LOOKBACK_QUARTERS * 2,
                )
            except Exception as exc:
                logger.exception("Transcript fetch failed")
                warnings.append(f"Transcript fetch error: {exc}")
                transcripts = []

            try:
                annual_reports = _fetch_edgar_10k(ticker, warnings, limit=2)
            except Exception as exc:
                logger.exception("EDGAR fetch failed")
                warnings.append(f"EDGAR fetch error: {exc}")
                annual_reports = []

            # Press releases are silent-fail.
            try:
                press = _fetch_fmp_press_releases(ticker, warnings, limit=4)
            except Exception:
                press = []

            documents = [*transcripts, *annual_reports, *press]

            # --- Source coverage ---
            try:
                source_coverage = _build_source_coverage(documents)
            except Exception as exc:
                logger.exception("Source coverage build failed")
                warnings.append(f"Source coverage error: {exc}")
                source_coverage = valid_fallback_schema([])["source_coverage"]

            # --- Sentiment analysis (Phase 3) ---
            try:
                sentiment = _sentiment_scores(documents)
            except Exception as exc:
                logger.exception("Sentiment analysis failed")
                warnings.append(f"Sentiment error: {exc}")
                sentiment = valid_fallback_schema([])["sentiment"]

            # --- Red flag analysis (Phase 4) ---
            try:
                red_flags = _red_flag_analysis(documents)
            except Exception as exc:
                logger.exception("Red flag analysis failed")
                warnings.append(f"Red flag error: {exc}")
                red_flags = valid_fallback_schema([])["red_flags"]

            # --- Key themes + financial alignment (Phase 5) ---
            try:
                key_themes = _key_themes_analysis(documents, financial_data)
            except Exception as exc:
                logger.exception("Theme analysis failed")
                warnings.append(f"Theme error: {exc}")
                key_themes = valid_fallback_schema([])["key_themes"]

            return {
                "sentiment": sentiment,
                "red_flags": red_flags,
                "key_themes": key_themes,
                "source_coverage": source_coverage,
                "meta": {
                    "computed_at": _now_iso(),
                    "model_version": MODEL_VERSION,
                    "nlp_approach": "rule_based",
                    "warnings": warnings,
                    "data_quality_flag": _data_quality_flag(
                        source_coverage["earnings_transcripts"]
                    ),
                    "assumptions": {
                        "risk_word_threshold": 0.07,
                        "sentiment_model": "rule_based_v1",
                        "lookback_quarters": NLP_LOOKBACK_QUARTERS,
                    },
                },
            }

        except Exception as exc:
            logger.exception("Engine 4 top-level failure")
            return valid_fallback_schema([f"Engine 4 fatal error: {exc}"])


# Back-compat alias — orchestrator.py on main still instantiates NLPEngine.
# Will be removed once the registration site is updated.
NLPEngine = NLPIntelligenceEngine


# ── Smoke test ───────────────────────────────────────────────────────

if __name__ == "__main__":
    from backend.engines.mock_bus_data import MOCK_FINANCIAL_DATA

    ctx = {"ticker": "AAPL", "financial_data": MOCK_FINANCIAL_DATA}
    engine = NLPIntelligenceEngine()
    result = engine.run(ctx)

    ok, errs = validate_contract(result)
    print(f"Contract validation: {'PASS' if ok else 'FAIL'}")
    if errs:
        for e in errs:
            print(f"  - {e}")

    # Smoke test each failure path.
    empty_result = engine.run({"financial_data": {}})
    ok2, _ = validate_contract(empty_result)
    print(f"Empty financial_data: {'PASS' if ok2 else 'FAIL'}")

    no_ctx = engine.run({})
    ok3, _ = validate_contract(no_ctx)
    print(f"Empty context:        {'PASS' if ok3 else 'FAIL'}")
