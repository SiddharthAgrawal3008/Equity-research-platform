"""
Engine 2 — Main Valuation Engine (Owner: Siddharth)
====================================================

Real implementation lives in backend/engines/engine_2/ package.
This file re-exports ValuationEngine for backwards compatibility
with the engine registry in __init__.py.
"""

from backend.engines.engine_2.valuation import ValuationEngine

__all__ = ["ValuationEngine"]
