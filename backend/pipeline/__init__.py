"""
Pipeline package — Central Orchestrator + Data Bus.
====================================================

Usage:
    from backend.pipeline import run_pipeline
    from backend.engines import DEFAULT_ENGINES

    result = run_pipeline("AAPL", engines=DEFAULT_ENGINES)
"""

from backend.pipeline.base_engine import BaseEngine
from backend.pipeline.context import create_context
from backend.pipeline.orchestrator import run_pipeline, resolve_stages

__all__ = ["BaseEngine", "create_context", "run_pipeline", "resolve_stages"]
