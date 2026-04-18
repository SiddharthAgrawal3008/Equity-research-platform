"""
Engine 4 — NLP Intelligence Engine (Owner: Annant)
===================================================

Sub-package for Engine 4. The implementation lives in the sibling file
``backend/engines/engine_4_nlp.py``; this package re-exports the public
surface so downstream code can import from either location.

Usage
-----
    from backend.engines.engine_4 import NLPIntelligenceEngine

    engine = NLPIntelligenceEngine()
    result = engine.run(context)          # returns nlp_insights dict

Contract
--------
    produces:  "nlp_insights"
    requires:  ["financial_data"]

    The output dict contains five top-level keys:
        sentiment       — scores, trend, guidance tone
        red_flags       — severity, flags list, category breakdown
        key_themes      — top-5 themes with financial-alignment cross-check
        source_coverage — document counts, date range, staleness flag
        meta            — version, approach, warnings, data quality flag

Guarantees
----------
    - run() NEVER raises — all failures are caught and returned as a
      valid fallback schema with null scalars and empty lists.
    - List-typed fields are always [] (never None).
    - Sub-components fail independently.
"""

from backend.engines.engine_4_nlp import (  # noqa: F401
    NLPIntelligenceEngine,
    NLPEngine,           # back-compat alias
    valid_fallback_schema,
    validate_contract,
    MODEL_VERSION,
)

__all__ = [
    "NLPIntelligenceEngine",
    "NLPEngine",
    "valid_fallback_schema",
    "validate_contract",
    "MODEL_VERSION",
]
