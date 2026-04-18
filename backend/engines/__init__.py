"""
Engine Registry — All pipeline engines registered here.
========================================================

The orchestrator receives DEFAULT_ENGINES and automatically resolves
execution stages from each engine's `requires` and `produces` fields.

To add a new engine:
    1. Create a new file implementing BaseEngine
    2. Import it here and add an instance to DEFAULT_ENGINES
    3. The orchestrator handles the rest (stage placement is automatic)
"""

from backend.engines.engine_1_financial_data import FinancialDataEngine
from backend.engines.engine_2_valuation import ValuationEngine
from backend.engines.engine_3_risk import RiskEngine
from backend.engines.engine_4_nlp import NLPEngine
from backend.engines.engine_5_report import ReportEngine

DEFAULT_ENGINES = [
    FinancialDataEngine(),
    ValuationEngine(),
    RiskEngine(),
    NLPEngine(),
    ReportEngine(),
]
