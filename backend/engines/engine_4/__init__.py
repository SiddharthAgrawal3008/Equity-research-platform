"""
Engine 4 — NLP Intelligence Engine (Owner: Annant)
===================================================

Package layout
--------------
    words.py     — finance-domain word lists & transcript markers
    patterns.py  — red-flag patterns & theme keyword anchors
    helpers.py   — contract schema helpers & validator
    fetchers.py  — FMP API + SEC EDGAR document fetchers
    analysis.py  — sentiment, red-flag, theme & alignment functions
    engine.py    — NLPIntelligenceEngine (BaseEngine subclass)

Quick start
-----------
    from backend.engines.engine_4 import NLPIntelligenceEngine

    result = NLPIntelligenceEngine().run(context)

Contract (produces: "nlp_insights")
------------------------------------
    sentiment       — overall_score, management_optimism, risk_word_frequency,
                      uncertainty_score, forward_guidance_tone, sentiment_trend,
                      qna_vs_prepared_delta
    red_flags       — severity, flags list, categories_detected, new_vs_prior
    key_themes      — top-5 themes, theme_scores, emerging/fading, financial_alignment
    source_coverage — document counts, date range, staleness_flag
    meta            — model_version, nlp_approach, warnings, data_quality_flag

Guarantees
----------
    - run() NEVER raises
    - List-typed fields are always [] (never None)
    - Sub-components fail independently
"""

from backend.engines.engine_4.engine import (   # noqa: F401
    NLPIntelligenceEngine,
    NLPEngine,           # back-compat alias
)
from backend.engines.engine_4.helpers import (  # noqa: F401
    MODEL_VERSION,
    valid_fallback_schema,
    validate_contract,
)

__all__ = [
    "NLPIntelligenceEngine",
    "NLPEngine",
    "MODEL_VERSION",
    "valid_fallback_schema",
    "validate_contract",
]
