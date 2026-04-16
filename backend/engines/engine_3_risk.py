"""
Engine 3 — Risk & Financial Health Engine (Owner: Siddharth)
============================================================

Input:  financial_data (from bus)
Output: risk_metrics (to bus)
"""

from backend.engines.engine_3.risk_engine import RiskEngine

__all__ = ["RiskEngine"]
