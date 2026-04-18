"""
Engine 4 — NLP Analysis Functions
====================================
Sentiment scoring, red-flag detection, theme extraction,
financial alignment cross-check, and source coverage assembly.
"""

from __future__ import annotations

import datetime
import re

from backend.engines.shared_config import STALENESS_DAYS
from backend.engines.engine_4.words import (
    POSITIVE_WORDS, RISK_WORDS, HEDGING_WORDS,
    QNA_MARKERS, GUIDANCE_MARKERS,
)
from backend.engines.engine_4.patterns import (
    VALID_CATEGORIES, CATEGORY_MIN_HITS,
    RED_FLAG_PATTERNS, FLAG_TEMPLATES, THEME_KEYWORDS,
)

_TOKEN_RE = re.compile(r"[a-zA-Z]+")


# ── Text primitives ───────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]


def _count_in(tokens: list[str], vocab: set[str]) -> int:
    if not tokens:
        return 0
    return sum(1 for t in tokens if t in vocab)


def _split_prepared_qna(text: str) -> tuple[str, str]:
    """Split transcript into (prepared_remarks, qna) via heuristic markers."""
    if not text:
        return ("", "")
    lower = text.lower()
    split_at: int | None = None
    for marker in QNA_MARKERS:
        idx = lower.find(marker)
        if idx != -1 and (split_at is None or idx < split_at):
            split_at = idx
    if split_at is None:
        return (text, "")
    return (text[:split_at], text[split_at:])


def _score_block(text: str) -> dict:
    """Return raw word-count stats for a text block."""
    tokens = _tokenize(text)
    total = len(tokens)
    if total == 0:
        return {"tokens": 0, "positive": 0, "risk": 0, "hedge": 0,
                "guidance_neg": 0, "guidance_pos": 0}

    lower = text.lower()
    guidance_neg = guidance_pos = 0
    for marker in GUIDANCE_MARKERS:
        idx = lower.find(marker)
        while idx != -1:
            window = lower[max(0, idx - 60): idx + 60]
            wt = _tokenize(window)
            guidance_neg += _count_in(wt, RISK_WORDS)
            guidance_pos += _count_in(wt, POSITIVE_WORDS)
            idx = lower.find(marker, idx + 1)

    return {
        "tokens":       total,
        "positive":     _count_in(tokens, POSITIVE_WORDS),
        "risk":         _count_in(tokens, RISK_WORDS),
        "hedge":        _count_in(tokens, HEDGING_WORDS),
        "guidance_neg": guidance_neg,
        "guidance_pos": guidance_pos,
    }


def _sentiment_from_counts(pos: int, risk: int, tokens: int) -> float | None:
    """Map positive/risk word counts to a 0–1 sentiment score (0.5 = neutral)."""
    if tokens <= 0:
        return None
    raw = (pos - risk) / tokens
    return max(0.0, min(1.0, 0.5 + raw * 10))


# ── Sentiment analysis ────────────────────────────────────────────────

def _classify_guidance_tone(guidance_pos: int, guidance_neg: int) -> str | None:
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


def sentiment_scores(documents: list[dict]) -> dict:
    """Compute the full sentiment sub-object from available documents."""
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

    totals = {"tokens": 0, "positive": 0, "risk": 0, "hedge": 0,
              "guidance_neg": 0, "guidance_pos": 0}
    prepared_totals = {"tokens": 0, "positive": 0, "risk": 0}
    qna_totals      = {"tokens": 0, "positive": 0, "risk": 0}
    per_doc_scores: list[tuple[str, float]] = []

    for doc in texts:
        scores = _score_block(doc["text"])
        for k, v in scores.items():
            totals[k] += v

        if doc.get("doc_type") == "earnings_transcript":
            prepared, qna = _split_prepared_qna(doc["text"])
            p = _score_block(prepared)
            q = _score_block(qna)
            for k in ("tokens", "positive", "risk"):
                prepared_totals[k] += p[k]
                qna_totals[k]      += q[k]

        doc_score = _sentiment_from_counts(
            scores["positive"], scores["risk"], scores["tokens"],
        )
        if doc_score is not None:
            per_doc_scores.append((doc.get("date") or "", doc_score))

    overall    = _sentiment_from_counts(totals["positive"], totals["risk"], totals["tokens"])
    management = _sentiment_from_counts(prepared_totals["positive"], prepared_totals["risk"],
                                        prepared_totals["tokens"])
    qna_score  = _sentiment_from_counts(qna_totals["positive"], qna_totals["risk"],
                                        qna_totals["tokens"])

    risk_freq   = totals["risk"]  / totals["tokens"] if totals["tokens"] else None
    uncertainty = totals["hedge"] / totals["tokens"] if totals["tokens"] else None
    guidance    = _classify_guidance_tone(totals["guidance_pos"], totals["guidance_neg"])

    delta = None
    if management is not None and qna_score is not None:
        delta = round(management - qna_score, 4)

    per_doc_scores.sort(key=lambda t: t[0])
    trend = _compute_sentiment_trend(per_doc_scores)
    status = "success" if totals["tokens"] > 0 else "failed"

    return {
        "status":               status,
        "overall_score":        round(overall, 4) if overall is not None else None,
        "management_optimism":  round(management, 4) if management is not None else None,
        "risk_word_frequency":  round(risk_freq, 4) if risk_freq is not None else None,
        "uncertainty_score":    round(uncertainty, 4) if uncertainty is not None else None,
        "forward_guidance_tone": guidance,
        "sentiment_trend":      trend,
        "qna_vs_prepared_delta": delta,
    }


