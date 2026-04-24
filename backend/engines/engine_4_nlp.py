"""
Engine 4 — Backward-compatibility shim
=======================================
The implementation has moved into the ``backend.engines.engine_4`` package.
This file re-exports the full public surface so any existing import
(orchestrator, tests, E5) continues to work without changes.
"""

from backend.engines.engine_4 import (           # noqa: F401
    NLPIntelligenceEngine,
    NLPEngine,
    MODEL_VERSION,
    valid_fallback_schema,
    validate_contract,
)
from backend.engines.engine_4.fetchers import (  # noqa: F401
    fetch_fmp_transcripts    as _fetch_fmp_transcripts,
    fetch_fmp_press_releases as _fetch_fmp_press_releases,
    fetch_edgar_10k          as _fetch_edgar_10k,
)

__all__ = [
    "NLPIntelligenceEngine",
    "NLPEngine",
    "MODEL_VERSION",
    "valid_fallback_schema",
    "validate_contract",
    "_fetch_fmp_transcripts",
    "_fetch_fmp_press_releases",
    "_fetch_edgar_10k",
]


if __name__ == "__main__":
    from backend.engines.engine_1.mock_data import MOCK_FINANCIAL_DATA

    ctx = {"ticker": "AAPL", "financial_data": MOCK_FINANCIAL_DATA}
    engine = NLPIntelligenceEngine()
    result = engine.run(ctx)

    ok, errs = validate_contract(result)
    print(f"Contract validation: {'PASS' if ok else 'FAIL'}")
    if errs:
        for e in errs:
            print(f"  - {e}")

    ok2, _ = validate_contract(engine.run({"financial_data": {}}))
    print(f"Empty financial_data: {'PASS' if ok2 else 'FAIL'}")

    ok3, _ = validate_contract(engine.run({}))
    print(f"Empty context:        {'PASS' if ok3 else 'FAIL'}")
