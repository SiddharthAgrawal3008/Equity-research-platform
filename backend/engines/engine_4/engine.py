"""
Engine 4 — NLPIntelligenceEngine
==================================
Orchestrates document fetching, NLP analysis, and contract assembly.

Input:  context["financial_data"]  (produced by Engine 1)
Output: nlp_insights dict          (consumed by Engine 5)

Guarantees:
    - run() NEVER raises — all failures caught internally
    - list-typed fields are always [] (never None)
    - Sub-components fail independently
    - Does NOT import Engine 2 or Engine 3
"""

from __future__ import annotations

import logging

from backend.engines.shared_config import NLP_LOOKBACK_QUARTERS
from backend.pipeline.base_engine import BaseEngine

from backend.engines.engine_4.helpers import (
    MODEL_VERSION, valid_fallback_schema, _now_iso,
)
from backend.engines.engine_4.fetchers import (
    fetch_fmp_transcripts,
    fetch_fmp_press_releases,
    fetch_edgar_10k,
)
from backend.engines.engine_4.analysis import (
    sentiment_scores,
    red_flag_analysis,
    key_themes_analysis,
    build_source_coverage,
    data_quality_flag,
)

logger = logging.getLogger(__name__)


class NLPIntelligenceEngine(BaseEngine):
    """Engine 4 — reads financial_data, writes nlp_insights."""

    name     = "engine_4"
    requires = ["financial_data"]
    produces = "nlp_insights"

    def run(self, context: dict) -> dict:
        try:
            financial_data = context.get("financial_data") or {}
            meta   = financial_data.get("meta") or {}
            ticker = meta.get("ticker") or financial_data.get("ticker")

            if not ticker:
                return valid_fallback_schema(
                    ["No ticker available in financial_data — NLP analysis skipped"]
                )

            warnings: list[str] = list(
                (financial_data.get("quality") or {}).get("warnings") or []
            )

            # ── Fetch documents ───────────────────────────────────────
            # BOTTLENECK: all three fetches are sequential HTTP calls.
            # Worst-case wall time ≈ 3 × _HTTP_TIMEOUT_S (15 s) if APIs are slow.
            # To speed up, run these concurrently (e.g. ThreadPoolExecutor).
            try:
                transcripts = fetch_fmp_transcripts(
                    ticker, warnings, limit=NLP_LOOKBACK_QUARTERS * 2,
                )
            except Exception as exc:
                logger.exception("Transcript fetch failed")
                warnings.append(f"Transcript fetch error: {exc}")
                transcripts = []

            try:
                annual_reports = fetch_edgar_10k(ticker, warnings, limit=2)
            except Exception as exc:
                logger.exception("EDGAR fetch failed")
                warnings.append(f"EDGAR fetch error: {exc}")
                annual_reports = []

            try:
                press = fetch_fmp_press_releases(ticker, warnings, limit=4)
            except Exception:
                press = []

            documents = [*transcripts, *annual_reports, *press]

            # ── Source coverage ───────────────────────────────────────
            try:
                source_coverage = build_source_coverage(documents)
            except Exception as exc:
                logger.exception("Source coverage build failed")
                warnings.append(f"Source coverage error: {exc}")
                source_coverage = valid_fallback_schema([])["source_coverage"]

            # ── Sentiment ─────────────────────────────────────────────
            # CPU cost scales with total token count across all documents.
            # Large 10-K snippets or many transcripts will slow this step.
            try:
                sentiment = sentiment_scores(documents)
            except Exception as exc:
                logger.exception("Sentiment analysis failed")
                warnings.append(f"Sentiment error: {exc}")
                sentiment = valid_fallback_schema([])["sentiment"]

            # ── Red flags ─────────────────────────────────────────────
            # CPU cost is O(documents × categories × patterns × text_len).
            # Long annual-report texts are the most likely bottleneck here.
            try:
                red_flags = red_flag_analysis(documents)
            except Exception as exc:
                logger.exception("Red flag analysis failed")
                warnings.append(f"Red flag error: {exc}")
                red_flags = valid_fallback_schema([])["red_flags"]

            # ── Key themes + financial alignment ──────────────────────
            # CPU cost is O(documents × themes × keywords × text_len).
            # Regex tokenisation per document adds overhead for large texts.
            try:
                key_themes = key_themes_analysis(documents, financial_data)
            except Exception as exc:
                logger.exception("Theme analysis failed")
                warnings.append(f"Theme error: {exc}")
                key_themes = valid_fallback_schema([])["key_themes"]

            return {
                "sentiment":      sentiment,
                "red_flags":      red_flags,
                "key_themes":     key_themes,
                "source_coverage": source_coverage,
                "meta": {
                    "computed_at":      _now_iso(),
                    "model_version":    MODEL_VERSION,
                    "nlp_approach":     "rule_based",
                    "warnings":         warnings,
                    "data_quality_flag": data_quality_flag(
                        source_coverage["earnings_transcripts"]
                    ),
                    "assumptions": {
                        "risk_word_threshold": 0.07,
                        "sentiment_model":     "rule_based_v1",
                        "lookback_quarters":   NLP_LOOKBACK_QUARTERS,
                    },
                },
            }

        except Exception as exc:
            logger.exception("Engine 4 top-level failure")
            return valid_fallback_schema([f"Engine 4 fatal error: {exc}"])


# Back-compat alias
NLPEngine = NLPIntelligenceEngine