# ── Red flag detection ────────────────────────────────────────────────

def _detect_categories(text: str) -> dict[str, int]:
    if not text:
        return {cat: 0 for cat in VALID_CATEGORIES}
    lower = text.lower()
    out: dict[str, int] = {}
    for category, patterns in RED_FLAG_PATTERNS.items():
        count = 0
        for pat in patterns:
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


def red_flag_analysis(documents: list[dict]) -> dict:
    """Analyze all documents for red-flag category hits."""
    transcripts = [d for d in documents if d.get("doc_type") == "earnings_transcript"]
    scorable    = [d for d in documents if d.get("text")]

    if not scorable:
        return {
            "status": "failed",
            "flags": [], "flags_count": 0,
            "severity": None, "categories_detected": [],
            "new_vs_prior": None,
        }

    totals: dict[str, int] = {cat: 0 for cat in VALID_CATEGORIES}
    for d in scorable:
        for cat, hits in _detect_categories(d["text"]).items():
            totals[cat] += hits

    detected = [cat for cat, n in totals.items() if n >= CATEGORY_MIN_HITS]
    flags    = [FLAG_TEMPLATES[cat] for cat in detected if cat in FLAG_TEMPLATES][:10]

    new_vs_prior: dict | None = None
    if len(transcripts) >= 2:
        by_date = sorted(transcripts, key=lambda d: d.get("date") or "")
        latest  = by_date[-1]
        prior   = by_date[:-1]

        latest_cats = {
            cat for cat, hits in _detect_categories(latest["text"]).items()
            if hits >= CATEGORY_MIN_HITS
        }
        prior_cats: set[str] = set()
        for d in prior:
            for cat, hits in _detect_categories(d["text"]).items():
                if hits >= CATEGORY_MIN_HITS:
                    prior_cats.add(cat)

        new_vs_prior = {
            "new":        sorted(latest_cats - prior_cats),
            "resolved":   sorted(prior_cats - latest_cats),
            "persistent": sorted(latest_cats & prior_cats),
        }

    return {
        "status":             "success",
        "flags":              flags,
        "flags_count":        len(flags),
        "severity":           _severity_from_flag_count(len(flags)),
        "categories_detected": detected,
        "new_vs_prior":       new_vs_prior,
    }


# ── Theme extraction & financial alignment ────────────────────────────

def _theme_hits(text: str) -> dict[str, int]:
    if not text:
        return {theme: 0 for theme in THEME_KEYWORDS}
    lower = text.lower()
    out: dict[str, int] = {}
    for theme, keywords in THEME_KEYWORDS.items():
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
    ranked = sorted(
        [(t, r) for t, r in theme_rates.items() if r > 0],
        key=lambda x: x[1], reverse=True,
    )[:top_n]
    if not ranked:
        return [], {}
    top = ranked[0][1] or 1.0
    themes = [t for t, _ in ranked]
    scores = {t: round(r / top, 4) for t, r in ranked}
    return themes, scores


def _is_declining(series: list) -> bool:
    vals = [v for v in (series or []) if isinstance(v, (int, float))]
    if len(vals) < 3:
        return False
    mid   = len(vals) // 2
    older  = sum(vals[:mid]) / mid
    recent = sum(vals[mid:]) / (len(vals) - mid)
    return recent < older * 0.98


def _financial_alignment(themes: list[str], financial_data: dict) -> str | None:
    if not themes:
        return None

    derived = (
        financial_data.get("derived")
        or financial_data.get("derived_metrics")
        or {}
    )
    if not derived:
        return None

    gm_series   = derived.get("gross_margin")
    revenue_yoy = derived.get("revenue_yoy")

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

    if any("margin" in t.lower() for t in themes):
        if isinstance(gm_series, list) and gm_series:
            if _is_declining(gm_series):
                divergences.append("margin_expansion_vs_declining_gm")
            else:
                aligned_any = True

    if any(
        "revenue growth" in t.lower() or "top-line" in t.lower()
        or "topline" in t.lower() or "sales growth" in t.lower()
        for t in themes
    ):
        if latest_yoy is not None:
            if latest_yoy < 0:
                divergences.append("revenue_growth_vs_declining_yoy")
            else:
                aligned_any = True

    if divergences:
        return "Divergent"
    if aligned_any:
        return "Aligned"
    return None


def key_themes_analysis(documents: list[dict], financial_data: dict) -> dict:
    """Extract top themes + detect emerging/fading themes across periods."""
    scorable = [d for d in documents if d.get("text")]
    if not scorable:
        return {
            "status": "failed",
            "themes": [], "theme_scores": None,
            "emerging_themes": [], "fading_themes": [],
            "financial_alignment": None,
        }

    total_tokens = 0
    theme_hits_total: dict[str, int] = {theme: 0 for theme in THEME_KEYWORDS}
    for d in scorable:
        tokens = len(_tokenize(d["text"]))
        total_tokens += tokens
        for theme, n in _theme_hits(d["text"]).items():
            theme_hits_total[theme] += n

    if total_tokens <= 0:
        return {
            "status": "failed",
            "themes": [], "theme_scores": None,
            "emerging_themes": [], "fading_themes": [],
            "financial_alignment": None,
        }

    rates = {
        theme: (hits / total_tokens) * 1000.0
        for theme, hits in theme_hits_total.items()
    }
    themes, theme_scores = _rank_themes(rates, top_n=5)

    emerging: list[str] = []
    fading:   list[str] = []
    transcripts = sorted(
        [d for d in scorable if d.get("doc_type") == "earnings_transcript"],
        key=lambda d: d.get("date") or "",
    )
    if len(transcripts) >= 2:
        latest      = transcripts[-1]
        prior       = transcripts[:-1]
        latest_hits = _theme_hits(latest["text"])
        prior_union: dict[str, int] = {theme: 0 for theme in THEME_KEYWORDS}
        for d in prior:
            for theme, n in _theme_hits(d["text"]).items():
                prior_union[theme] += n

        for theme in THEME_KEYWORDS:
            if latest_hits[theme] > 0 and prior_union[theme] == 0:
                emerging.append(theme)
            elif latest_hits[theme] == 0 and prior_union[theme] > 0:
                fading.append(theme)

    alignment = _financial_alignment(themes, financial_data)

    return {
        "status":             "success",
        "themes":             themes,
        "theme_scores":       theme_scores if theme_scores else None,
        "emerging_themes":    emerging,
        "fading_themes":      fading,
        "financial_alignment": alignment,
    }


# ── Source coverage ───────────────────────────────────────────────────

def data_quality_flag(transcript_count: int) -> str:
    if transcript_count >= 4:
        return "clean"
    if transcript_count >= 1:
        return "partial"
    return "minimal"


def build_source_coverage(documents: list[dict]) -> dict:
    """Assemble the source_coverage section of the contract."""
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
    annual      = [d for d in documents if d.get("doc_type") == "annual_report"]

    dated = sorted([d for d in documents if d.get("date")], key=lambda d: d["date"])
    start = dated[0]["date"]  if dated else None
    end   = dated[-1]["date"] if dated else None

    staleness_flag = True
    if end:
        try:
            age_days = (datetime.date.today() - datetime.date.fromisoformat(end[:10])).days
            staleness_flag = age_days > STALENESS_DAYS
        except ValueError:
            staleness_flag = True

    most_recent_quarter = None
    if transcripts:
        most_recent_quarter = max(transcripts, key=lambda d: d.get("date") or "").get("period")

    sources_list = [
        {
            "doc_type":   d.get("doc_type"),
            "period":     d.get("period"),
            "date":       d.get("date") or "",
            "source_url": d.get("source_url"),
            "word_count": int(d.get("word_count") or 0),
        }
        for d in documents
    ]

    return {
        "status":               "success",
        "earnings_transcripts": len(transcripts),
        "annual_reports":       len(annual),
        "total_documents":      len(documents),
        "date_range_start":     start,
        "date_range_end":       end,
        "most_recent_quarter":  most_recent_quarter,
        "staleness_flag":       staleness_flag,
        "sources_list":         sources_list,
    }
